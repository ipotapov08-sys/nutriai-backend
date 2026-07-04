path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Повышаем лимит: основные блюда — 3 раза
content = content.replace("pool = [m for m in pool if used_count.get(m[0], 0) < 2]", "pool = [m for m in pool if used_count.get(m[0], 0) < 3]")

# Гарниры/салаты — 4 раза
content = content.replace("side_pool = [m for m in all_meals.get(st, []) if used_count.get(m[0], 0) < 3]", "side_pool = [m for m in all_meals.get(st, []) if used_count.get(m[0], 0) < 4]")

# Увеличиваем перебор до 2000
content = content.replace("for _ in range(1000):", "for _ in range(2000):")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('OK: повторы до 3-4, перебор 2000')
