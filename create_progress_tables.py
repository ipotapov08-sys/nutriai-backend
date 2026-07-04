import sqlite3
conn = sqlite3.connect('nutriai.db')
c = conn.cursor()

c.executescript('''
    -- Ежедневные чекины
    CREATE TABLE IF NOT EXISTS daily_checkins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL,
        weight REAL,
        mood TEXT,
        energy_level INTEGER,
        sleep_hours REAL,
        water_ml INTEGER,
        notes TEXT,
        completed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, date),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- Еженедельные отчёты
    CREATE TABLE IF NOT EXISTS weekly_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        week_start DATE NOT NULL,
        avg_calories_planned REAL,
        avg_calories_actual REAL,
        avg_protein REAL,
        avg_fat REAL,
        avg_carbs REAL,
        weight_change REAL,
        compliance_rate REAL,
        nutri_state TEXT,
        recommendations TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, week_start),
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- Предупреждения
    CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- Цели и их изменения
    CREATE TABLE IF NOT EXISTS goal_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        old_weight REAL,
        new_weight REAL,
        old_calories REAL,
        new_calories REAL,
        reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
''')

conn.commit()
print('Таблицы прогресса созданы')
conn.close()
