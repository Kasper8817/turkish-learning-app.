# ==========================================
# ИНСТРУКЦИЯ ПО ЗАПУСКУ:
# 1. Убедитесь, что вы в папке проекта: cd путь/к/папке
# 2. Запустите: uvicorn app:app --reload
# ==========================================

import random
from datetime import date
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# --- КРИТИЧЕСКИ ВАЖНЫЙ БЛОК ДЛЯ СВЯЗИ С БРАУЗЕРОМ ---
# Без этих настроек браузер будет выдавать ошибку "Failed to fetch"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Разрешаем запросы с любого адреса
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ВАША БАЗА ДАННЫХ (Хранится в оперативной памяти) ---
dictionary_db = [
    {"id": 1, "ru": "Книга", "tr": "Kitap", "type": "слово"},
    {"id": 2, "ru": "Яблоко", "tr": "Elma", "type": "слово"},
    {"id": 3, "ru": "Как тебя зовут?", "tr": "Adın ne?", "type": "фраза"},
    {"id": 4, "ru": "Доброе утро", "tr": "Günaydın", "type": "фраза"},
    {"id": 5, "ru": "Стол", "tr": "Masa", "type": "слово"},
    {"id": 6, "ru": "Машина", "tr": "Araba", "type": "слово"},
    {"id": 7, "ru": "Друг", "tr": "Arkadaş", "type": "слово"},
    {"id": 8, "ru": "Приятного аппетита", "tr": "Afiyet olsun", "type": "фраза"},
    {"id": 9, "ru": "Где находится...?", "tr": "Nerede...?", "type": "фраза"},
    {"id": 10, "ru": "Пожалуйста (ответ)", "tr": "Rica ederim", "type": "фраза"},
]

# Кэш для хранения заданий текущего дня
daily_cache = {"date": None, "tasks": []}

# Модель для приема новых слов через форму на сайте
class NewItem(BaseModel):
    ru: str
    tr: str
    type: str

def generate_hint(word: str):
    """Автоматически создает подсказку для слова"""
    return f"Начинается на '{word[0]}', всего букв: {len(word)}"

def update_daily_tasks():
    """Случайным образом выбирает слова и фразы из базы"""
    words = [item for item in dictionary_db if item["type"] == "слово"]
    phrases = [item for item in dictionary_db if item["type"] == "фраза"]
    
    # Пытаемся взять 10 слов и 20 фраз, если их меньше — берем всё, что есть
    selected_words = random.sample(words, min(len(words), 10))
    selected_phrases = random.sample(phrases, min(len(phrases), 20))
    
    combined = selected_words + selected_phrases
    
    # Добавляем подсказки к выбранным элементам
    for item in combined:
        item["hint"] = generate_hint(item["tr"])
    
    return combined

# --- МАРШРУТЫ API ---

@app.get("/get-daily-tasks")
async def get_tasks():
    """Отдает список заданий. Обновляется раз в сутки."""
    today = date.today()
    # Если наступил новый день или список пуст — генерируем новый набор
    if daily_cache["date"] != today or not daily_cache["tasks"]:
        daily_cache["tasks"] = update_daily_tasks()
        daily_cache["date"] = today
        print(f"DEBUG: Список обновлен на дату {today}")
        
    return daily_cache["tasks"]

@app.post("/add-to-db")
async def add_item(item: NewItem):
    """Принимает новое слово из браузера и сохраняет в список"""
    new_entry = {
        "id": len(dictionary_db) + 1, 
        "ru": item.ru, 
        "tr": item.tr, 
        "type": item.type
    }
    dictionary_db.append(new_entry)
    
    # Сбрасываем кэш, чтобы новое слово могло сразу попасть в выборку
    daily_cache["date"] = None 
    print(f"DEBUG: Добавлено новое слово: {item.ru}")
    
    return {"status": "success", "added": item.ru}