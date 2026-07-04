path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_marker = '@app.get("/plan/weekly")'
next_marker = '@app.on_event("startup")'

start_idx = content.find(old_marker)
end_idx = content.find(next_marker, start_idx)

new_weekly = r'''@app.get("/plan/weekly")
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
    
    # Загружаем блюда: основные (lunch/dinner) и завтраки (breakfast)
    main_meals = conn.execute(
        "SELECT * FROM meals WHERE meal_type IN ('lunch','dinner','breakfast','snack') AND diet_types LIKE ?",
        (f'%{diet_type}%',)
    ).fetchall()
    
    if len(main_meals) < 5:
        main_meals = conn.execute(
            "SELECT * FROM meals WHERE meal_type IN ('lunch','dinner','breakfast','snack')"
        ).fetchall()
    
    # Гарниры и салаты
    sides = conn.execute(
        "SELECT * FROM meals WHERE meal_type IN ('side','salad') AND diet_types LIKE ?",
        (f'%{diet_type}%',)
    ).fetchall()
    
    if len(sides) < 3:
        sides = conn.execute("SELECT * FROM meals WHERE meal_type IN ('side','salad')").fetchall()
    
    conn.close()
    
    week = {}
    used_main = {}
    used_side = {}
    
    for day_idx in range(7):
        day_date = monday + timedelta(days=day_idx)
        day_cal = 0
        day_p = 0
        day_f = 0
        day_c = 0
        
        # Структура дня: Завтрак, Обед (первое + второе + салат), Ужин, Перекус
        structure = []
        
        # Завтрак (25%)
        pool = [m for m in main_meals if m[2] == 'breakfast' and used_main.get(m[0], 0) < 3]
        if not pool: pool = [m for m in main_meals if m[2] == 'breakfast']
        if pool:
            best = min(pool, key=lambda m: abs(m[5] - daily_cal * 0.25))
            structure.append(('breakfast', 'Завтрак', [best], daily_cal * 0.25))
        
        # Обед (40%) — первое + второе + салат
        lunch_main_pool = [m for m in main_meals if m[2] == 'lunch' and used_main.get(m[0], 0) < 3]
        if not lunch_main_pool: lunch_main_pool = [m for m in main_meals if m[2] == 'lunch']
        
        lunch_items = []
        if lunch_main_pool:
            best = min(lunch_main_pool, key=lambda m: abs(m[5] - daily_cal * 0.20))
            lunch_items.append(best)
        
        side_pool = [s for s in sides if used_side.get(s[0], 0) < 4]
        if not side_pool: side_pool = sides
        if side_pool:
            salad = [s for s in side_pool if s[2] == 'salad']
            if salad:
                lunch_items.append(random.choice(salad[:3]))
            else:
                lunch_items.append(random.choice(side_pool[:3]))
        
        if lunch_items:
            structure.append(('lunch', 'Обед', lunch_items, daily_cal * 0.40))
        
        # Ужин (25%) — основное + гарнир
        dinner_pool = [m for m in main_meals if m[2] in ('lunch','dinner') and used_main.get(m[0], 0) < 3]
        if not dinner_pool: dinner_pool = [m for m in main_meals if m[2] in ('lunch','dinner')]
        
        dinner_items = []
        if dinner_pool:
            best = min(dinner_pool, key=lambda m: abs(m[5] - daily_cal * 0.17))
            dinner_items.append(best)
        
        side_pool2 = [s for s in sides if used_side.get(s[0], 0) < 4]
        if not side_pool2: side_pool2 = sides
        if side_pool2:
            dinner_items.append(random.choice(side_pool2[:3]))
        
        if dinner_items:
            structure.append(('dinner', 'Ужин', dinner_items, daily_cal * 0.25))
        
        # Перекус (10%)
        snack_pool = [m for m in main_meals if m[2] == 'snack' and used_main.get(m[0], 0) < 3]
        if not snack_pool: snack_pool = [m for m in main_meals if m[2] == 'snack']
        if snack_pool:
            best = min(snack_pool, key=lambda m: abs(m[5] - daily_cal * 0.10))
            structure.append(('snack', 'Перекус', [best], daily_cal * 0.10))
        
        # Формируем ответ
        day_plan = {}
        for meal_key, meal_name, items, _ in structure:
            items_data = []
            total_cal = 0
            total_p = 0
            total_f = 0
            total_carb = 0
            
            for item in items:
                mid = item[0]
                if item[2] in ('breakfast','lunch','dinner','snack'):
                    used_main[mid] = used_main.get(mid, 0) + 1
                else:
                    used_side[mid] = used_side.get(mid, 0) + 1
                
                # Масштабируем порцию под целевые калории
                scale = 1.0
                if item[5] > 0:
                    # Подгоняем под нужный процент дня
                    target_for_meal = daily_cal * (0.25 if meal_key == 'breakfast' else 0.40 if meal_key == 'lunch' else 0.25 if meal_key == 'dinner' else 0.10)
                    scale = target_for_meal / item[5] / len(items)
                    scale = max(0.8, min(1.5, scale))  # Ограничиваем масштаб
                
                cal = round(item[5] * scale)
                p = round(item[6] * scale, 1)
                f = round(item[7] * scale, 1)
                cb = round(item[8] * scale, 1)
                
                items_data.append({
                    'name': item[1],
                    'calories': cal,
                    'protein': p,
                    'fat': f,
                    'carbs': cb,
                    'recipe': item[10] if len(item) > 10 else '',
                    'ingredients': item[9] if len(item) > 9 else '',
                })
                total_cal += cal
                total_p += p
                total_f += f
                total_carb += cb
            
            day_plan[meal_key] = {
                'name': meal_name,
                'items': items_data,
                'calories': total_cal,
                'protein': round(total_p, 1),
                'fat': round(total_f, 1),
                'carbs': round(total_carb, 1),
            }
            day_cal += total_cal
            day_p += total_p
            day_f += total_f
            day_c += total_carb
        
        accuracy = round(day_cal / daily_cal * 100, 1) if daily_cal > 0 else 0
        
        week[day_date.isoformat()] = {
            'date': day_date.isoformat(),
            'day_name': day_date.strftime('%A'),
            'plan': day_plan,
            'totals': {'calories': day_cal, 'protein': round(day_p, 1), 'fat': round(day_f, 1), 'carbs': round(day_c, 1)},
            'accuracy': accuracy
        }
    
    return {
        'weekly_target': {'calories': daily_cal, 'protein': target_p, 'fat': target_f, 'carbs': target_c},
        'week': week,
        'diet_type': diet_type,
    }
'''

content = content[:start_idx] + new_weekly + '\n' + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Новый алгоритм плана: порции вместо множества блюд')
