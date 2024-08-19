import os
import csv
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

# Define the News model
class News(BaseModel):
    title: str
    description: str
    date: str

# CSV file path
NEWS_FILE = 'news.csv'

# Ensure the CSV file exists
if not os.path.exists(NEWS_FILE):
    with open(NEWS_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['title', 'description', 'date'])  # CSV headers

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




from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path



# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("static/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    file_location = UPLOAD_DIR / file.filename
    with file_location.open("wb") as buffer:
        buffer.write(await file.read())
    return {"filename": file.filename}

@app.get("/images/{filename}")
async def get_image(filename: str):
    file_location = UPLOAD_DIR / filename
    if file_location.exists():
        return FileResponse(file_location)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/images/")
async def list_images():
    images = [f.name for f in UPLOAD_DIR.iterdir() if f.is_file()]
    return images

@app.delete("/images/{filename}")
async def delete_image(filename: str):
    file_location = UPLOAD_DIR / filename
    if file_location.exists():
        file_location.unlink()  # Elimina el archivo
        return {"message": "File deleted successfully"}
    raise HTTPException(status_code=404, detail="File not found")
