path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoint = '''
@app.get("/diet-types")
async def get_diet_types():
    return [
        {"id": "omnivore", "name": "Всеядный", "icon": "🍖", "description": "Сбалансированное питание, включающее все группы продуктов", "features": ["Мясо и рыба", "Молочные продукты", "Овощи и фрукты", "Крупы и злаки"], "exclude": []},
        {"id": "vegetarian", "name": "Вегетарианский", "icon": "🥬", "description": "Исключает мясо, но допускает молочные продукты и яйца", "features": ["Молочные продукты", "Яйца", "Овощи и фрукты", "Бобовые"], "exclude": ["Мясо", "Птица", "Рыба", "Морепродукты"]},
        {"id": "vegan", "name": "Веганский", "icon": "🌱", "description": "Полностью растительное питание", "features": ["Овощи и фрукты", "Бобовые", "Орехи и семена", "Соевые"], "exclude": ["Мясо", "Птица", "Рыба", "Морепродукты", "Молочные", "Яйца"]},
        {"id": "keto", "name": "Кето / LCHF", "icon": "🥑", "description": "Высокожировое низкоуглеводное питание", "features": ["Жирное мясо и рыба", "Яйца", "Масла", "Орехи"], "exclude": ["Сахар", "Крупы", "Хлеб", "Бобовые"]},
        {"id": "mediterranean", "name": "Средиземноморский", "icon": "🫒", "description": "Традиционная кухня Средиземноморья", "features": ["Оливковое масло", "Рыба", "Овощи", "Цельнозерновые"], "exclude": ["Переработанное мясо"]},
        {"id": "low_carb", "name": "Низкоуглеводный", "icon": "🍗", "description": "Ограничение углеводов", "features": ["Мясо и рыба", "Овощи", "Яйца", "Молочные"], "exclude": ["Сахар", "Хлеб", "Макароны", "Рис", "Картофель"]}
    ]

'''

old = '@app.on_event("startup")'
content = content.replace(old, new_endpoint + '\n' + old)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('OK')
