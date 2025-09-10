import os
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio


import ParsingScripts
import workers


def get_latest_file_info(folder_path):
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
             if os.path.isfile(os.path.join(folder_path, f))]

    if not files:
        return "", None

    latest_file = max(files, key=os.path.getmtime)
    mtime = os.path.getmtime(latest_file)
    dt = datetime.datetime.fromtimestamp(mtime)

    return os.path.basename(latest_file), dt


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with workers.orders_lock:
        for parser in ParsingScripts.parsers.values():
            latest_parse_file_name, dt = get_latest_file_info(parser.output_path)
            parser.set_latest_parse_file_name(latest_parse_file_name)
            parser.set_latest_parse_date_time(dt)
            print(f"{parser.get_key()}, {dt}, {latest_parse_file_name}")

    for _ in range(3):
        asyncio.create_task(workers.worker(workers.httpx_queue))
    asyncio.create_task(workers.worker(workers.selenium_queue))
    asyncio.create_task(workers.distributor_worker())
    print("workers started")
    yield
