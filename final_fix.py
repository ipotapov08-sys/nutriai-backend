import sqlite3
conn = sqlite3.connect('nutriai.db')
c = conn.cursor()

reserve_meals = [
    ('Яичница с помидорами', 'breakfast', 'omnivore,vegetarian,low_carb,keto', 'Классика', 180, 12, 14, 3, 'Яйца 2 шт, Помидор 50 г, Масло', 'Обжарить'),
    ('Творог с зеленью и огурцом', 'breakfast', 'omnivore,vegetarian,low_carb,keto', 'Солёный завтрак', 150, 20, 8, 4, 'Творог 150 г, Огурец 50 г, Укроп', 'Смешать'),
    ('Овсяноблин с бананом', 'breakfast', 'omnivore,vegetarian', 'Фитнес-завтрак', 220, 10, 8, 28, 'Овсянка 30 г, Яйцо 1 шт, Банан 50 г', 'Замесить, пожарить'),
    ('Запеканка рисовая с изюмом', 'breakfast', 'omnivore,vegetarian', 'Сладкая', 200, 6, 5, 35, 'Рис 60 г, Молоко 100 мл, Изюм 20 г, Яйцо', 'Запечь'),
    ('Тосты с авокадо и лососем', 'breakfast', 'omnivore,mediterranean', 'Ресторанный', 290, 14, 16, 22, 'Хлеб 50 г, Авокадо 40 г, Лосось 50 г', 'Поджарить хлеб, выложить'),
    ('Суп-пюре из цветной капусты', 'lunch', 'vegetarian,vegan,omnivore,low_carb', 'Нежный', 120, 5, 6, 14, 'Цветная капуста 200 г, Сливки 30 мл', 'Отварить, взбить'),
    ('Картофельная запеканка с фаршем', 'lunch', 'omnivore', 'Сытная', 350, 20, 16, 30, 'Картофель 200 г, Фарш 100 г, Сыр 30 г', 'Запечь слоями'),
    ('Котлеты куриные на пару', 'dinner', 'omnivore,low_carb,keto', 'Диетические', 190, 22, 10, 4, 'Филе куриное 150 г, Лук 30 г, Яйцо', 'Измельчить, на пару 20 мин'),
    ('Запеканка из кабачков с сыром', 'dinner', 'vegetarian,omnivore,low_carb', 'Лёгкая', 130, 8, 8, 8, 'Кабачок 200 г, Яйцо 1 шт, Сыр 30 г', 'Запечь'),
    ('Творожная паста с фруктами', 'snack', 'omnivore,vegetarian', 'Десерт', 160, 14, 5, 16, 'Творог 120 г, Банан 50 г, Какао 5 г', 'Взбить блендером'),
    ('Кефир с отрубями и ягодами', 'snack', 'omnivore,vegetarian,low_carb', 'Полезный', 110, 6, 3, 16, 'Кефир 200 мл, Отруби 10 г, Ягоды 30 г', 'Смешать'),
    ('Сырная тарелка с виноградом', 'snack', 'omnivore,vegetarian,low_carb,keto', 'Элегантный', 190, 10, 14, 8, 'Сыр 50 г, Виноград 50 г, Орехи 10 г', 'Нарезать'),
]

for m in reserve_meals:
    c.execute('INSERT INTO meals (name_ru, meal_type, diet_types, description, calories, protein, fat, carbs, ingredients, recipe) VALUES (?,?,?,?,?,?,?,?,?,?)', m)

conn.commit()
print(f'Резервных блюд добавлено: {len(reserve_meals)}')
conn.close()

# Обновим main.py — увеличим перебор до 3000
path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('for _ in range(2000):', 'for _ in range(3000):')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Перебор: 3000')
