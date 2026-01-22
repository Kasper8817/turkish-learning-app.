import random
import sqlite3
from datetime import date
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Настройка логирования для отслеживания работы сервера и отладки
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Настройка CORS: позволяет вашему index.html (даже если он запущен локально или на GitHub Pages)
# безопасно отправлять запросы к этому серверу на Render.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- КОНФИГУРАЦИЯ БАЗЫ ДАННЫХ SQLite ---

DB_PATH = "words.db"

def init_db():
    """
    Инициализирует базу данных: создает файл words.db и таблицу dictionary.
    Если база пуста, заполняет её начальным набором слов и фраз.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Создаем таблицу, если она еще не создана
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dictionary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ru TEXT NOT NULL,
                tr TEXT NOT NULL,
                type TEXT NOT NULL
            )
        """)
        
        # Проверяем, есть ли уже данные в базе
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        if cursor.fetchone()[0] == 0:
            logger.info("База данных пуста. Заполнение начальными данными...")
            initial_data = [
                ("Книга", "Kitap", "слово"),
                ("Яблоко", "Elma", "слово"),
                ("Как тебя зовут?", "Adın ne?", "фраза"),
                ("Доброе утро", "Günaydın", "фраза"),
                ("Стол", "Masa", "слово"),
                ("Машина", "Araba", "слово"),
                ("Друг", "Arkadaş", "слово"),
                ("Приятного аппетита", "Afiyet olsun", "фраза"),
                ("Где находится...?", "Nerede...?", "фраза"),
                ("Пожалуйста (ответ)", "Rica ederim", "фраза")
            ]
            cursor.executemany("INSERT INTO dictionary (ru, tr, type) VALUES (?, ?, ?)", initial_data)
        conn.commit()

# Запуск инициализации при старте приложения
init_db()

# --- МОДЕЛИ ДАННЫХ (Pydantic) ---

class NewItem(BaseModel):
    """Схема данных для добавления нового слова через POST-запрос"""
    ru: str
    tr: str
    type: str

# Кэш для "Заданий дня". Хранит дату и список выбранных слов,
# чтобы в течение дня набор слов не менялся при каждом обновлении страницы.
daily_cache = {"date": None, "tasks": []}

def get_all_from_db():
    """Извлекает все записи из файла базы данных и возвращает их в виде списка словарей"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row  # Позволяет обращаться к полям по именам (как в словаре)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dictionary")
        return [dict(row) for row in cursor.fetchall()]

def generate_hint(word: str):
    """Создает текстовую подсказку: первая буква и общее количество символов"""
    if not word: return ""
    return f"Начинается на '{word[0].upper()}', всего букв: {len(word)}"

# --- МАРШРУТЫ API (Эндпоинты) ---

@app.get("/get-daily-tasks")
async def get_tasks():
    """
    Выбирает случайные слова и фразы из базы. 
    Использует кэширование, чтобы состав заданий обновлялся раз в сутки.
    """
    today = date.today()
    
    # Если кэш пуст или наступил новый день — обновляем выборку
    if daily_cache["date"] != today or not daily_cache["tasks"]:
        all_items = get_all_from_db()
        
        words = [i for i in all_items if i["type"] == "слово"]
        phrases = [i for i in all_items if i["type"] == "фраза"]
        
        # Выбираем до 10 случайных слов и до 20 случайных фраз
        selected = random.sample(words, min(len(words), 10)) + \
                   random.sample(phrases, min(len(phrases), 20))
        
        # Для каждого выбранного элемента генерируем подсказку "на лету"
        for item in selected:
            item["hint"] = generate_hint(item["tr"])
            
        daily_cache["tasks"] = selected
        daily_cache["date"] = today
        logger.info(f"Сформирован новый список заданий на {today}")
        
    return daily_cache["tasks"]

@app.post("/add-to-db")
async def add_item(item: NewItem):
    """
    Принимает новое слово от фронтенда и сохраняет его в SQLite.
    Сбрасывает дневной кэш, чтобы новое слово могло попасть в выборку.
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO dictionary (ru, tr, type) VALUES (?, ?, ?)",
                (item.ru, item.tr, item.type)
            )
            conn.commit()
        
        # Очищаем дату в кэше, чтобы при следующем запросе /get-daily-tasks данные обновились
        daily_cache["date"] = None 
        logger.info(f"В базу добавлено новое выражение: {item.ru} ({item.type})")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Ошибка при записи в БД: {e}")
        return {"status": "error", "message": "Не удалось сохранить данные"}
