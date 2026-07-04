path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Меняем лимит повторов: для основных блюд — 2, для гарниров/салатов — 3
content = content.replace("pool = [m for m in pool if used_count.get(m[0], 0) < 2]", "pool = [m for m in pool if used_count.get(m[0], 0) < 2]")
content = content.replace("side_pool = [m for m in all_meals.get(st, []) if used_count.get(m[0], 0) < 2]", "side_pool = [m for m in all_meals.get(st, []) if used_count.get(m[0], 0) < 3]")

# Увеличиваем количество переборов до 500
content = content.replace("for _ in range(300):", "for _ in range(500):")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Лимиты обновлены: гарниры до 3 раз, перебор 500')
