import sqlite3
import os

# 確保資料庫建立在目前資料夾
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'cs2_skins.db')

def init_database():
    print("=== 🛠️ 開始初始化資料庫 ===")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. 建立 skins 表格 (加上 UNIQUE 限制，避免同樣的武器重複存入)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            steam_hash TEXT NOT NULL,
            buff_id TEXT NOT NULL,
            uu_id TEXT NOT NULL
        )
    ''')

    # 2. 建立 price_history 歷史價格表格 (如果你還沒建立的話)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skin_name TEXT NOT NULL,
            platform TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 寫入初始資料 (使用 INSERT OR IGNORE 忽略已經存在的重複資料)
    items = [
        ("AK-47 | 紅線 (戰場實測)", "AK-47 | Redline (Field-Tested)", "33975", "10167"),
        ("M4A1-S | 毀滅者 2000 (戰場實測)", "M4A1-S | Mecha Industries (Field-Tested)", "34997", "108612")
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO skins (name, steam_hash, buff_id, uu_id) 
        VALUES (?, ?, ?, ?)
    ''', items)
    
    conn.commit()
    conn.close()
    print("✅ 資料庫與資料表建立成功！(已過濾重複的測試資料)")

if __name__ == '__main__':
    init_database()