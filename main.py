from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Path, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import aiofiles
import logging
import csv
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración de MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["video_database"]
video_collection = db["videos"]

# Directorio para guardar videos
VIDEO_DIR = "static/videos"
os.makedirs(VIDEO_DIR, exist_ok=True)

# Configuración de logging
logging.basicConfig(level=logging.INFO)

# Modelos
class VideoUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]

class VideoResponse(BaseModel):
    success: bool
    videoUrl: Optional[str] = None
    videoTitle: Optional[str] = None
    videoDescription: Optional[str] = None
    videoId: str

@app.post("/upload_video", response_model=VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(...)
):
    try:
        video_path = os.path.join(VIDEO_DIR, file.filename)
        async with aiofiles.open(video_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        video_url = f"http://localhost:8000/static/videos/{file.filename}"
        video_data = {
            "title": title,
            "description": description,
            "video_url": video_url
        }
        result = await video_collection.insert_one(video_data)
        video_id = str(result.inserted_id)

        return {
            "success": True,
            "videoUrl": video_url,
            "videoTitle": title,
            "videoDescription": description,
            "videoId": video_id
        }
    except Exception as e:
        logging.error(f"Error al subir el video: {e}")
        raise HTTPException(status_code=500, detail="Error al subir el video")

@app.get("/videos", response_model=List[dict])
async def get_videos(skip: int = 0, limit: int = 3):
    try:
        videos = []
        async for video in video_collection.find().skip(skip).limit(limit).sort("_id", -1):
            video["_id"] = str(video["_id"])  # Convert ObjectId to str for serialization
            videos.append(video)
        return videos
    except Exception as e:
        logging.error(f"Error al obtener videos: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener videos")

@app.delete("/delete_video/{video_id}", response_model=VideoResponse)
async def delete_video(video_id: str):
    try:
        result = await video_collection.delete_one({"_id": ObjectId(video_id)})
        if result.deleted_count == 1:
            return {"success": True, "videoId": video_id}
        else:
            raise HTTPException(status_code=404, detail="Video not found")
    except Exception as e:
        logging.error(f"Error al eliminar el video: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar el video")

@app.get("/videos/{video_name}")
async def get_video(video_name: str):
    video_path = os.path.join(VIDEO_DIR, video_name)
    if os.path.isfile(video_path):
        return FileResponse(video_path)
    else:
        raise HTTPException(status_code=404, detail="Video no encontrado")

# Configuración para servir archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuración del middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las solicitudes de cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todos los encabezados HTTP
)

# Archivo CSV para almacenar noticias
NEWS_FILE = 'news.csv'

# Asegúrate de que el archivo CSV exista
if not os.path.exists(NEWS_FILE):
    with open(NEWS_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['title', 'description', 'date'])  # Encabezados del CSV

class News(BaseModel):
    title: str
    description: str
    date: str  # Asegúrate de que el formato de la fecha sea YYYY-MM-DD

def read_news():
    with open(NEWS_FILE, 'r') as file:
        reader = csv.DictReader(file)
        return list(reader)

def write_news(news_list):
    with open(NEWS_FILE, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'description', 'date'])
        writer.writeheader()
        writer.writerows(news_list)

@app.get("/news", response_model=List[News])
def get_news():
    return read_news()

@app.get("/news/{index}", response_model=News)
def get_news_by_index(index: int):
    news_list = read_news()
    if index < 0 or index >= len(news_list):
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    return news_list[index]

@app.post("/news", response_model=News)
def create_news(news: News):
    news_list = read_news()
    news_list.append(news.dict())
    write_news(news_list)
    return news

@app.put("/news/{index}", response_model=News)
def update_news(index: int, news: News):
    news_list = read_news()
    if index < 0 or index >= len(news_list):
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    news_list[index] = news.dict()
    write_news(news_list)
    return news

@app.delete("/news/{index}", response_model=News)
def delete_news(index: int):
    news_list = read_news()
    if index < 0 or index >= len(news_list):
        raise HTTPException(status_code=404, detail="Noticia no encontrada")
    removed_news = news_list.pop(index)
    write_news(news_list)
    return removed_news
