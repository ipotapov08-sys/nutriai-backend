path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем новый улучшенный эндпоинт для генерации плана
new_endpoint = '''
@app.get("/plan/generate")
async def generate_meal_plan(user_id: int = Query(...), diet_type: str = "omnivore"):
    conn = sqlite3.connect(DB_PATH)
    
    # Получаем метрики пользователя
    metrics = conn.execute("SELECT * FROM metrics WHERE user_id=?", (user_id,)).fetchone()
    if not metrics:
        conn.close()
        raise HTTPException(400, "Метрики не найдены. Пройдите онбординг.")
    
    gender, age, weight, height, activity, goal = metrics[1], metrics[2], metrics[3], metrics[4], metrics[5], metrics[6]
    
    # Расчёт дневной нормы
    if gender == 'male':
        bmr = 88.36 + (13.4 * weight) + (4.8 * height) - (5.7 * age)
    else:
        bmr = 447.6 + (9.2 * weight) + (3.1 * height) - (4.3 * age)
    
    mult = {'sedentary': 1.2, 'light': 1.375, 'moderate': 1.55, 'active': 1.725, 'very_active': 1.9}
    adj = {'weight_loss': -400, 'maintenance': 0, 'muscle_gain': 300}
    
    daily_calories = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    # Макросы цели
    if goal == 'weight_loss':
        p_pct, f_pct, c_pct = 0.35, 0.25, 0.40
    elif goal == 'muscle_gain':
        p_pct, f_pct, c_pct = 0.30, 0.20, 0.50
    else:
        p_pct, f_pct, c_pct = 0.25, 0.25, 0.50
    
    target_protein = int(daily_calories * p_pct / 4)
    target_fat = int(daily_calories * f_pct / 9)
    target_carbs = int(daily_calories * c_pct / 4)
    
    # Распределение по приёмам
    meals_dist = {
        'breakfast': {'pct': 0.25, 'time': '07:00 - 09:00'},
        'lunch': {'pct': 0.35, 'time': '12:00 - 14:00'},
        'dinner': {'pct': 0.25, 'time': '17:00 - 19:00'},
        'snack': {'pct': 0.15, 'time': '10:00 - 11:00 / 16:00 - 17:00'},
    }
    
    plan = {}
    total_cal = 0
    total_p = 0
    total_f = 0
    total_c = 0
    
    for meal_type, info in meals_dist.items():
        target_cal = int(daily_calories * info['pct'])
        
        # Ищем блюда, подходящие по типу питания
        rows = conn.execute(
            "SELECT * FROM meals WHERE meal_type=? AND diet_types LIKE ? ORDER BY ABS(calories - ?) LIMIT 5",
            (meal_type, f"%{diet_type}%", target_cal)
        ).fetchall()
        
        if not rows:
            # Если нет подходящих — берём любые блюда этого типа
            rows = conn.execute(
                "SELECT * FROM meals WHERE meal_type=? ORDER BY ABS(calories - ?) LIMIT 5",
                (meal_type, target_cal)
            ).fetchall()
        
        best = rows[0] if rows else None
        
        if best:
            meal_cal = best[5]
            meal_p = best[6]
            meal_f = best[7]
            meal_c = best[8]
            
            plan[meal_type] = {
                'id': best[0],
                'name': best[1],
                'time': info['time'],
                'calories': meal_cal,
                'protein': meal_p,
                'fat': meal_f,
                'carbs': meal_c,
                'ingredients': best[9],
                'recipe': best[10],
                'target_calories': target_cal,
            }
            
            total_cal += meal_cal
            total_p += meal_p
            total_f += meal_f
            total_c += meal_c
    
    conn.close()
    
    return {
        'user_id': user_id,
        'diet_type': diet_type,
        'daily_target': {
            'calories': daily_calories,
            'protein': target_protein,
            'fat': target_fat,
            'carbs': target_carbs,
        },
        'plan': plan,
        'totals': {
            'calories': total_cal,
            'protein': total_p,
            'fat': total_f,
            'carbs': total_c,
        },
        'accuracy': {
            'calories': round(total_cal / daily_calories * 100, 1) if daily_calories > 0 else 0,
            'protein': round(total_p / target_protein * 100, 1) if target_protein > 0 else 0,
        }
    }
'''

old = '@app.on_event("startup")'
content = content.replace(old, new_endpoint + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Точный генератор плана добавлен')
