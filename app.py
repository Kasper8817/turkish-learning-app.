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

# Секретный ключ для административных действий
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
    """Инициализация БД и автоматическое наполнение 100 стартовыми записями"""
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
        
        cursor.execute("SELECT COUNT(*) FROM dictionary")
        if cursor.fetchone()[0] == 0:
            logger.info("База пуста. Наполняю списком из 100 фраз...")
            
            start_data = [
                # --- СЛОВА (50 штук) ---
                ("Книга", "Kitap", "слово"), ("Ручка", "Kalem", "слово"), ("Школа", "Okul", "слово"),
                ("Яблоко", "Elma", "слово"), ("Машина", "Araba", "слово"), ("Стол", "Masa", "слово"),
                ("Вода", "Su", "слово"), ("Хлеб", "Ekmek", "слово"), ("Друг", "Arkadaş", "слово"),
                ("Дом", "Ev", "слово"), ("Солнце", "Güneş", "слово"), ("Море", "Deniz", "слово"),
                ("Цветок", "Çiçek", "слово"), ("Кошка", "Kedi", "слово"), ("Собака", "Köpek", "слово"),
                ("Чай", "Çay", "слово"), ("Кофе", "Kahve", "слово"), ("Сахар", "Şeker", "слово"),
                ("Соль", "Tuz", "слово"), ("Молоко", "Süt", "слово"), ("Дверь", "Kapı", "слово"),
                ("Окно", "Pencere", "слово"), ("Кровать", "Yatak", "слово"), ("Город", "Şehir", "слово"),
                ("Улица", "Sokak", "слово"), ("Деньги", "Para", "слово"), ("Время", "Zaman", "слово"),
                ("Работа", "İş", "слово"), ("Учитель", "Öğretmen", "слово"), ("Студент", "Öğrenci", "слово"),
                ("Семья", "Aile", "слово"), ("Ребенок", "Çocuk", "слово"), ("Отец", "Baba", "слово"),
                ("Мать", "Anne", "слово"), ("Брат/Сестра", "Kardeş", "слово"), ("Ночь", "Gece", "слово"),
                ("Утро", "Sabah", "слово"), ("Вечер", "Akşam", "слово"), ("Сегодня", "Bugün", "слово"),
                ("Завтра", "Yarın", "слово"), ("Вчера", "Dün", "слово"), ("Неделя", "Hafta", "слово"),
                ("Месяц", "Ay", "слово"), ("Год", "Yıl", "слово"), ("Новый", "Yeni", "слово"),
                ("Старый", "Eski", "слово"), ("Большой", "Büyük", "слово"), ("Маленький", "Küçük", "слово"),
                ("Красивый", "Güzel", "слово"), ("Плохой", "Kötü", "слово"),

                # --- ФРАЗЫ (50 штук) ---
                ("Доброе утро", "Günaydın", "фраза"), ("Как дела?", "Nasılsın?", "фраза"),
                ("Меня зовут...", "Benim adım...", "фраза"), ("Приятно познакомиться", "Memnun oldum", "фраза"),
                ("Сколько это стоит?", "Bu ne kadar?", "фраза"), ("Где находится...?", "Nerede...?", "фраза"),
                ("Я тебя люблю", "Seni seviyorum", "фраза"), ("Хорошего дня", "İyi günler", "фраза"),
                ("Пожалуйста", "Lütfen", "фраза"), ("Большое спасибо", "Çok teşekkür ederim", "фраза"),
                ("Да", "Evet", "фраза"), ("Нет", "Hayır", "фраза"), ("Хорошо", "Tamam", "фраза"),
                ("Я не знаю", "Bilmiyorum", "фраза"), ("Понимаю", "Anlıyorum", "фраза"),
                ("Извините", "Affedersiniz", "фраза"), ("Простите", "Özür dilerim", "фраза"),
                ("Удачи", "İyi şanslar", "фраза"), ("Добро пожаловать", "Hoş geldiniz", "фраза"),
                ("Приятного аппетита", "Afiyet olsun", "фраза"), ("С днем рождения", "İyi ki doğdun", "фраза"),
                ("Помогите мне", "Bana yardım edin", "фраза"), ("Я хочу пить", "Su içmek istiyorum", "фраза"),
                ("Я голоден", "Acıktım", "фраза"), ("Где туалет?", "Tuvalet nerede?", "фраза"),
                ("Который час?", "Saat kaç?", "фраза"), ("Счастливого пути", "İyi yolculuklar", "фраза"),
                ("Береги себя", "Kendine iyi bak", "фраза"), ("Увидимся", "Görüşürüz", "фраза"),
                ("До свидания", "Hoşça kalın", "фраза"), ("Все в порядке", "Her şey yolunda", "фраза"),
                ("Это очень дорого", "Bu çok pahalı", "фраза"), ("Я согласен", "Katılıyorum", "фраза"),
                ("Что это?", "Bu ne?", "фраза"), ("Кто это?", "Bu kim?", "фраза"),
                ("Иди сюда", "Buraya gel", "фраза"), ("Подожди немного", "Biraz bekle", "фраза"),
                ("Забудь об этом", "Boşver", "фраза"), ("Конечно", "Tabii ki", "фраза"),
                ("Возможно", "Belki", "фраза"), ("Я устал", "Yoruldum", "фраза"),
                ("Мне скучно", "Sıkıldım", "фраза"), ("Ничего страшного", "Önemli değil", "фраза"),
                ("Ты говоришь по-русски?", "Rusça biliyor musun?", "фраза"), ("Немного", "Biraz", "фраза"),
                ("Как это называется?", "Bunun adı ne?", "фраза"), ("С праздником", "Bayramınız kutlu olsun", "фраза"),
                ("Здоровья вашим рукам", "Ellerinize sağlık", "фраза"), ("Выздоравливай", "Geçmiş olsun", "фраза"),
                ("Спокойной ночи", "İyi geceler", "фраза")
            ]
            
            cursor.executemany("INSERT INTO dictionary (ru, tr, type) VALUES (?, ?, ?)", start_data)
            conn.commit()
            logger.info("Успешно загружено 100 записей.")

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
        
        num_words = min(len(words), 10)
        num_phrases = min(len(phrases), 20)
        
        # Случайная выборка из того, что есть в базе
        selected_words = random.sample(words, num_words) if words else []
        selected_phrases = random.sample(phrases, num_phrases) if phrases else []
        
        selected = selected_words + selected_phrases
        
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
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Неверный токен")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dictionary WHERE id = ?", (item.id,))
            conn.commit()
        daily_cache["date"] = None
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка удаления")
