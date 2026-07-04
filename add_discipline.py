path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

endpoint = '''
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
'''

old = '@app.on_event("startup")'
content = content.replace(old, endpoint + '\n' + old)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Эндпоинт дисциплины добавлен')
