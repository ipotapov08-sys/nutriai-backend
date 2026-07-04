path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

endpoint = '''
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
'''

old = '@app.on_event("startup")'
content = content.replace(old, endpoint + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинт /diet-tables добавлен')
