import sqlite3

# 建立或連線資料庫
conn = sqlite3.connect('cs2_skins.db')
cursor = conn.cursor()

# 建立表格
cursor.execute('''
    CREATE TABLE IF NOT EXISTS skins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        steam_hash TEXT NOT NULL,
        buff_id TEXT NOT NULL,
        uu_id TEXT NOT NULL
    )
''')

# 寫入測試資料 (之後你可以自己手動增加更多)
items = [
    ("AK-47 | 紅線 (戰場實測)", "AK-47 | Redline (Field-Tested)", "33975", "10167"),
    ("M4A1-S | 毀滅者 2000 (戰場實測)", "M4A1-S | Mecha Industries (Field-Tested)", "34997", "108612")
]

cursor.executemany('INSERT INTO skins (name, steam_hash, buff_id, uu_id) VALUES (?, ?, ?, ?)', items)
conn.commit()
conn.close()

print("資料庫建立成功！已存入測試飾品。")