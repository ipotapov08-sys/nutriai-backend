from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import hashlib
import datetime
import random
import math

app = FastAPI(title="NutriAI API - Тамагочи Нутрициолог")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "nutriai.db"

# ========== Модели ==========
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Metrics(BaseModel):
    gender: str
    age: int
    weight_kg: float
    height_cm: float
    activity_level: str
    goal: str

class FoodEntry(BaseModel):
    food_id: int
    grams: float
    meal_type: str  # breakfast, lunch, dinner, snack

class PetName(BaseModel):
    name: str

# ========== Константы игры ==========
ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9
}

GOAL_ADJUSTMENTS = {
    "weight_loss": -400,
    "maintenance": 0,
    "muscle_gain": 300
}

ACHIEVEMENTS_DB = {
    "first_day": {"name": "🌱 Первый шаг", "desc": "Заполнить дневник в первый раз", "xp": 10},
    "streak_3": {"name": "🔥 Разгон", "desc": "Стрик 3 дня", "xp": 30},
    "streak_7": {"name": "🌟 Неделя ЗОЖ", "desc": "Стрик 7 дней", "xp": 70},
    "streak_30": {"name": "👑 Месяц здоровья", "desc": "Стрик 30 дней", "xp": 300},
    "perfect_day": {"name": "🎯 Идеальный день", "desc": "100% нормы калорий", "xp": 50},
    "variety_5": {"name": "🍽️ Гурман", "desc": "5 разных продуктов за день", "xp": 20},
    "water_lover": {"name": "💧 Водохлёб", "desc": "Выпить 8 стаканов воды", "xp": 15},
    "protein_master": {"name": "💪 Белковый мастер", "desc": "Выполнить норму белка", "xp": 25},
}

DAILY_QUESTS = [
    {"id": 1, "text": "Выпей стакан воды", "xp": 5, "icon": "💧"},
    {"id": 2, "text": "Съешь овощ или фрукт", "xp": 10, "icon": "🥬"},
    {"id": 3, "text": "Заполни завтрак", "xp": 15, "icon": "🍳"},
    {"id": 4, "text": "Не превысь норму калорий", "xp": 20, "icon": "⚖️"},
    {"id": 5, "text": "Съешь 3 разных продукта", "xp": 10, "icon": "🍱"},
]

NUTRI_PHRASES = {
    "happy": [
        "🥑 Ты молодец! Я так рад твоему прогрессу!",
        "🌟 Отлично! Продолжай в том же духе!",
        "💚 Сегодня ты меня порадовал(а)!",
        "🎉 Вау! Твой стрик растёт!"
    ],
    "hungry": [
        "🍽️ Эй! Покорми меня! Уже пора есть",
        "🤤 Я голоден... Давай перекусим?",
        "⏰ Не пропускай приём пищи!",
        "😋 Я знаю отличный рецепт на обед!"
    ],
    "angry": [
        "😡 Ты слишком мало ешь! Это вредно!",
        "😤 Перебор с калориями! Давай полегче",
        "🤨 Я недоволен твоим питанием сегодня",
        "😠 Ну сколько можно? Возьми себя в руки!"
    ],
    "sick": [
        "🤒 Мне плохо... Пожалуйста, питайся правильно",
        "🤢 Я заболел от такой еды...",
        "😷 Нужна диета! Срочно!",
        "🥴 Ой-ой... Кажется, я отравился"
    ]
}

# ========== База данных ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS metrics (
            user_id INTEGER PRIMARY KEY,
            gender TEXT,
            age INTEGER,
            weight_kg REAL,
            height_cm REAL,
            activity_level TEXT DEFAULT 'moderate',
            goal TEXT DEFAULT 'maintenance',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS foods (
            id INTEGER PRIMARY KEY,
            name_ru TEXT NOT NULL,
            category TEXT,
            calories REAL,
            protein REAL,
            fat REAL,
            carbs REAL
        );
        
        CREATE TABLE IF NOT EXISTS food_diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            food_id INTEGER,
            grams REAL,
            meal_type TEXT,
            consumed_at DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS nutri_pet (
            user_id INTEGER PRIMARY KEY,
            name TEXT DEFAULT 'Нутри',
            state TEXT DEFAULT 'neutral',
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            last_active DATE,
            created_at DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_id TEXT,
            unlocked_at DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS daily_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            quest_id INTEGER,
            completed INTEGER DEFAULT 0,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS water_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            glasses INTEGER DEFAULT 0,
            date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    
    # Заполняем продукты (таблица Скурихина)
    foods = [
        ('Говядина отварная', 'Мясо', 254, 25.8, 16.8, 0.0),
        ('Куриная грудка', 'Птица', 113, 23.6, 1.9, 0.4),
        ('Треска', 'Рыба', 69, 16.0, 0.6, 0.0),
        ('Лосось', 'Рыба', 208, 20.0, 13.0, 0.0),
        ('Рис отварной', 'Крупы', 116, 2.2, 0.4, 24.9),
        ('Гречка отварная', 'Крупы', 101, 3.0, 3.4, 14.6),
        ('Овсянка на воде', 'Крупы', 88, 3.0, 1.7, 15.0),
        ('Макароны отварные', 'Крупы', 112, 3.4, 0.4, 23.2),
        ('Картофель отварной', 'Овощи', 82, 2.0, 0.4, 16.7),
        ('Помидор', 'Овощи', 18, 0.9, 0.2, 3.9),
        ('Огурец', 'Овощи', 15, 0.7, 0.1, 3.0),
        ('Капуста белокочанная', 'Овощи', 25, 1.3, 0.1, 5.8),
        ('Яблоко', 'Фрукты', 47, 0.4, 0.4, 9.8),
        ('Банан', 'Фрукты', 89, 1.5, 0.1, 21.0),
        ('Апельсин', 'Фрукты', 43, 0.9, 0.2, 10.3),
        ('Молоко 2.5%', 'Молочные', 52, 2.9, 2.5, 4.8),
        ('Творог 5%', 'Молочные', 121, 17.2, 5.0, 1.8),
        ('Сыр российский', 'Молочные', 360, 23.0, 29.0, 0.0),
        ('Яйцо куриное', 'Яйца', 157, 12.7, 11.5, 0.7),
        ('Хлеб пшеничный', 'Хлеб', 235, 7.6, 0.8, 49.0),
        ('Хлеб ржаной', 'Хлеб', 210, 6.6, 1.2, 41.0),
        ('Масло сливочное', 'Жиры', 748, 0.5, 82.5, 0.8),
        ('Масло подсолнечное', 'Жиры', 899, 0.0, 99.9, 0.0),
        ('Сахар', 'Сладости', 399, 0.0, 0.0, 99.8),
        ('Мёд', 'Сладости', 304, 0.3, 0.0, 82.4),
    ]
    
    cursor.execute("SELECT COUNT(*) FROM foods")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            'INSERT INTO foods (name_ru, category, calories, protein, fat, carbs) VALUES (?,?,?,?,?,?)',
            foods
        )
    
    conn.commit()
    conn.close()

def hash_password(p: str) -> str:
    return hashlib.sha256(p.encode()).hexdigest()

# ========== Вспомогательные функции ==========
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_daily_calories(metrics: dict) -> float:
    """Формула Харриса-Бенедикта"""
    if not metrics:
        return 2000.0
    
    gender = metrics.get("gender", "male")
    weight = metrics.get("weight_kg", 70)
    height = metrics.get("height_cm", 170)
    age = metrics.get("age", 30)
    activity = metrics.get("activity_level", "moderate")
    goal = metrics.get("goal", "maintenance")
    
    # BMR
    if gender == "male":
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
    
    # Умножаем на уровень активности и цель
    daily = bmr * ACTIVITY_MULTIPLIERS.get(activity, 1.55)
    daily += GOAL_ADJUSTMENTS.get(goal, 0)
    
    return round(daily, 1)

def get_today_entries(user_id: int, date: str = None):
    if not date:
        date = datetime.date.today().isoformat()
    
    conn = get_db()
    entries = conn.execute("""
        SELECT d.*, f.name_ru, f.calories, f.protein, f.fat, f.carbs, f.category
        FROM food_diary d 
        JOIN foods f ON d.food_id = f.id 
        WHERE d.user_id = ? AND d.consumed_at = ?
    """, (user_id, date)).fetchall()
    conn.close()
    return entries

def get_streak(user_id: int) -> int:
    """Считает стрик последовательных дней с записями в дневнике"""
    conn = get_db()
    dates = conn.execute("""
        SELECT DISTINCT consumed_at 
        FROM food_diary 
        WHERE user_id = ? 
        ORDER BY consumed_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    
    if not dates:
        return 0
    
    streak = 1
    today = datetime.date.today()
    
    for i in range(len(dates)):
        date = datetime.date.fromisoformat(dates[i]["consumed_at"])
        expected = today - datetime.timedelta(days=i)
        
        if date == expected:
            if i > 0:
                streak = i + 1
        else:
            break
    
    return streak

def check_achievements(user_id: int) -> List[dict]:
    """Проверяет и разблокирует достижения"""
    conn = get_db()
    new_achievements = []
    
    # Стрики
    streak = get_streak(user_id)
    streak_checks = [
        (1, "first_day"),
        (3, "streak_3"),
        (7, "streak_7"),
        (30, "streak_30"),
    ]
    for days, ach_id in streak_checks:
        if streak >= days:
            existing = conn.execute(
                "SELECT id FROM achievements WHERE user_id=? AND achievement_id=?",
                (user_id, ach_id)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO achievements (user_id, achievement_id) VALUES (?,?)",
                    (user_id, ach_id)
                )
                conn.execute(
                    "UPDATE nutri_pet SET xp = xp + ? WHERE user_id=?",
                    (ACHIEVEMENTS_DB[ach_id]["xp"], user_id)
                )
                new_achievements.append(ACHIEVEMENTS_DB[ach_id])
    
    # Разнообразие продуктов
    today_entries = get_today_entries(user_id)
    unique_foods = len(set(e["food_id"] for e in today_entries))
    if unique_foods >= 5:
        ach_id = "variety_5"
        existing = conn.execute(
            "SELECT id FROM achievements WHERE user_id=? AND achievement_id=?",
            (user_id, ach_id)
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO achievements (user_id, achievement_id) VALUES (?,?)",
                (user_id, ach_id)
            )
            new_achievements.append(ACHIEVEMENTS_DB[ach_id])
    
    conn.commit()
    conn.close()
    return new_achievements

def calculate_nutri_state(user_id: int) -> dict:
    """Главный алгоритм состояния Тамагочи"""
    conn = get_db()
    
    # Получаем питомца
    pet = conn.execute("SELECT * FROM nutri_pet WHERE user_id=?", (user_id,)).fetchone()
    if not pet:
        conn.execute(
            "INSERT INTO nutri_pet (user_id, name, state) VALUES (?, 'Нутри', 'neutral')",
            (user_id,)
        )
        conn.commit()
        pet = conn.execute("SELECT * FROM nutri_pet WHERE user_id=?", (user_id,)).fetchone()
    
    # Получаем метрики
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    
    # Считаем калории за сегодня
    today_entries = get_today_entries(user_id)
    eaten_calories = sum(e["calories"] * e["grams"] / 100 for e in today_entries)
    eaten_protein = sum(e["protein"] * e["grams"] / 100 for e in today_entries)
    eaten_fat = sum(e["fat"] * e["grams"] / 100 for e in today_entries)
    eaten_carbs = sum(e["carbs"] * e["grams"] / 100 for e in today_entries)
    
    # Считаем норму
    daily_norm = calculate_daily_calories(dict(metrics) if metrics else {})
    
    percent = eaten_calories / daily_norm * 100 if daily_norm > 0 else 0
    meals_count = len(set(e["meal_type"] for e in today_entries))
    
    # Обновляем стрик
    streak = get_streak(user_id)
    best_streak = max(streak, pet["best_streak"])
    
    conn.execute("""
        UPDATE nutri_pet 
        SET streak=?, best_streak=?, last_active=DATE('now')
        WHERE user_id=?
    """, (streak, best_streak, user_id))
    
    # Определяем состояние
    if percent >= 90 and percent <= 100 and meals_count >= 3:
        state = "happy"
        mood = random.choice(NUTRI_PHRASES["happy"])
        xp_bonus = 20
    elif percent >= 75 and percent <= 100:
        state = "happy"
        mood = random.choice(NUTRI_PHRASES["happy"])
        xp_bonus = 10
    elif meals_count < 2:
        state = "hungry"
        mood = random.choice(NUTRI_PHRASES["hungry"])
        xp_bonus = 0
    elif percent < 50:
        state = "angry"
        mood = random.choice(NUTRI_PHRASES["angry"])
        xp_bonus = -5
    elif percent > 120:
        state = "sick"
        mood = random.choice(NUTRI_PHRASES["sick"])
        xp_bonus = -10
    else:
        state = "neutral"
        mood = "🤔 Могло быть и лучше..."
        xp_bonus = 0
    
    # Начисляем XP
    new_xp = pet["xp"] + xp_bonus + (5 if len(today_entries) > 0 else 0)
    level = int(new_xp / 100) + 1
    
    conn.execute("""
        UPDATE nutri_pet 
        SET state=?, xp=?, level=?
        WHERE user_id=?
    """, (state, max(0, new_xp), level, user_id))
    
    conn.commit()
    conn.close()
    
    # Проверяем достижения
    new_achievements = check_achievements(user_id)
    
    return {
        "name": pet["name"],
        "state": state,
        "mood": mood,
        "level": level,
        "xp": max(0, new_xp),
        "xp_to_next": (level * 100) - max(0, new_xp),
        "streak": streak,
        "best_streak": best_streak,
        "percent": round(percent, 1),
        "eaten_calories": round(eaten_calories, 1),
        "eaten_protein": round(eaten_protein, 1),
        "eaten_fat": round(eaten_fat, 1),
        "eaten_carbs": round(eaten_carbs, 1),
        "daily_norm": daily_norm,
        "meals_today": meals_count,
        "new_achievements": new_achievements,
        "daily_quests": get_daily_quests(user_id)
    }

def get_daily_quests(user_id: int) -> List[dict]:
    """Получает квесты на сегодня"""
    conn = get_db()
    today = datetime.date.today().isoformat()
    
    quests = []
    for q in DAILY_QUESTS:
        completed = conn.execute(
            "SELECT completed FROM daily_quests WHERE user_id=? AND quest_id=? AND date=?",
            (user_id, q["id"], today)
        ).fetchone()
        
        quests.append({
            **q,
            "completed": bool(completed and completed["completed"])
        })
    
    conn.close()
    return quests

# ========== API Эндпоинты ==========

@app.post("/register")
async def register(user: UserRegister):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (?,?,?)",
            (user.email, hash_password(user.password), user.full_name)
        )
        conn.commit()
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Создаём питомца
        conn.execute("INSERT INTO nutri_pet (user_id) VALUES (?)", (user_id,))
        conn.commit()
        
        return {"status": "ok", "user_id": user_id, "message": "Аккаунт создан!"}
    except sqlite3.IntegrityError:
        raise HTTPException(400, "Email уже зарегистрирован")
    finally:
        conn.close()

@app.post("/login")
async def login(user: UserLogin):
    conn = get_db()
    row = conn.execute(
        "SELECT id, full_name FROM users WHERE email=? AND password_hash=?",
        (user.email, hash_password(user.password))
    ).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(401, "Неверный email или пароль")
    
    return {
        "status": "ok",
        "user_id": row["id"],
        "full_name": row["full_name"],
        "token": str(row["id"])
    }

@app.post("/metrics/save")
async def save_metrics(metrics: Metrics, user_id: int = Query(...)):
    conn = get_db()
    conn.execute('''
        INSERT OR REPLACE INTO metrics (user_id, gender, age, weight_kg, height_cm, activity_level, goal, updated_at)
        VALUES (?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
    ''', (user_id, metrics.gender, metrics.age, metrics.weight_kg, metrics.height_cm, metrics.activity_level, metrics.goal))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/foods/search")
async def search_foods(q: str = ""):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM foods WHERE name_ru LIKE ? LIMIT 20",
        (f"%{q}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/diary/add")
async def add_food_entry(entry: FoodEntry, user_id: int = Query(...)):
    conn = get_db()
    conn.execute(
        "INSERT INTO food_diary (user_id, food_id, grams, meal_type) VALUES (?,?,?,?)",
        (user_id, entry.food_id, entry.grams, entry.meal_type)
    )
    conn.commit()
    conn.close()
    
    # Обновляем состояние питомца
    state = calculate_nutri_state(user_id)
    return {"status": "ok", "nutri": state}

@app.get("/diary/today")
async def get_today_diary(user_id: int = Query(...)):
    entries = get_today_entries(user_id)
    summary = {
        "calories": sum(e["calories"] * e["grams"] / 100 for e in entries),
        "protein": sum(e["protein"] * e["grams"] / 100 for e in entries),
        "fat": sum(e["fat"] * e["grams"] / 100 for e in entries),
        "carbs": sum(e["carbs"] * e["grams"] / 100 for e in entries),
        "meals": {}
    }
    
    for e in entries:
        meal = e["meal_type"]
        if meal not in summary["meals"]:
            summary["meals"][meal] = []
        summary["meals"][meal].append({
            "food_name": e["name_ru"],
            "grams": e["grams"],
            "calories": round(e["calories"] * e["grams"] / 100, 1)
        })
    
    return {"entries": [dict(e) for e in entries], "summary": summary}

@app.get("/nutri/state")
async def get_nutri_state(user_id: int = Query(...)):
    return calculate_nutri_state(user_id)

@app.post("/nutri/name")
async def set_pet_name(data: PetName, user_id: int = Query(...)):
    conn = get_db()
    conn.execute("UPDATE nutri_pet SET name=? WHERE user_id=?", (data.name, user_id))
    conn.commit()
    conn.close()
    return {"status": "ok", "name": data.name}

@app.post("/quest/complete")
async def complete_quest(quest_id: int = Query(...), user_id: int = Query(...)):
    conn = get_db()
    today = datetime.date.today().isoformat()
    
    conn.execute(
        "INSERT OR REPLACE INTO daily_quests (user_id, quest_id, completed, date) VALUES (?,?,1,?)",
        (user_id, quest_id, today)
    )
    
    xp = next((q["xp"] for q in DAILY_QUESTS if q["id"] == quest_id), 0)
    conn.execute("UPDATE nutri_pet SET xp = xp + ? WHERE user_id=?", (xp, user_id))
    conn.commit()
    conn.close()
    
    return {"status": "ok", "xp_earned": xp}

@app.post("/water/add")
async def add_water(user_id: int = Query(...)):
    conn = get_db()
    today = datetime.date.today().isoformat()
    
    existing = conn.execute(
        "SELECT glasses FROM water_tracking WHERE user_id=? AND date=?",
        (user_id, today)
    ).fetchone()
    
    if existing:
        conn.execute(
            "UPDATE water_tracking SET glasses = glasses + 1 WHERE user_id=? AND date=?",
            (user_id, today)
        )
    else:
        conn.execute(
            "INSERT INTO water_tracking (user_id, glasses, date) VALUES (?,1,?)",
            (user_id, today)
        )
    
    conn.commit()
    glasses = conn.execute(
        "SELECT glasses FROM water_tracking WHERE user_id=? AND date=?",
        (user_id, today)
    ).fetchone()["glasses"]
    conn.close()
    
    return {"glasses": glasses, "goal": 8}

@app.get("/nutri/achievements")
async def get_achievements(user_id: int = Query(...)):
    conn = get_db()
    rows = conn.execute(
        "SELECT achievement_id, unlocked_at FROM achievements WHERE user_id=?",
        (user_id,)
    ).fetchall()
    conn.close()
    
    return [
        {
            "id": r["achievement_id"],
            "name": ACHIEVEMENTS_DB.get(r["achievement_id"], {}).get("name", r["achievement_id"]),
            "desc": ACHIEVEMENTS_DB.get(r["achievement_id"], {}).get("desc", ""),
            "unlocked_at": r["unlocked_at"]
        }
        for r in rows
    ]

@app.get("/")
async def root():
    return {
        "app": "NutriAI",
        "version": "2.0.0",
        "description": "Тамагочи-нутрициолог",
        "endpoints": [
            "/register", "/login", "/metrics/save",
            "/foods/search", "/diary/add", "/diary/today",
            "/nutri/state", "/nutri/achievements",
            "/quest/complete", "/water/add",
            "/diet-types", "/meals", "/diet-tables",
            "/plan/generate", "/plan/weekly", "/diary/delete",
            "/plan/adaptive", "/discipline",
            "/progress/daily-report", "/progress/weekly-report"
        ]
    }


@app.get("/diet-types")
async def get_diet_types():
    return [
        {"id": "omnivore", "name": "Всеядный", "icon": "🍖", "description": "Сбалансированное питание, включающее все группы продуктов", "features": ["Мясо и рыба", "Молочные продукты", "Овощи и фрукты", "Крупы и злаки"], "exclude": []},
        {"id": "vegetarian", "name": "Вегетарианский", "icon": "🥬", "description": "Исключает мясо, но допускает молочные продукты и яйца", "features": ["Молочные продукты", "Яйца", "Овощи и фрукты", "Бобовые"], "exclude": ["Мясо", "Птица", "Рыба", "Морепродукты"]},
        {"id": "vegan", "name": "Веганский", "icon": "🌱", "description": "Полностью растительное питание", "features": ["Овощи и фрукты", "Бобовые", "Орехи и семена", "Соевые"], "exclude": ["Мясо", "Птица", "Рыба", "Морепродукты", "Молочные", "Яйца"]},
        {"id": "keto", "name": "Кето / LCHF", "icon": "🥑", "description": "Высокожировое низкоуглеводное питание", "features": ["Жирное мясо и рыба", "Яйца", "Масла", "Орехи"], "exclude": ["Сахар", "Крупы", "Хлеб", "Бобовые"]},
        {"id": "mediterranean", "name": "Средиземноморский", "icon": "🫒", "description": "Традиционная кухня Средиземноморья", "features": ["Оливковое масло", "Рыба", "Овощи", "Цельнозерновые"], "exclude": ["Переработанное мясо"]},
        {"id": "low_carb", "name": "Низкоуглеводный", "icon": "🍗", "description": "Ограничение углеводов", "features": ["Мясо и рыба", "Овощи", "Яйца", "Молочные"], "exclude": ["Сахар", "Хлеб", "Макароны", "Рис", "Картофель"]}
    ]



@app.get("/meals")
async def get_meals(meal_type: str = "", diet_type: str = "omnivore"):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM meals WHERE 1=1"
    params = []
    if meal_type:
        query += " AND meal_type = ?"
        params.append(meal_type)
    if diet_type:
        query += " AND diet_types LIKE ?"
        params.append(f"%{diet_type}%")
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [{"id": r[0], "name_ru": r[1], "meal_type": r[2], "diet_types": r[3], "description": r[4], "calories": r[5], "protein": r[6], "fat": r[7], "carbs": r[8], "ingredients": r[9], "recipe": r[10]} for r in rows]



@app.post("/diary/add")
async def add_food_entry(request: Request):
    try:
        data = await request.json()
    except:
        raise HTTPException(400, "Invalid JSON")
    
    user_id = int(request.query_params.get("user_id", 0))
    if not user_id:
        raise HTTPException(400, "user_id required")
    
    conn = sqlite3.connect(DB_PATH)
    food_name = str(data.get("food_name", "Блюдо"))
    food = conn.execute("SELECT id FROM foods WHERE name_ru=?", (food_name,)).fetchone()
    
    if not food:
        conn.execute(
            "INSERT INTO foods (name_ru, category, calories, protein, fat, carbs) VALUES (?,?,?,?,?,?)",
            (food_name, "Блюда", 
             float(data.get("calories", 0)), 
             float(data.get("protein", 0)), 
             float(data.get("fat", 0)), 
             float(data.get("carbs", 0)))
        )
        conn.commit()
        food = conn.execute("SELECT id FROM foods WHERE name_ru=?", (food_name,)).fetchone()
    
    conn.execute(
        "INSERT INTO food_diary (user_id, food_id, grams, meal_type) VALUES (?,?,?,?)",
        (user_id, food[0], float(data.get("grams", 100)), str(data.get("meal_type", "snack")))
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "message": f"{food_name} добавлен"}



@app.post("/diary/add-meal")
async def add_meal_entry(request: Request):
    try:
        data = await request.json()
    except:
        return {"status": "error", "message": "Invalid JSON"}
    
    user_id = int(request.query_params.get("user_id", 0))
    if not user_id:
        return {"status": "error", "message": "user_id required"}
    
    # Дата: из параметра или сегодня
    date_str = str(data.get("date", datetime.date.today().isoformat()))
    
    conn = sqlite3.connect(DB_PATH)
    food_name = str(data.get("food_name", "Блюдо"))
    
    conn.execute(
        "INSERT INTO foods (name_ru, category, calories, protein, fat, carbs) VALUES (?,?,?,?,?,?)",
        (food_name, "Блюда", 
         float(data.get("calories", 0)), 
         float(data.get("protein", 0)), 
         float(data.get("fat", 0)), 
         float(data.get("carbs", 0)))
    )
    conn.commit()
    food = conn.execute("SELECT id FROM foods WHERE name_ru=?", (food_name,)).fetchone()
    
    conn.execute(
        "INSERT INTO food_diary (user_id, food_id, grams, meal_type, consumed_at) VALUES (?,?,?,?,?)",
        (user_id, food[0], float(data.get("grams", 100)), str(data.get("meal_type", "snack")), date_str)
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.post("/diary/add-meal")
async def add_meal_entry(request: Request):
    try:
        data = await request.json()
    except:
        return {"status": "error", "message": "Invalid JSON"}
    
    user_id = int(request.query_params.get("user_id", 0))
    if not user_id:
        return {"status": "error", "message": "user_id required"}
    
    # Дата: из параметра или сегодня
    date_str = str(data.get("date", datetime.date.today().isoformat()))
    
    conn = sqlite3.connect(DB_PATH)
    food_name = str(data.get("food_name", "Блюдо"))
    
    conn.execute(
        "INSERT INTO foods (name_ru, category, calories, protein, fat, carbs) VALUES (?,?,?,?,?,?)",
        (food_name, "Блюда", 
         float(data.get("calories", 0)), 
         float(data.get("protein", 0)), 
         float(data.get("fat", 0)), 
         float(data.get("carbs", 0)))
    )
    conn.commit()
    food = conn.execute("SELECT id FROM foods WHERE name_ru=?", (food_name,)).fetchone()
    
    conn.execute(
        "INSERT INTO food_diary (user_id, food_id, grams, meal_type, consumed_at) VALUES (?,?,?,?,?)",
        (user_id, food[0], float(data.get("grams", 100)), str(data.get("meal_type", "snack")), date_str)
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.get("/diet-tables")
async def get_diet_tables(goal: str = ""):
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM diet_tables"
    params = []
    if goal:
        query += " WHERE goal_relation = ?"
        params.append(goal)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "description": r[2], "recommendations": r[3], "restrictions": r[4], "goal_relation": r[5]} for r in rows]


@app.post("/diary/reset")
async def reset_diary(user_id: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM food_diary WHERE user_id=? AND consumed_at=DATE('now')", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Дневник за сегодня очищен"}


@app.get("/plan/generate")
async def generate_meal_plan(user_id: int = Query(...), diet_type: str = "omnivore"):
    conn = sqlite3.connect(DB_PATH)
    
    # Получаем метрики пользователя
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    if not metrics:
        conn.close()
        raise HTTPException(400, "Метрики не найдены. Пройдите онбординг.")
    
    gender, age, weight, height, activity, goal = metrics[1], metrics[2], metrics[3], metrics[4], metrics[5], metrics[6]
    
    # Расчёт дневной нормы
    if gender == 'male':
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
    
    mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
    
    daily_calories = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    # Макросы цели
    if goal == 'weight_loss':
        p_pct, f_pct, c_pct = 0.35, 0.25, 0.40
    elif goal == 'muscle_gain':
        p_pct, f_pct, c_pct = 0.30, 0.20, 0.50
    else:
        p_pct, f_pct, c_pct = 0.25, 0.25, 0.50
    
    target_protein = int(daily_calories * p_pct / 4)
    target_fat = int(daily_calories * f_pct / 9)
    target_carbs = int(daily_calories * c_pct / 4)
    
    # Распределение по приёмам
    meals_dist = {
        'breakfast': {'pct': 0.25, 'time': '07:00 - 09:00'},
        'lunch': {'pct': 0.35, 'time': '12:00 - 14:00'},
        'dinner': {'pct': 0.25, 'time': '17:00 - 19:00'},
        'snack': {'pct': 0.15, 'time': '10:00 - 11:00 / 16:00 - 17:00'},
    }
    
    plan = {}
    total_cal = 0
    total_p = 0
    total_f = 0
    total_c = 0
    
    for meal_type, info in meals_dist.items():
        target_cal = int(daily_calories * info['pct'])
        
        # Ищем блюда, подходящие по типу питания
        rows = conn.execute(
            "SELECT * FROM meals WHERE meal_type=? AND diet_types LIKE ? ORDER BY ABS(calories - ?) LIMIT 5",
            (meal_type, f"%{diet_type}%", target_cal)
        ).fetchall()
        
        if not rows:
            # Если нет подходящих — берём любые блюда этого типа
            rows = conn.execute(
                "SELECT * FROM meals WHERE meal_type=? ORDER BY ABS(calories - ?) LIMIT 5",
                (meal_type, target_cal)
            ).fetchall()
        
        best = rows[0] if rows else None
        
        if best:
            meal_cal = best[5]
            meal_p = best[6]
            meal_f = best[7]
            meal_c = best[8]
            
            plan[meal_type] = {
                'id': best[0],
                'name': best[1],
                'time': info['time'],
                'calories': meal_cal,
                'protein': meal_p,
                'fat': meal_f,
                'carbs': meal_c,
                'ingredients': best[9],
                'recipe': best[10],
                'target_calories': target_cal,
            }
            
            total_cal += meal_cal
            total_p += meal_p
            total_f += meal_f
            total_c += meal_c
    
    conn.close()
    
    return {
        'user_id': user_id,
        'diet_type': diet_type,
        'daily_target': {
            'calories': daily_calories,
            'protein': target_protein,
            'fat': target_fat,
            'carbs': target_carbs,
        },
        'plan': plan,
        'totals': {
            'calories': total_cal,
            'protein': total_p,
            'fat': total_f,
            'carbs': total_c,
        },
        'accuracy': {
            'calories': round(total_cal / daily_calories * 100, 1) if daily_calories > 0 else 0,
            'protein': round(total_p / target_protein * 100, 1) if target_protein > 0 else 0,
        }
    }



@app.get("/plan/weekly")
async def generate_weekly_plan(user_id: int = Query(...), diet_type: str = "omnivore"):
    conn = sqlite3.connect(DB_PATH)
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    if not metrics:
        conn.close()
        raise HTTPException(400, "Метрики не найдены — пройдите онбординг")
    
    gender, age, weight, height, activity, goal = metrics[1], metrics[2], metrics[3], metrics[4], metrics[5], metrics[6]
    
    # Расчёт BMR
    if gender == 'male':
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
    
    mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
    daily_cal = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    # Макросы
    if goal == 'weight_loss':
        p_pct, f_pct, c_pct = 0.35, 0.25, 0.40
    elif goal == 'muscle_gain':
        p_pct, f_pct, c_pct = 0.30, 0.20, 0.50
    else:
        p_pct, f_pct, c_pct = 0.25, 0.25, 0.50
    
    target_p = int(daily_cal * p_pct / 4)
    target_f = int(daily_cal * f_pct / 9)
    target_c = int(daily_cal * c_pct / 4)
    
    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # Загружаем блюда по типам
    def load_meals(meal_type):
        rows = conn.execute(
            "SELECT id, name_ru, meal_type, description, calories, protein, fat, carbs, ingredients, recipe FROM meals WHERE meal_type=? AND diet_types LIKE ?",
            (meal_type, f'%{diet_type}%')
        ).fetchall()
        if len(rows) < 3:
            rows = conn.execute(
                "SELECT id, name_ru, meal_type, description, calories, protein, fat, carbs, ingredients, recipe FROM meals WHERE meal_type=?",
                (meal_type,)
            ).fetchall()
        return rows
    
    breakfasts = load_meals('breakfast')
    lunches = load_meals('lunch')
    dinners = load_meals('dinner')
    snacks = load_meals('snack')
    
    conn.close()
    
    # Распределение калорий
    cal = {
        'breakfast': int(daily_cal * 0.25),
        'lunch': int(daily_cal * 0.35),
        'dinner': int(daily_cal * 0.25),
        'snack': int(daily_cal * 0.15),
    }
    
    week = {}
    used = set()
    
    for day_idx in range(7):
        day_date = monday + timedelta(days=day_idx)
        day_cal = 0
        day_p = 0
        day_f = 0
        day_c = 0
        day_plan = {}
        
        for meal_type, meals in [('breakfast', breakfasts), ('lunch', lunches), ('dinner', dinners), ('snack', snacks)]:
            target_cal = cal[meal_type]
            
            # Доступные блюда (не использованные)
            available = [m for m in meals if m[0] not in used]
            if len(available) < 3:
                used.clear()
                available = meals
            
            if not available:
                continue
            
            # Выбираем блюдо, ближайшее по калориям
            best = min(available, key=lambda m: abs(m[4] - target_cal))
            used.add(best[0])
            
            # Масштабируем порцию
            scale = target_cal / best[4] if best[4] > 0 else 1
            scale = round(scale, 1)
            
            cal_scaled = round(best[4] * scale)
            p_scaled = round(best[5] * scale, 1)
            f_scaled = round(best[6] * scale, 1)
            c_scaled = round(best[7] * scale, 1)
            
            day_plan[meal_type] = {
                'name': best[1],
                'description': best[3] if best[3] else '',
                'calories': cal_scaled,
                'protein': p_scaled,
                'fat': f_scaled,
                'carbs': c_scaled,
                'portion': scale,
                'ingredients': best[8] if len(best) > 8 else '',
                'recipe': best[9] if len(best) > 9 else '',
            }
            
            day_cal += cal_scaled
            day_p += p_scaled
            day_f += f_scaled
            day_c += c_scaled
        
        accuracy = round(day_cal / daily_cal * 100, 1) if daily_cal > 0 else 0
        
        week[day_date.isoformat()] = {
            'date': day_date.isoformat(),
            'day_name': day_date.strftime('%A'),
            'plan': day_plan,
            'totals': {'calories': day_cal, 'protein': round(day_p,1), 'fat': round(day_f,1), 'carbs': round(day_c,1)},
            'accuracy': accuracy
        }
    
    return {
        'weekly_target': {'calories': daily_cal, 'protein': target_p, 'fat': target_f, 'carbs': target_c},
        'week': week,
        'diet_type': diet_type,
    }


@app.post("/diary/delete")
async def delete_diary_entry(entry_id: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM food_diary WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.get("/plan/adaptive")
async def get_adaptive_plan(user_id: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    
    # Текущие метрики
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    if not metrics:
        conn.close()
        raise HTTPException(400, "Метрики не найдены")
    
    # История веса за последние 2 недели
    weight_history = conn.execute(
        "SELECT date, weight FROM daily_checkins WHERE user_id=? AND weight IS NOT NULL ORDER BY date DESC LIMIT 14",
        (user_id,)
    ).fetchall()
    
    # Последний вес
    current_weight = weight_history[0][1] if weight_history else metrics[3]
    
    # Вес 7 дней назад
    old_weight = None
    if len(weight_history) >= 7:
        old_weight = weight_history[6][1]
    elif len(weight_history) >= 2:
        old_weight = weight_history[-1][1]
    
    weight_change = round(current_weight - old_weight, 1) if old_weight else 0
    
    gender, age, height, activity, goal = metrics[1], metrics[2], metrics[4], metrics[5], metrics[6]
    
    # Базовый расчёт
    if gender == 'male':
        bmr = 88.36 + (13.4 * current_weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * current_weight) + (3.1 * height) - (4.3 * age)
    
    mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
    
    new_calories = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    old_calories = metrics[0] if len(metrics) > 6 else new_calories
    
    # Адаптация: если цель — похудение, а вес не меняется 2 недели → снижаем калории
    adjustments = []
    
    if goal == 'weight_loss':
        if weight_change >= 0:
            new_calories = int(new_calories * 0.93)
            adjustments.append("Вес стоит на месте. Снижаем калорийность на 7%")
        elif weight_change < -1:
            adjustments.append("Отличная динамика! Продолжаем в том же темпе")
        else:
            adjustments.append("Вес снижается умеренно. Корректировка не требуется")
    
    elif goal == 'muscle_gain':
        if weight_change <= 0:
            new_calories = int(new_calories * 1.07)
            adjustments.append("Вес не растёт. Увеличиваем калорийность на 7%")
        elif weight_change > 2:
            adjustments.append("Слишком быстрый набор. Снижаем калорийность")
            new_calories = int(new_calories * 0.95)
    
    elif goal == 'maintenance':
        if abs(weight_change) > 1:
            adjustments.append(f"Вес изменился на {weight_change} кг. Корректируем норму")
    
    # Обновляем метрики
    conn.execute(
        "UPDATE metrics SET weight_kg=?, updated_at=datetime('now') WHERE user_id=?",
        (current_weight, user_id)
    )
    conn.commit()
    conn.close()
    
    # Пересчитываем БЖУ
    if goal == 'weight_loss': p_pct, f_pct, c_pct = 0.35, 0.25, 0.40
    elif goal == 'muscle_gain': p_pct, f_pct, c_pct = 0.30, 0.20, 0.50
    else: p_pct, f_pct, c_pct = 0.25, 0.25, 0.50
    
    return {
        "old_calories": old_calories,
        "new_calories": new_calories,
        "current_weight": current_weight,
        "weight_change": weight_change,
        "adjustments": adjustments,
        "new_macros": {
            "protein": int(new_calories * p_pct / 4),
            "fat": int(new_calories * f_pct / 9),
            "carbs": int(new_calories * c_pct / 4),
        }
    }


@app.post("/nutri/add-xp")
async def add_xp(user_id: int = Query(...), xp: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE nutri_pet SET xp = xp + ? WHERE user_id=?", (xp, user_id))
    conn.commit()
    pet = conn.execute("SELECT xp FROM nutri_pet WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    level = int(pet[0] / 100) + 1 if pet else 1
    return {"status": "ok", "xp": pet[0] if pet else xp, "level": level}


@app.get("/discipline")
async def get_discipline(user_id: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    
    # Стрик
    pet = conn.execute("SELECT streak, best_streak FROM nutri_pet WHERE user_id=?", (user_id,)).fetchone()
    streak = pet[0] if pet else 0
    best_streak = pet[1] if pet else 0
    
    # Чекины за 7 дней
    today = datetime.date.today()
    checkins = conn.execute(
        "SELECT COUNT(*) FROM daily_checkins WHERE user_id=? AND date >= ?",
        (user_id, (today - datetime.timedelta(days=6)).isoformat())
    ).fetchone()[0]
    
    # Записи в дневнике за 7 дней
    diary_days = conn.execute(
        "SELECT COUNT(DISTINCT consumed_at) FROM food_diary WHERE user_id=? AND consumed_at >= ?",
        (user_id, (today - datetime.timedelta(days=6)).isoformat())
    ).fetchone()[0]
    
    # Дней с попаданием в норму (90-110%)
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    on_target = 0
    if metrics:
        daily_cal = 2000
        gender, age, weight, height, activity, goal = metrics[1], metrics[2], metrics[3], metrics[4], metrics[5], metrics[6]
        if gender == 'male':
            bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
        else:
            bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
        mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
        adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
        daily_cal = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    # Считаем дни в норме
    for i in range(7):
        d = (today - datetime.timedelta(days=i)).isoformat()
        cals = conn.execute(
            "SELECT SUM(f.calories * d2.grams / 100) FROM food_diary d2 JOIN foods f ON d2.food_id = f.id WHERE d2.user_id=? AND d2.consumed_at=?",
            (user_id, d)
        ).fetchone()[0] or 0
        if 0 < cals <= daily_cal * 1.2 and cals >= daily_cal * 0.8:
            on_target += 1
    
    conn.close()
    
    # Общий счёт дисциплины
    score = min(100, (streak * 10) + (checkins * 8) + (diary_days * 6) + (on_target * 10))
    
    # Ранг
    if score >= 90: rank = '🥇 Мастер дисциплины'
    elif score >= 70: rank = '🥈 Дисциплинированный'
    elif score >= 50: rank = '🥉 На пути к цели'
    elif score >= 30: rank = '📋 Начинающий'
    else: rank = '🌱 Новичок'
    
    return {
        'score': score,
        'rank': rank,
        'streak': streak,
        'best_streak': best_streak,
        'checkins_7d': checkins,
        'diary_days_7d': diary_days,
        'on_target_7d': on_target,
        'max_possible': 100,
        'message': 'Отлично!' if score >= 70 else 'Есть куда расти!' if score >= 40 else 'Начни с малого!'
    }

@app.on_event("startup")
async def startup():
    init_db()
    print("🥑 NutriAI Тамагочи-нутрициолог запущен!")
    print("📱 API: http://127.0.0.1:8000")
    print("📊 Документация: http://127.0.0.1:8000/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Render deploy trigger
