path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_marker = '@app.get("/plan/weekly")'
next_marker = '@app.on_event("startup")'

start_idx = content.find(old_marker)
end_idx = content.find(next_marker, start_idx)

new_plan = r'''@app.get("/plan/weekly")
async def generate_weekly_plan(user_id: int = Query(...), diet_type: str = "omnivore"):
    conn = sqlite3.connect(DB_PATH)
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    if not metrics:
        conn.close()
        raise HTTPException(400, "Метрики не найдены — пройдите онбординг")
    
    gender, age, weight, height, activity, goal = metrics[1], metrics[2], metrics[3], metrics[4], metrics[5], metrics[6]
    
    # Расчёт BMR
    if gender == 'male':
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
    
    mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
    daily_cal = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    # Макросы
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
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    # Загружаем блюда по типам
    def load_meals(meal_type):
        rows = conn.execute(
            "SELECT id, name_ru, meal_type, description, calories, protein, fat, carbs, ingredients, recipe FROM meals WHERE meal_type=? AND diet_types LIKE ?",
            (meal_type, f'%{diet_type}%')
        ).fetchall()
        if len(rows) < 3:
            rows = conn.execute(
                "SELECT id, name_ru, meal_type, description, calories, protein, fat, carbs, ingredients, recipe FROM meals WHERE meal_type=?",
                (meal_type,)
            ).fetchall()
        return rows
    
    breakfasts = load_meals('breakfast')
    lunches = load_meals('lunch')
    dinners = load_meals('dinner')
    snacks = load_meals('snack')
    
    conn.close()
    
    # Распределение калорий
    cal = {
        'breakfast': int(daily_cal * 0.25),
        'lunch': int(daily_cal * 0.35),
        'dinner': int(daily_cal * 0.25),
        'snack': int(daily_cal * 0.15),
    }
    
    week = {}
    used = set()
    
    for day_idx in range(7):
        day_date = monday + timedelta(days=day_idx)
        day_cal = 0
        day_p = 0
        day_f = 0
        day_c = 0
        day_plan = {}
        
        for meal_type, meals in [('breakfast', breakfasts), ('lunch', lunches), ('dinner', dinners), ('snack', snacks)]:
            target_cal = cal[meal_type]
            
            # Доступные блюда (не использованные)
            available = [m for m in meals if m[0] not in used]
            if len(available) < 3:
                used.clear()
                available = meals
            
            if not available:
                continue
            
            # Выбираем блюдо, ближайшее по калориям
            best = min(available, key=lambda m: abs(m[4] - target_cal))
            used.add(best[0])
            
            # Масштабируем порцию
            scale = target_cal / best[4] if best[4] > 0 else 1
            scale = round(scale, 1)
            
            cal_scaled = round(best[4] * scale)
            p_scaled = round(best[5] * scale, 1)
            f_scaled = round(best[6] * scale, 1)
            c_scaled = round(best[7] * scale, 1)
            
            day_plan[meal_type] = {
                'name': best[1],
                'description': best[3] if best[3] else '',
                'calories': cal_scaled,
                'protein': p_scaled,
                'fat': f_scaled,
                'carbs': c_scaled,
                'portion': scale,
                'ingredients': best[8] if len(best) > 8 else '',
                'recipe': best[9] if len(best) > 9 else '',
            }
            
            day_cal += cal_scaled
            day_p += p_scaled
            day_f += f_scaled
            day_c += c_scaled
        
        accuracy = round(day_cal / daily_cal * 100, 1) if daily_cal > 0 else 0
        
        week[day_date.isoformat()] = {
            'date': day_date.isoformat(),
            'day_name': day_date.strftime('%A'),
            'plan': day_plan,
            'totals': {'calories': day_cal, 'protein': round(day_p,1), 'fat': round(day_f,1), 'carbs': round(day_c,1)},
            'accuracy': accuracy
        }
    
    return {
        'weekly_target': {'calories': daily_cal, 'protein': target_p, 'fat': target_f, 'carbs': target_c},
        'week': week,
        'diet_type': diet_type,
    }
'''

content = content[:start_idx] + new_plan + '\n' + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Новый алгоритм: 1 блюдо на приём, масштабирование, БЖУ')
