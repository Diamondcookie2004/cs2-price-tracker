import sqlite3
import json

def import_skins_from_json(json_file_path):
    # 連線到資料庫 (如果沒有檔案會自動建立)
    conn = sqlite3.connect('cs2_skins.db')
    cursor = conn.cursor()

    # 建立表格
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            buff_id TEXT,
            uu_id TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skin_name TEXT,         -- 關聯到 skins 表的飾品名稱
            platform TEXT,          -- 紀錄平台 (例如: 'steam', 'buff', 'uu')
            price REAL,             -- 最低售價 (存成純數字 REAL 格式方便畫圖)
            check_time DATETIME DEFAULT CURRENT_TIMESTAMP -- 查詢時間 (自動帶入當下時間)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_skin ON price_history(skin_name);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_time ON price_history(check_time);')
    
    try:
        # 讀取 JSON 檔案
        with open(json_file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        print("🔍 正在分析 JSON 寶藏檔案...")
        
        # 根據你提供的檔案結構，所有的資料都包在 'items' 這個 Key 裡面
        items_dict = raw_data.get('items')
        
        if not items_dict:
            print("❌ 找不到 'items' 欄位，請確認 JSON 檔案格式是否正確。")
            return
            
        total_items = len(items_dict)
        print(f"✨ 發現了 {total_items} 筆飾品對應資料！開始全力匯入...")
        
        count = 0
        # items_dict 的結構是 { "飾品名稱": { "buff163_goods_id": 123, "youpin_id": 456, ... } }
        for name, details in items_dict.items():
            
            # 抓取我們需要的兩個關鍵 ID，如果 JSON 裡面沒有就補 None
            buff_id = details.get('buff163_goods_id')
            uu_id = details.get('youpin_id')
            
            # 使用 UPSERT 語法：如果名稱不存在就新增，如果已經存在就更新它的 ID
            cursor.execute('''
                INSERT INTO skins (name, buff_id, uu_id) 
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    buff_id = excluded.buff_id,
                    uu_id = excluded.uu_id
            ''', (
                name, 
                str(buff_id) if buff_id else None, 
                str(uu_id) if uu_id else None
            ))
            
            count += 1
            
            # 每處理 1000 筆印出一次進度，讓你知道程式沒當機
            if count % 1000 == 0:
                print(f"   ⏳ 目前進度: {count} / {total_items} ...")
        
        # 儲存變更
        conn.commit()
        print(f"🎉 太神啦！成功匯入/更新了 {count} 筆飾品資料與跨平台 ID！")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # 請確認這個路徑與你的 JSON 檔案位置相符
    json_path = r"D:\Project\cs2_marketplaceids.json"
    import_skins_from_json(json_path)