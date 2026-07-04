path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем новый эндпоинт ДО @app.on_event
new_endpoint = '''
@app.get("/plan/weekly")
async def generate_weekly_plan(user_id: int = Query(...), diet_type: str = "omnivore"):
    conn = sqlite3.connect(DB_PATH)
    
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    if not metrics:
        conn.close()
        raise HTTPException(400, "Метрики не найдены")
    
    gender, age, weight, height, activity, goal = metrics[1], metrics[2], metrics[3], metrics[4], metrics[5], metrics[6]
    
    if gender == 'male':
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
    
    mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
    daily_calories = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    if goal == 'weight_loss':
        p_pct, f_pct, c_pct = 0.35, 0.25, 0.40
    elif goal == 'muscle_gain':
        p_pct, f_pct, c_pct = 0.30, 0.20, 0.50
    else:
        p_pct, f_pct, c_pct = 0.25, 0.25, 0.50
    
    target_p = int(daily_calories * p_pct / 4)
    target_f = int(daily_calories * f_pct / 9)
    target_c = int(daily_calories * c_pct / 4)
    
    from datetime import date, timedelta
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    
    week = {}
    for day_idx in range(7):
        day_date = monday + timedelta(days=day_idx)
        day_plan = {}
        day_cal = 0
        day_p = 0
        day_f = 0
        day_c = 0
        
        for meal_type, pct in [('breakfast', 0.25), ('lunch', 0.35), ('dinner', 0.25), ('snack', 0.15)]:
            target_cal = int(daily_calories * pct)
            
            # Поиск подходящего блюда
            rows = conn.execute(
                """SELECT * FROM meals 
                   WHERE meal_type=? AND diet_types LIKE ? 
                   ORDER BY ABS(calories - ?) LIMIT 1""",
                (meal_type, f'%{diet_type}%', target_cal)
            ).fetchone()
            
            if not rows:
                rows = conn.execute(
                    "SELECT * FROM meals WHERE meal_type=? ORDER BY ABS(calories - ?) LIMIT 1",
                    (meal_type, target_cal)
                ).fetchone()
            
            if rows:
                day_plan[meal_type] = {
                    'name': rows[1],
                    'calories': rows[5],
                    'protein': rows[6],
                    'fat': rows[7],
                    'carbs': rows[8],
                    'ingredients': rows[9],
                    'recipe': rows[10],
                    'target_cal': target_cal,
                }
                day_cal += rows[5]
                day_p += rows[6]
                day_f += rows[7]
                day_c += rows[8]
        
        week[day_date.isoformat()] = {
            'date': day_date.isoformat(),
            'day_name': day_date.strftime('%A'),
            'plan': day_plan,
            'totals': {'calories': day_cal, 'protein': day_p, 'fat': day_f, 'carbs': day_c},
            'accuracy': round(day_cal / daily_calories * 100, 1) if daily_calories > 0 else 0
        }
    
    conn.close()
    
    return {
        'weekly_target': {'calories': daily_calories, 'protein': target_p, 'fat': target_f, 'carbs': target_c},
        'week': week,
        'diet_type': diet_type,
    }
'''

old = '@app.on_event("startup")'
content = content.replace(old, new_endpoint + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Недельный план добавлен')
