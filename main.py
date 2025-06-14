# main.py
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import yt_dlp
import os
from pydantic import BaseModel
import uuid
import shutil

app = FastAPI()

class VideoRequest(BaseModel):
    url: str
    format: str = "best"
    start: str = None
    end: str = None

@app.post("/download")
def download_video(data: VideoRequest):
    uid = str(uuid.uuid4())
    output_path = f"{uid}.%(ext)s"
    ydl_opts = {
        "format": data.format,
        "outtmpl": output_path,
        "noplaylist": True,
    }

    if data.start and data.end:
        ydl_opts["postprocessor_args"] = [
            "-ss", data.start,
            "-to", data.end
        ]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.download([data.url])

    file_path = [f for f in os.listdir() if f.startswith(uid)][0]
    response = FileResponse(file_path, filename=file_path)
    return response

@app.get("/thumbnail")
def download_thumbnail(url: str):
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        thumbnail_url = info.get("thumbnail", "")
    return {"thumbnail": thumbnail_url}

@app.get("/tags")
def get_tags(url: str):
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        return {"tags": info.get("tags", [])}

@app.get("/playlist")
def download_playlist(url: str):
    ydl_opts = {"ignoreerrors": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=False)
        return {"entries": [entry["webpage_url"] for entry in result["entries"] if entry]}
