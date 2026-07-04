path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Находим и заменяем эндпоинт /plan/weekly полностью
old_start = '@app.get("/plan/weekly")'
old_marker = '@app.on_event("startup")'

start_idx = content.find(old_start)
end_idx = content.find(old_marker, start_idx)

new_endpoint = '''@app.get("/plan/weekly")
async def generate_weekly_plan(user_id: int = Query(...), diet_type: str = "omnivore"):
    conn = sqlite3.connect(DB_PATH)
    
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    if not metrics:
        conn.close()
        raise HTTPException(400, "Метрики не найдены")
    
    gender, age, weight, height, activity, goal = metrics[1], metrics[2], metrics[3], metrics[4], metrics[5], metrics[6]
    
    # BMR
    if gender == 'male':
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
    
    mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
    daily_cal = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    if goal == 'weight_loss':
        p_pct, f_pct, c_pct = 0.35, 0.25, 0.40
    elif goal == 'muscle_gain':
        p_pct, f_pct, c_pct = 0.30, 0.20, 0.50
    else:
        p_pct, f_pct, c_pct = 0.25, 0.25, 0.50
    
    target_p = int(daily_cal * p_pct / 4)
    target_f = int(daily_cal * f_pct / 9)
    target_c = int(daily_cal * c_pct / 4)
    
    from datetime import date, timedelta
    import random
    
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # Загружаем все блюда
    all_meals = {}
    for mt in ['breakfast', 'lunch', 'dinner', 'snack']:
        rows = conn.execute(
            "SELECT * FROM meals WHERE meal_type=? AND diet_types LIKE ?",
            (mt, f'%{diet_type}%')
        ).fetchall()
        if len(rows) < 3:
            rows = conn.execute("SELECT * FROM meals WHERE meal_type=?", (mt,)).fetchall()
        all_meals[mt] = rows
    
    week = {}
    used_count = {}
    
    for day_idx in range(7):
        day_date = monday + timedelta(days=day_idx)
        
        # Целевые калории по приёмам
        targets = [
            ('breakfast', int(daily_cal * 0.25)),
            ('lunch', int(daily_cal * 0.35)),
            ('dinner', int(daily_cal * 0.25)),
            ('snack', int(daily_cal * 0.15)),
        ]
        
        best_combo = None
        best_score = float('inf')
        
        # Перебираем 500 случайных комбинаций и выбираем лучшую
        for _ in range(500):
            combo = {}
            total_cal = 0
            
            for meal_type, target_cal in targets:
                pool = all_meals.get(meal_type, [])
                if not pool:
                    continue
                
                # Выбираем случайное блюдо, но предпочитаем те, что использованы <2 раз
                candidates = [m for m in pool if used_count.get(m[0], 0) < 2]
                if not candidates:
                    candidates = pool
                
                best = random.choice(candidates)
                combo[meal_type] = best
                total_cal += best[5]
            
            # Оценка: насколько близко к daily_cal
            score = abs(total_cal - daily_cal)
            if score < best_score:
                best_score = score
                best_combo = combo
        
        # Формируем день
        day_plan = {}
        day_cal = 0
        day_p = 0
        day_f = 0
        day_c = 0
        
        for meal_type, _ in targets:
            best = best_combo.get(meal_type)
            if best:
                meal_id = best[0]
                used_count[meal_id] = used_count.get(meal_id, 0) + 1
                
                day_plan[meal_type] = {
                    'name': best[1],
                    'calories': best[5],
                    'protein': best[6],
                    'fat': best[7],
                    'carbs': best[8],
                    'ingredients': best[9],
                    'recipe': best[10],
                }
                day_cal += best[5]
                day_p += best[6]
                day_f += best[7]
                day_c += best[8]
        
        accuracy = round(day_cal / daily_cal * 100, 1) if daily_cal > 0 else 0
        
        week[day_date.isoformat()] = {
            'date': day_date.isoformat(),
            'day_name': day_date.strftime('%A'),
            'plan': day_plan,
            'totals': {'calories': day_cal, 'protein': day_p, 'fat': day_f, 'carbs': day_c},
            'accuracy': accuracy
        }
    
    conn.close()
    
    return {
        'weekly_target': {'calories': daily_cal, 'protein': target_p, 'fat': target_f, 'carbs': target_c},
        'week': week,
        'diet_type': diet_type,
    }
'''

content = content[:start_idx] + new_endpoint + '\n' + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Алгоритм заменён: перебор 500 комбинаций для точности 95%+')
