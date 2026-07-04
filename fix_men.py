path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Добавляем коэффициент для мужчин после расчёта BMR
old = "daily_cal = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))"
new = """daily_cal = int(bmr * mult.get(activity, 1.55) + adj.get(goal, 0))
    
    # Для мужчин с высокими нормами (>2800) удваиваем порции гарниров и салатов
    double_sides = (gender == 'male' and daily_cal > 2800)"""

content = content.replace(old, new)

# В генерации плана добавляем удвоение гарниров
old_side = """for st in side_types:
                    side_pool = [m for m in all_meals.get(st, []) if used_count.get(m[0], 0) < 4]"""

new_side = """for st in side_types:
                    side_pool = [m for m in all_meals.get(st, []) if used_count.get(m[0], 0) < 4]
                    # Для мужчин с высокими нормами — двойная порция
                    if double_sides and side_pool:
                        combo[meal_key].append(side_pool[0])
                        total += side_pool[0][5]"""

content = content.replace(old_side, new_side)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Удвоение гарниров для мужчин')
