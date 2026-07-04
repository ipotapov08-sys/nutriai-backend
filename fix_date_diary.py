path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем /diary/add-meal — добавляем параметр date
old = '''@app.post("/diary/add-meal")
async def add_meal_entry(request: Request):
    try:
        data = await request.json()
    except:
        return {"status": "error", "message": "Invalid JSON"}
    
    user_id = int(request.query_params.get("user_id", 0))
    if not user_id:
        return {"status": "error", "message": "user_id required"}
    
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
        "INSERT INTO food_diary (user_id, food_id, grams, meal_type) VALUES (?,?,?,?)",
        (user_id, food[0], float(data.get("grams", 100)), str(data.get("meal_type", "snack")))
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}'''

new = '''@app.post("/diary/add-meal")
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
    return {"status": "ok"}'''

content = content.replace(old, new)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Дата добавлена в /diary/add-meal')
