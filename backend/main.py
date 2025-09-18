from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import uuid
import datetime
import zipfile
import asyncio
import io

import ParsingScripts
from bootstrap import lifespan 
from workers import ParsingOrder, ParsingTask, order_queue
from workers import get_order, remove_order


from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List

class Source(BaseModel):
    key: str = Field(..., description="Ключ парсера, зарегистрированный в реестре")
    datetime: Optional[str] = Field(
        None,
        description="Дата/время в формате 'dd.mm.yyyy_HH-MM'. Не требуется для forced-запуска.",
        examples=["10.09.2025_12-30"],
    )

class ParseRequest(BaseModel):
    source: List[Source] = Field(..., min_items=1, description="Список источников для запуска")

class OrderIdRequest(BaseModel):
    order_id: uuid.UUID = Field(..., description="UUID заказа")

class ParseResponse(BaseModel):
    order_id: uuid.UUID

tags_metadata = [
    {"name": "Parsers", "description": "Работа со списком доступных парсеров"},
    {"name": "Orders", "description": "Создание и проверка задач парсинга"},
    {"name": "Results", "description": "Получение результатов парсинга"},
    {"name": "Health", "description": "Проверка статуса сервиса"},
]

app = FastAPI(
    title="Parsing Manager API",
    description="Единый REST API для запуска и мониторинга парсеров, агрегации результатов и экспорта.",
    contact={"name": "Maintainer", "url": "https://github.com/vanin2004", "email": "vanin2004i@mail.ru"},
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/availableparsers", tags=["Parsers"], summary="Список доступных парсеров")
async def available_parsers():
    available_parsers = []
    async with ParsingScripts.parsers_lock:
        for key, parser in ParsingScripts.parsers.items():
            available_parsers.append ({
                "name": parser.name,
                "key": key
            })
        return {"parsers": available_parsers}

@app.post("/parse",
    tags=["Orders"],
    summary="Создать заказ на парсинг",
    description="Запускает задачи по заданным источникам и возвращает идентификатор заказа.",
    response_model=ParseResponse,)
async def create_parse_order(body: ParseRequest):
    return await start_parsing(body)

@app.post(
    "/forceparse",
    tags=["Orders"],
    summary="Создать заказ на парсинг (forced)",
    description="Игнорирует поле datetime у источников и запускает немедленно.",
    response_model=ParseResponse,
)
async def create_forced_parse_order(body: ParseRequest):
    return await start_parsing(body, forced= True)


async def start_parsing(body: ParseRequest, forced = False):
    async with ParsingScripts.parsers_lock:
        parsing_tasks = []
        for source in body.source:
            if source["key"] not in ParsingScripts.parsers:
                raise HTTPException(status_code=400, detail=f"undefined source({source.key})")
            
            pt_id = uuid.uuid4()
            if forced:
                date_time = None
            else:
                if not source.datetime:
                    raise HTTPException(status_code=400, detail="missing datetime for non-forced run")
                try:
                    date_time = datetime.datetime.strptime(source.datetime, "%d.%m.%Y_%H-%M")
                except ValueError:
                    raise HTTPException(status_code=400, detail="bad datetime format, expected dd.mm.yyyy_HH-MM")
            pt = ParsingTask(source.key, date_time, pt_id)
            parsing_tasks.append(pt)
            
        po_id = uuid.uuid4()
        po = ParsingOrder(po_id,parsing_tasks,datetime.datetime.now())
        print(f"registred forced = {forced}, {po}")
        order_queue.put_nowait(po)
        return {"order_id": po_id}

@app.post(
    "/check",
    tags=["Orders"],
    summary="Проверить статус заказа",
    description="Возвращает состояние всех задач в заказе по его UUID.",
)
async def check_status(body: OrderIdRequest):
    order: ParsingOrder = await get_order(body.order_id)
    if order is None:
        raise HTTPException(status_code=400, detail=f"unknown order_id {body.order_id}")
    async with order.get_lock():
        status = await order.get_full_status()
    return {"status": {"order_id": str(body.order_id), "tasks": status}}

@app.post(
    "/result",
    tags=["Results"],
    summary="Получить результат заказа",
    description="Возвращает архив с результатами или другой формат, согласно реализации.",
)
async def get_result(body: OrderIdRequest):
    
    order_id = order.order_id

    if order_id is None:
        raise HTTPException(status_code=400, detail="Missing order_id")

    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order_id format")

    order : ParsingOrder = await get_order(order_uuid)
    async with order.get_lock():
        task_list = order.get_task_list()
        print(f"sending {order}")
    
    files_bin = {}
    for task in task_list:
        async with task.get_lock():
            files_bin[task.get_file_name()] = task.get_file()

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name in files_bin:
            zip_file.writestr(file_name, files_bin[file_name].read())
        
    zip_buffer.seek(0)

    asyncio.create_task(remove_order(order_id, delay=3600))

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=reports.zip"}
    )
