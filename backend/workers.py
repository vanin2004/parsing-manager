import pandas as pd
import asyncio
import datetime
from io import BytesIO
import time

import ParsingScripts
from ParsingScripts import ParserType
from status import TaskStatus, OrderStatus

import os
import uuid

class SafeFileOpener:
    def __init__(self, file_path: str, file_mode: str = "rb", timeout: float = 30.0, delay: float = 0.5):
        self.file_path = file_path
        self.file_mode = file_mode
        self.timeout = timeout
        self.delay = delay
        self.file_descriptor = None

    async def __aenter__(self):
        start = asyncio.get_event_loop().time()

        while True:
            try:
                if os.path.exists(self.file_path):
                    self.file_descriptor = open(self.file_path, self.file_mode)
                    return self.file_descriptor
            except (OSError, PermissionError):
                pass

            if asyncio.get_event_loop().time() - start > self.timeout:
                raise TimeoutError(f"File opening timed out for: {self.file_path}")

            await asyncio.sleep(self.delay)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.file_descriptor is not None and not self.file_descriptor.closed:
            self.file_descriptor.close()

class ParsingTask:
    def __init__(self,parser_key: ParsingScripts.ParserKey, date_time: datetime.datetime, id: uuid.UUID):
        self.parser_key = parser_key
        self.date_time = date_time
        self.id = id
        self.file = None
        self.file_name = ""
        self.status = TaskStatus.PENDING
        self.error = None
        self.lock = asyncio.Lock()

    def __str__(self):
        if self.error:
            return f"ParsingTask(id={self.get_id()}, status={self.get_status()}, key={self.get_parser_key()}, error={self.get_error()})"
        return f"ParsingTask(id={self.get_id()}, status={self.get_status()}, key={self.get_parser_key()})"

    def get_status(self) -> str: 
        return self.status

    def get_id(self) -> uuid.UUID: 
        return self.id

    def get_file(self) -> bytes: 
        return self.file

    def get_file_name(self) -> str: 
        return self.file_name

    def get_error(self) -> str: 
        return self.error

    def get_date_time(self) -> datetime: 
        return self.date_time

    def get_lock(self) -> asyncio.Lock:
        return self.lock

    async def get_parser(self) -> ParsingScripts.Parser:
        async with ParsingScripts.parsers_lock:
            return ParsingScripts.parsers[self.parser_key]
    
    def get_parser_key(self):
        return self.parser_key

    def set_file(self, file: bytes): 
        self.file = file

    def set_file_name(self, file_name: str): 
        self.file_name = file_name

    def set_error(self, error: str): 
        self.error = error

    def set_status(self, status: str): 
        self.status = status

    def set_date_time(self, date_time: datetime.datetime):
        self.date_time = date_time

class ParsingOrder:
    def __init__(self, id: uuid.UUID,task_list: list[ParsingTask], date_time):
        self.id = id
        self.task_list = task_list
        self.date_time = date_time
        self.status = OrderStatus.PENDING
        self.lock = asyncio.Lock()
        self.error = ""

    def __str__(self):
        if self.error:
            return f"ParsingOrder(id={self.id}, status={self.status}, error={self.error})"
        return f"ParsingOrder(id={self.id}, status={self.status})"

    def get_status(self) -> str:
        return self.status
    
    async def get_full_status(self) -> dict[str:str]:
        status = {}
        for task in self.task_list:
            async with task.get_lock():
                task_status = task.get_status()
                parser_key = task.get_parser_key()
            status[parser_key] = task_status
        return status

    def get_id(self) -> uuid.UUID:
        return self.id

    def get_error(self) -> str:
        return self.error

    def get_date_time(self) -> datetime.datetime:
        return self.date_time

    def get_task_list(self) -> list[ParsingTask]:
        return self.task_list

    def get_lock(self) -> asyncio.Lock:
        return self.lock

    def set_error(self, error: str) -> None:
        self.error = error

    def set_status(self, status: str) -> None:
        self.status = status

order_queue: asyncio.Queue[ParsingOrder] = asyncio.Queue()
httpx_queue: asyncio.Queue[ParsingTask] = asyncio.Queue()
selenium_queue: asyncio.Queue[ParsingTask] = asyncio.Queue()

orders_lock = asyncio.Lock()
orders: dict[str, ParsingOrder] = {}

async def add_order(key: str, result: dict) -> None:
    async with orders_lock:
        orders[key] = result
        print(f"Orders: {orders}")

async def get_order(key: str) -> ParsingOrder:
    async with orders_lock:
        return orders.get(key)

async def remove_order(key: str, delay: int) -> None:
    await asyncio.sleep(delay)
    async with orders_lock:
        orders.pop(key, None)

async def worker(queue:asyncio.Queue):
    while True:
        task : ParsingTask = await queue.get()
        try:
            async with task.get_lock():
                task_id : uuid.UUID = task.get_id()
                deadline_time : datetime.datetime = task.get_date_time()
                parser: ParsingScripts.Parser = await task.get_parser()
                print(f"in work {task}")
            async with parser.get_lock():
                latest_parse = parser.get_latest_parse_datetime()


            # if (latest_parse is not None and
            #     latest_parse > deadline_time
            #     ):
            if (latest_parse is not None and deadline_time is not None):
                async with parser.get_lock():
                    full_latest_path = parser.get_output_path() + parser.get_latest_parse_file_name()
                    file_name = parser.get_latest_parse_file_name()

                with open(full_latest_path, "rb") as f:
                    xlsxfile_bin = BytesIO(f.read())
                xlsxfile_bin.seek(0)
                async with task.get_lock():
                    task.set_file(xlsxfile_bin)
                    task.set_file_name(file_name)
                    task.set_date_time(parser.get_latest_parse_datetime())
                    task.set_status(TaskStatus.COMPLETED)
                    print(f"found old data in {full_latest_path}  {task}")
            else:
                print(f"worker start new parse {task_id}")
                async with task.get_lock():
                    task.set_file(None)
                    task.set_file_name("")
                    task.set_date_time(datetime.datetime.now())
                    task.set_status(TaskStatus.IN_PROGRESS)
                    print(f"parsing started in {task}")
                
                start_time = time.time()
                async with parser.get_lock():
                    df = await parser.run()
                
                end_time = time.time()
             

                file_name = f"{parser.get_key()}_{datetime.datetime.now().strftime('%d.%m.%Y_%H-%M')}.xlsx"
                xlsxfile_bin = BytesIO() 
                df.to_excel(xlsxfile_bin, index=False)
                xlsxfile_bin.seek(0)
                with open(parser.get_output_path() + file_name, "wb") as f:
                    f.write(xlsxfile_bin.read())
                xlsxfile_bin.seek(0)
                async with task.get_lock():
                    task.set_file(xlsxfile_bin)
                    task.set_file_name(file_name)
                    task.set_date_time(datetime.datetime.now())
                    task.set_status(TaskStatus.COMPLETED)
                    print(f"worker finished parse {task}, time taken: {end_time - start_time} sec.")

                async with parser.get_lock():
                    parser.set_latest_parse_date_time(datetime.datetime.now())
                    parser.set_latest_parse_file_name(file_name)
                    print(f"new latest parse {file_name} for {parser.get_key()}")

        except Exception as e:
            async with task.get_lock():
                task.set_status(TaskStatus.FAILED)
                task.set_error(str(e))
                print(f"worker failed parse {task}")
        finally:
            queue.task_done()

async def distributor_worker():
    while True:
        order: ParsingOrder = await order_queue.get()
        try:
            async with order.get_lock():
                order_id: uuid.UUID = order.get_id()
                print(f"distributing {order}")

            await add_order(order_id, order)


            async with order.get_lock():
                for task in order.get_task_list():
                    async with task.get_lock():
                        parser:ParsingScripts.Parser = await task.get_parser()
                        task.set_status(TaskStatus.PENDING)
                        task_id = task.get_id()
                    async with parser.get_lock():
                        parser_type = parser.get_type()
                        print(f"distributing {order_id}, {task_id}, {parser_type}")

                    match parser_type:
                        case ParserType.HTTPX:
                            httpx_queue.put_nowait(task)
                        case ParserType.SELENIUM:
                            selenium_queue.put_nowait(task)
                        case _:
                            async with task.get_lock():
                                task.set_status(TaskStatus.FAILED)
                                print(f"Unknown parser type: {parser_type} in {task}")
                order.set_status(OrderStatus.PENDING)
                
        except Exception as e:
            async with order.get_lock():
                order.set_status(OrderStatus.FAILED)
                order.set_error(str(e))
                print(f"Failed to distribute {order}: {e}")
        finally:
            order_queue.task_done()
