path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

endpoint = '''
@app.post("/diary/delete")
async def delete_diary_entry(entry_id: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM food_diary WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    return {"status": "ok"}
'''

old = '@app.on_event("startup")'
content = content.replace(old, endpoint + '\n' + old)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинт /diary/delete добавлен')
