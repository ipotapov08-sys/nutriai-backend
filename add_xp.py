path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

xp_endpoint = '''
@app.post("/nutri/add-xp")
async def add_xp(user_id: int = Query(...), xp: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE nutri_pet SET xp = xp + ? WHERE user_id=?", (xp, user_id))
    conn.commit()
    pet = conn.execute("SELECT xp FROM nutri_pet WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    level = int(pet[0] / 100) + 1 if pet else 1
    return {"status": "ok", "xp": pet[0] if pet else xp, "level": level}
'''

old = '@app.on_event("startup")'
content = content.replace(old, xp_endpoint + '\n' + old)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинт XP добавлен')
