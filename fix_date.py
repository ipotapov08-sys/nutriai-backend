path = 'main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Исправляем str(date.today()) → str(datetime.date.today())
content = content.replace('str(date.today())', 'str(datetime.date.today())')

# Исправляем fromisoformat
content = content.replace("d1 = datetime.date.fromisoformat(checkins[i][0])", "d1 = datetime.date.fromisoformat(checkins[i][0])")
content = content.replace("d2 = datetime.date.fromisoformat(checkins[i+1][0])", "d2 = datetime.date.fromisoformat(checkins[i+1][0])")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('OK')
