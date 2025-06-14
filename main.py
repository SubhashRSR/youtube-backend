from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import uuid
import os
import shutil
import ffmpeg
import requests

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Clean up helper
def clean_folder():
    for f in os.listdir(DOWNLOAD_DIR):
        path = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(path):
            os.remove(path)

# Download video
@app.post("/download")
async def download_video(url: str = Form(...)):
    clean_folder()
    uid = str(uuid.uuid4())
    out = os.path.join(DOWNLOAD_DIR, f"{uid}.%(ext)s")
    ydl_opts = {"outtmpl": out, "format": "best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        ext = info['ext']
    return FileResponse(os.path.join(DOWNLOAD_DIR, f"{uid}.{ext}"), filename=f"video.{ext}")

# Download MP3
@app.post("/mp3")
async def download_mp3(url: str = Form(...)):
    clean_folder()
    uid = str(uuid.uuid4())
    out = os.path.join(DOWNLOAD_DIR, f"{uid}.%(ext)s")
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return FileResponse(os.path.join(DOWNLOAD_DIR, f"{uid}.mp3"), filename="audio.mp3")

# Download thumbnail
@app.post("/thumbnail")
async def download_thumbnail(url: str = Form(...)):
    clean_folder()
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        thumbnail_url = info.get("thumbnail")
    r = requests.get(thumbnail_url, stream=True)
    path = os.path.join(DOWNLOAD_DIR, "thumb.jpg")
    with open(path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return FileResponse(path, filename="thumbnail.jpg")

# Get tags
@app.post("/tags")
async def get_tags(url: str = Form(...)):
    with yt_dlp.YoutubeDL({}) as ydl:
        info = ydl.extract_info(url, download=False)
        tags = info.get("tags", [])
    return JSONResponse({"tags": tags})

# Download playlist as ZIP
@app.post("/playlist")
async def download_playlist(url: str = Form(...)):
    clean_folder()
    uid = str(uuid.uuid4())
    folder = os.path.join(DOWNLOAD_DIR, uid)
    os.makedirs(folder, exist_ok=True)
    ydl_opts = {"outtmpl": f"{folder}/%(title)s.%(ext)s", "format": "best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    shutil.make_archive(folder, 'zip', folder)
    return FileResponse(f"{folder}.zip", filename="playlist.zip")

# Cut video
@app.post("/clip")
async def cut_video(url: str = Form(...), start: str = Form(...), end: str = Form(...)):
    clean_folder()
    uid = str(uuid.uuid4())
    video_path = os.path.join(DOWNLOAD_DIR, f"{uid}.mp4")
    clip_path = os.path.join(DOWNLOAD_DIR, f"{uid}_clip.mp4")

    ydl_opts = {'outtmpl': video_path, 'format': 'best'}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    ffmpeg.input(video_path, ss=start, to=end).output(clip_path).run()
    return FileResponse(clip_path, filename="clip.mp4")

