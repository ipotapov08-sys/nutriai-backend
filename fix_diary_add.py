path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoint = '''
@app.post("/diary/add")
async def add_food_entry(request: Request):
    data = await request.json()
    user_id = int(request.query_params.get("user_id", 0))
    if not user_id:
        raise HTTPException(400, "user_id required")
    
    conn = sqlite3.connect(DB_PATH)
    # Ищем или создаём продукт
    food_name = data.get("food_name", "Блюдо")
    food = conn.execute("SELECT id FROM foods WHERE name_ru=?", (food_name,)).fetchone()
    if not food:
        conn.execute(
            "INSERT INTO foods (name_ru, category, calories, protein, fat, carbs) VALUES (?,?,?,?,?,?)",
            (food_name, "Блюда", data.get("calories", 0), data.get("protein", 0), data.get("fat", 0), data.get("carbs", 0))
        )
        conn.commit()
        food = conn.execute("SELECT id FROM foods WHERE name_ru=?", (food_name,)).fetchone()
    
    conn.execute(
        "INSERT INTO food_diary (user_id, food_id, grams, meal_type) VALUES (?,?,?,?)",
        (user_id, food[0], data.get("grams", 100), data.get("meal_type", "snack"))
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "message": f"{food_name} добавлен"}

'''

# Добавляем импорт Request
if 'from fastapi import' in content:
    content = content.replace('from fastapi import FastAPI, HTTPException, Query', 'from fastapi import FastAPI, HTTPException, Query, Request')

old = '@app.on_event("startup")'
content = content.replace(old, new_endpoint + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинт /diary/add обновлён')
