from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import tempfile
import os
import subprocess
import shutil

app = FastAPI()

from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
import os, tempfile, subprocess, io

@app.post("/convert")
async def convert_doc_to_docx(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory(dir="/tmp") as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())

        result = subprocess.run([
            "libreoffice", "--headless", "--convert-to", "docx",
            "--outdir", tmpdir, input_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode != 0:
            return {
                "error": "Conversion failed",
                "details": result.stderr.decode()
            }

        base_name = os.path.splitext(file.filename)[0]
        output_path = os.path.join(tmpdir, base_name + ".docx")

        if not os.path.exists(output_path):
            return {"error": "Converted file not found"}

        with open(output_path, "rb") as f:
            docx_bytes = f.read()

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.docx"'}
        )

@app.get("/health")
async def health_check():
    return {"status": "ok"}