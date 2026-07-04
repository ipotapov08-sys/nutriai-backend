import sqlite3, hashlib
conn = sqlite3.connect('nutriai.db')
c = conn.cursor()

# Ищем пользователя
c.execute("SELECT id, email, full_name FROM users WHERE email=?", ('ipotapo08@yandex.ru',))
user = c.fetchone()

if user:
    print(f'ID: {user[0]}')
    print(f'Email: {user[1]}')
    print(f'Имя: {user[2]}')
    
    # Сбрасываем пароль
    new_pass = '123456'
    new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
    c.execute("UPDATE users SET password_hash=? WHERE email=?", (new_hash, 'ipotapo08@yandex.ru'))
    conn.commit()
    print(f'Пароль сброшен на: {new_pass}')
else:
    print('Пользователь не найден')
    # Создаём нового
    new_pass = '123456'
    new_hash = hashlib.sha256(new_pass.encode()).hexdigest()
    c.execute("INSERT INTO users (email, password_hash, full_name) VALUES (?,?,?)", ('ipotapo08@yandex.ru', new_hash, 'Ivan'))
    conn.commit()
    print(f'Пользователь создан! Пароль: {new_pass}')

conn.close()
