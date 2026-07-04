path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

endpoint = '''
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

'''

old = '@app.on_event("startup")'
content = content.replace(old, endpoint + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинт /meals добавлен')
