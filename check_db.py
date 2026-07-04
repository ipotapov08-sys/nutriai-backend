import sqlite3
conn = sqlite3.connect('nutriai.db')
c = conn.cursor()

print('ТАБЛИЦЫ В БАЗЕ:')
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for row in c.fetchall():
    print(f'  - {row[0]}')

print()
print('ПРОДУКТЫ:')
c.execute('SELECT COUNT(*) FROM foods')
print(f'  Всего: {c.fetchone()[0]} шт.')

c.execute('SELECT id, name_ru, calories FROM foods LIMIT 5')
for row in c.fetchall():
    print(f'  {row[0]}. {row[1]} - {row[2]} ккал')

print()
print('ПОЛЬЗОВАТЕЛИ:')
c.execute('SELECT id, email, full_name FROM users')
users = c.fetchall()
if users:
    for row in users:
        print(f'  ID:{row[0]} | {row[1]} | {row[2]}')
else:
    print('  (пусто)')

print()
print('МЕТРИКИ:')
c.execute('SELECT * FROM metrics')
metrics = c.fetchall()
if metrics:
    for row in metrics:
        print(f'  Пользователь {row[0]}: пол={row[1]}, возраст={row[2]}, вес={row[3]}, рост={row[4]}')
else:
    print('  (пусто)')

print()
print('ДНЕВНИК:')
c.execute('SELECT COUNT(*) FROM food_diary')
print(f'  Записей: {c.fetchone()[0]}')

print()
print('ПИТОМЕЦ:')
c.execute('SELECT user_id, name, state, level, xp, streak FROM nutri_pet')
pets = c.fetchall()
if pets:
    for row in pets:
        print(f'  {row[1]} (user {row[0]}): {row[2]} | lvl {row[3]} | xp {row[4]} | streak {row[5]}')
else:
    print('  (пусто)')

print()
print('ДОСТИЖЕНИЯ:')
c.execute('SELECT COUNT(*) FROM achievements')
print(f'  Всего: {c.fetchone()[0]}')

print()
print('ВОДА:')
c.execute('SELECT COUNT(*) FROM water_tracking')
print(f'  Записей: {c.fetchone()[0]}')

conn.close()
print()
print('=== ПРОВЕРКА ЗАВЕРШЕНА ===')
