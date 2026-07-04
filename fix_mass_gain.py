import sqlite3
conn = sqlite3.connect('nutriai.db')
c = conn.cursor()

mass_gainer_meals = [
    ('Масс-гейнер домашний', 'breakfast', 'omnivore,vegetarian',
     'Сверхкалорийный завтрак', 850, 35, 30, 100,
     'Овсянка 100 г, Молоко 400 мл, Банан 120 г, Арахисовая паста 40 г, Мёд 30 г', 'Всё взбить в блендере'),
    ('Панкейки с шоколадом и бананом', 'breakfast', 'omnivore,vegetarian',
     'Десертный завтрак', 700, 18, 25, 95,
     'Мука 120 г, Молоко 200 мл, Яйцо 1 шт, Шоколад 50 г, Банан 100 г, Сироп', 'Испечь панкейки, украсить'),
    ('Яичница из 4 яиц с беконом', 'breakfast', 'omnivore,keto',
     'Мощный белковый завтрак', 620, 38, 48, 2,
     'Яйца 4 шт, Бекон 80 г, Сыр 50 г', 'Обжарить'),
    
    ('Стейк из лосося с рисом', 'lunch', 'omnivore,mediterranean',
     'Двойная порция', 750, 42, 32, 65,
     'Лосось 250 г, Рис 100 г, Масло сливочное 20 г', 'Запечь, рис отварить'),
    ('Паста Болоньезе', 'lunch', 'omnivore,mediterranean',
     'Большая порция', 800, 35, 32, 85,
     'Макароны 120 г, Фарш 200 г, Томатный соус 100 г, Сыр 50 г', 'Обжарить фарш, смешать с пастой'),
    ('Жаркое из свинины с картофелем', 'lunch', 'omnivore',
     'Деревенское блюдо', 820, 38, 40, 70,
     'Свинина 200 г, Картофель 250 г, Лук 50 г, Масло 30 мл', 'Тушить в горшочке 1 час'),
    
    ('Курица гриль с картофелем фри', 'dinner', 'omnivore',
     'Ресторанная порция', 780, 42, 35, 68,
     'Курица 250 г, Картофель 200 г, Масло 30 мл', 'Запечь курицу, картофель фри'),
    ('Говядина с макаронами', 'dinner', 'omnivore',
     'Паста с мясом', 720, 40, 28, 70,
     'Говядина 200 г, Макароны 100 г, Сыр 40 г', 'Обжарить, смешать'),
    
    ('Гейнер с протеином', 'snack', 'omnivore,vegetarian',
     'Спортивный перекус', 450, 35, 10, 55,
     'Молоко 400 мл, Протеин 40 г, Банан 100 г, Овсянка 30 г', 'Взбить'),
    ('Бутерброд с курицей и сыром', 'snack', 'omnivore',
     'Двойной бутерброд', 420, 30, 18, 35,
     'Хлеб 80 г, Курица 100 г, Сыр 40 г, Майонез 15 г', 'Собрать'),
    ('Творожная масса с вареньем', 'snack', 'omnivore,vegetarian',
     'Сладкий белок', 350, 28, 15, 28,
     'Творог 200 г, Сметана 30 г, Варенье 40 г', 'Смешать'),
]

for m in mass_gainer_meals:
    c.execute('INSERT INTO meals (name_ru, meal_type, diet_types, description, calories, protein, fat, carbs, ingredients, recipe) VALUES (?,?,?,?,?,?,?,?,?,?)', m)

conn.commit()
print(f'Блюд для набора массы: {len(mass_gainer_meals)}')

# Обновим main.py — для mass_gain подбираем только калорийные блюда
path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Снижаем целевой процент для mass_gain, чтобы подбирать более калорийные блюда
old_breakfast = "('breakfast', int(daily_cal * 0.25)"
old_lunch = "('lunch', int(daily_cal * 0.35)"
old_dinner = "('dinner', int(daily_cal * 0.25)"
old_snack = "('snack', int(daily_cal * 0.15)"

# Для mass_gain увеличиваем порции
new_breakfast = "('breakfast', int(daily_cal * 0.30) if goal == 'muscle_gain' else int(daily_cal * 0.25)"
new_lunch = "('lunch', int(daily_cal * 0.40) if goal == 'muscle_gain' else int(daily_cal * 0.35)"
new_dinner = "('dinner', int(daily_cal * 0.20) if goal == 'muscle_gain' else int(daily_cal * 0.25)"
new_snack = "('snack', int(daily_cal * 0.10) if goal == 'muscle_gain' else int(daily_cal * 0.15)"

content = content.replace(old_breakfast, new_breakfast)
content = content.replace(old_lunch, new_lunch)
content = content.replace(old_dinner, new_dinner)
content = content.replace(old_snack, new_snack)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Пропорции для mass_gain: 30/40/20/10')
conn.close()
