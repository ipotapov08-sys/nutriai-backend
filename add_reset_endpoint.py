path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

endpoint = '''
@app.post("/diary/reset")
async def reset_diary(user_id: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM food_diary WHERE user_id=? AND consumed_at=DATE('now')", (user_id,))
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Дневник за сегодня очищен"}
'''

old = '@app.on_event("startup")'
content = content.replace(old, endpoint + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинт /diary/reset добавлен')
