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

app = FastAPI(lifespan=lifespan)


@app.get("/availableparsers")
async def available_parsers():
    available_parsers = []
    async with ParsingScripts.parsers_lock:
        for key, parser in ParsingScripts.parsers.items():
            available_parsers.append ({
                "name": parser.name,
                "key": key
            })
        print(f"available parsers {[parser['key'] for parser in available_parsers]}")
        return JSONResponse(content={"parsers": available_parsers})

@app.post("/parse")
async def forceparse(request: Request):
    return await start_parsing(request)

@app.post("/forceparse")
async def forceparse(request: Request):
    return await start_parsing(request, forced= True)


async def start_parsing(request: Request, forced = False):
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="badrequest")

    async with ParsingScripts.parsers_lock:
        parsing_tasks = []
        for source in data.get("source"):
            if source["key"] not in ParsingScripts.parsers:
                raise HTTPException(status_code=400, detail=f"undefined source({source})")
            
            pt_id = uuid.uuid4()
            if forced:
                date_time = None
            else:
                date_time = datetime.datetime.strptime(source["datetime"], '%d.%m.%Y_%H-%M')
            pt = ParsingTask(source["key"],date_time,pt_id)
            parsing_tasks.append(pt)
        po_id = uuid.uuid4()
        po = ParsingOrder(po_id,parsing_tasks,datetime.datetime.now())
        print(f"registred forced = {forced}, {po}")
        order_queue.put_nowait(po)
        return {"order_id": po_id}

@app.post("/check")
async def check_status(request: Request):
    data = await request.json()
    order_id = data.get("order_id")

    if order_id is None:
        raise HTTPException(status_code=400, detail="Missing order_id")
    
    try:
        order_uuid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order_id format")

    order: ParsingOrder = await get_order(order_uuid)

    if order is None:
        raise HTTPException(status_code=400, detail=f"unknown order_id {order_uuid}")

    async with order.get_lock():
        status = await order.get_full_status()
        print(f"check status {order}: {status}")

    return {"status": {
        "order_id": order_id,
        "tasks": status
    }}

@app.post("/result")
async def get_result(request: Request):
    data = await request.json()
    order_id = data.get("order_id")

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
