path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

progress_endpoints = '''
# ==================== СИСТЕМА ПРОГРЕССА ====================

@app.post("/checkin")
async def daily_checkin(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    date_str = data.get("date", str(date.today()))
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        INSERT OR REPLACE INTO daily_checkins (user_id, date, weight, mood, energy_level, sleep_hours, water_ml, notes, completed)
        VALUES (?,?,?,?,?,?,?,?,1)
    ''', (user_id, date_str, data.get("weight"), data.get("mood"), 
          data.get("energy_level"), data.get("sleep_hours"), data.get("water_ml"), data.get("notes")))
    conn.commit()
    
    # Проверяем стрик чекинов
    checkins = conn.execute('''
        SELECT date FROM daily_checkins WHERE user_id=? ORDER BY date DESC LIMIT 30
    ''', (user_id,)).fetchall()
    
    streak = 1
    from datetime import timedelta
    for i in range(len(checkins)-1):
        d1 = date.fromisoformat(checkins[i][0])
        d2 = date.fromisoformat(checkins[i+1][0])
        if (d1 - d2).days == 1:
            streak += 1
        else:
            break
    
    conn.execute("UPDATE nutri_pet SET streak=? WHERE user_id=?", (streak, user_id))
    conn.commit()
    conn.close()
    
    return {"status": "ok", "streak": streak, "message": f"Чекин принят! Стрик: {streak} дней"}


@app.get("/progress/weekly-report")
async def get_weekly_report(user_id: int = Query(...)):
    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    conn = sqlite3.connect(DB_PATH)
    
    # Данные за неделю
    week_data = conn.execute('''
        SELECT date, weight, mood, energy_level, sleep_hours, water_ml
        FROM daily_checkins 
        WHERE user_id=? AND date >= ? AND date <= ?
        ORDER BY date
    ''', (user_id, monday.isoformat(), today.isoformat())).fetchall()
    
    # Питание за неделю
    nutrition = conn.execute('''
        SELECT d.consumed_at, SUM(f.calories * d.grams / 100), SUM(f.protein * d.grams / 100),
               SUM(f.fat * d.grams / 100), SUM(f.carbs * d.grams / 100)
        FROM food_diary d JOIN foods f ON d.food_id = f.id
        WHERE d.user_id=? AND d.consumed_at >= ? AND d.consumed_at <= ?
        GROUP BY d.consumed_at
    ''', (user_id, monday.isoformat(), today.isoformat())).fetchall()
    
    # Метрики пользователя
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    
    checkin_days = len(week_data)
    avg_cal = sum(r[1] for r in nutrition) / max(len(nutrition), 1)
    
    # Вес
    weights = [r[1] for r in week_data if r[1]]
    weight_change = round(weights[-1] - weights[0], 1) if len(weights) >= 2 else 0
    
    compliance = round(checkin_days / 7 * 100, 1)
    
    # Рекомендации
    recommendations = []
    if compliance < 70:
        recommendations.append("⚠️ Низкая дисциплина чек-инов. Нутри ждёт тебя каждый день!")
    if weight_change > 0 and metrics and metrics[6] == 'weight_loss':
        recommendations.append("📈 Вес растёт при цели похудения. Пересмотри рацион.")
    if avg_cal > 0 and metrics:
        target = 2000
        if metrics[1] == 'male':
            target = 88.36 + 13.4*metrics[3] + 4.8*metrics[4] - 5.7*metrics[2]
        else:
            target = 447.6 + 9.2*metrics[3] + 3.1*metrics[4] - 4.3*metrics[2]
        if avg_cal > target * 1.2:
            recommendations.append("🔥 Превышение калорий. Нутри советует снизить порции.")
    if checkin_days == 7:
        recommendations.append("✅ Отличная дисциплина! Ты проверялся каждый день!")
    
    return {
        "week": f"{monday} - {today}",
        "checkin_days": checkin_days,
        "compliance": compliance,
        "avg_calories": round(avg_cal, 1),
        "weight_change": weight_change,
        "checkins": [{"date": r[0], "weight": r[1], "mood": r[2]} for r in week_data],
        "recommendations": recommendations,
        "nutri_message": "🥑 Ты молодец!" if compliance >= 70 else "🥑 Нутри грустит... Проверяйся чаще!"
    }
'''

old = '@app.on_event("startup")'
content = content.replace(old, progress_endpoints + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинты прогресса добавлены')
