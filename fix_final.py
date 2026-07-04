import sqlite3
conn = sqlite3.connect('nutriai.db')
c = conn.cursor()

extra_sides = [
    ('Чечевица с овощами', 'side', 'vegan,vegetarian,omnivore,mediterranean', 'Тушёная чечевица', 130, 9.0, 3.0, 18.0, 'Чечевица — 60 г, Морковь — 50 г, Лук — 30 г', 'Отварить чечевицу, добавить зажарку'),
    ('Перловка с грибами', 'side', 'vegan,vegetarian,omnivore', 'Перловая каша', 120, 3.8, 2.5, 22.0, 'Перловка — 60 г, Шампиньоны — 80 г, Лук', 'Отварить перловку, обжарить с грибами'),
    ('Рис с кукурузой', 'side', 'vegan,vegetarian,omnivore,mediterranean', 'Яркий гарнир', 140, 3.5, 2.0, 28.0, 'Рис — 60 г, Кукуруза — 50 г, Масло', 'Смешать'),
    ('Пюре из тыквы', 'side', 'vegan,vegetarian,omnivore,keto,low_carb', 'Нежное пюре', 60, 1.5, 2.0, 10.0, 'Тыква — 200 г, Сливки — 20 мл', 'Запечь тыкву, взбить'),
]

extra_salads = [
    ('Салат Коул-слоу', 'salad', 'vegan,vegetarian,omnivore,low_carb', 'Капуста, морковь, яблоко', 50, 1.5, 2.0, 7.0, 'Капуста — 80 г, Морковь — 40 г, Яблоко — 40 г', 'Нашинковать, заправить'),
    ('Салат из огурцов с йогуртом', 'salad', 'vegetarian,omnivore,low_carb', 'Тцацики', 40, 3.0, 2.0, 4.0, 'Огурец — 100 г, Йогурт — 50 г, Чеснок', 'Нарезать, смешать'),
    ('Салат из помидоров с моцареллой', 'salad', 'vegetarian,omnivore,low_carb,mediterranean', 'Капрезе', 150, 8.0, 10.0, 4.0, 'Помидор — 100 г, Моцарелла — 60 г, Базилик', 'Нарезать, выложить слоями'),
    ('Салат Мимоза', 'salad', 'omnivore,keto,low_carb', 'Рыбный салат', 180, 12.0, 14.0, 3.0, 'Горбуша консерв. — 80 г, Яйцо — 1 шт, Сыр — 20 г', 'Слоями: рыба, белок, сыр, желток'),
]

# Меняем лимит в бэкенде
for m in extra_sides + extra_salads:
    c.execute('INSERT INTO meals (name_ru, meal_type, diet_types, description, calories, protein, fat, carbs, ingredients, recipe) VALUES (?,?,?,?,?,?,?,?,?,?)', m)

conn.commit()
print(f'Добавлено {len(extra_sides)} гарниров и {len(extra_salads)} салатов')

# Обновим main.py — увеличим перебор до 1000
path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('for _ in range(500):', 'for _ in range(1000):')
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Перебор увеличен до 1000')
conn.close()
