import random
import sqlite3
from datetime import date
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Секретный ключ для административных действий (замените 'my-secret-key' на свой пароль)
ADMIN_TOKEN = "my-secret-key"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "words.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dictionary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ru TEXT NOT NULL,
                tr TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

class NewItem(BaseModel):
    ru: str
    tr: str
    type: str

class DeleteItem(BaseModel):
    id: int

daily_cache = {"date": None, "tasks": []}

def get_all_from_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dictionary")
        return [dict(row) for row in cursor.fetchall()]

@app.get("/get-daily-tasks")
async def get_tasks():
    today = date.today()
    if daily_cache["date"] != today or not daily_cache["tasks"]:
        all_items = get_all_from_db()
        words = [i for i in all_items if i["type"] == "слово"]
        phrases = [i for i in all_items if i["type"] == "фраза"]
        selected = random.sample(words, min(len(words), 10)) + \
                   random.sample(phrases, min(len(phrases), 20))
        for item in selected:
            item["hint"] = f"Начинается на '{item['tr'][0].upper()}', букв: {len(item['tr'])}"
        daily_cache["tasks"] = selected
        daily_cache["date"] = today
    return daily_cache["tasks"]

@app.post("/add-to-db")
async def add_item(item: NewItem):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dictionary (ru, tr, type) VALUES (?, ?, ?)", (item.ru, item.tr, item.type))
            conn.commit()
        daily_cache["date"] = None 
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/delete-item")
async def delete_item(item: DeleteItem, x_admin_token: Optional[str] = Header(None)):
    """
    Удаление записи с проверкой токена администратора в заголовках.
    """
    # Проверка: совпадает ли присланный токен с нашим секретом
    if x_admin_token != ADMIN_TOKEN:
        logger.warning("Попытка несанкционированного удаления!")
        raise HTTPException(status_code=403, detail="Доступ запрещен: Неверный токен администратора")

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dictionary WHERE id = ?", (item.id,))
            conn.commit()
        daily_cache["date"] = None
        logger.info(f"Запись ID {item.id} успешно удалена администратором.")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка сервера при удалении")
