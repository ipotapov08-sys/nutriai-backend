import sqlite3
conn = sqlite3.connect('nutriai.db')
c = conn.cursor()

# 5 разных сценариев
users = [
    (1, 'male', 30, 80, 180, 'moderate', 'maintenance'),
    (2, 'female', 28, 70, 165, 'moderate', 'weight_loss'),
    (3, 'male', 25, 75, 178, 'active', 'muscle_gain'),
    (4, 'female', 35, 60, 160, 'light', 'maintenance'),
    (5, 'male', 40, 100, 175, 'sedentary', 'weight_loss'),
]

for u in users:
    uid, g, a, w, h, act, goal = u
    c.execute('INSERT OR REPLACE INTO metrics VALUES (?,?,?,?,?,?,?,datetime("now"))', (uid, g, a, w, h, act, goal))
    c.execute('INSERT OR IGNORE INTO users (id, email, password_hash, full_name) VALUES (?,?,?,?)', (uid, f'user{uid}@test.com', 'hash', f'User {uid}'))

conn.commit()
conn.close()
print('5 пользователей создано')
