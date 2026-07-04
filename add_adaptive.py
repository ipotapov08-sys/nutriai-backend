path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

adaptive_endpoint = '''
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
'''

old = '@app.on_event("startup")'
content = content.replace(old, adaptive_endpoint + '\n' + old)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Адаптивный план добавлен')
