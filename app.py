from flask import Flask, jsonify, request
import sqlite3
import time
from flask_cors import CORS
import os

# 【超級關鍵】：這行絕對不能漏掉！沒有這行，下面的 fetch_now 就會報錯找不到 cs2_main
import cs2_main

app = Flask(__name__)
# 允許跨網域請求 (讓 dashboard.html 可以順利連線)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 將資料庫路徑綁定在程式同一個資料夾下
DB_PATH = os.path.join(BASE_DIR, 'cs2_skins.db')

# 全域冷卻時間 (保護網頁的抓取按鈕不被連點)
last_fetch_time = 0
COOLDOWN_SECONDS = 15

@app.route('/api/search', methods=['GET'])
def search_skins():
    """終極版搜尋：支援多重關鍵字與忽略符號"""
    keyword = request.args.get('q', '')
    if not keyword: 
        return jsonify({'success': True, 'results': []})
        
    # 將輸入的字串用空格切開，變成多個搜尋條件 (例如輸入 "ak47 redline" 會變成 ['ak47', 'redline'])
    keywords = keyword.lower().split()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 動態組合 SQL 語法：確保每個關鍵字都有被比對到
        query = "SELECT name FROM skins WHERE "
        conditions = []
        params = []
        
        for kw in keywords:
            # 忽略連字號 (讓 ak47 可以對應到 AK-47)
            kw_clean = kw.replace('-', '')
            # 在資料庫的比對中也忽略連字號
            conditions.append("REPLACE(LOWER(name), '-', '') LIKE ?")
            params.append(f'%{kw_clean}%')
            
        # 把條件用 AND 串接起來 (必須同時包含所有關鍵字)，並限制顯示 100 筆
        query += " AND ".join(conditions) + " LIMIT 100"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'success': True, 'results': [row[0] for row in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history', methods=['GET'])
def get_skin_history():
    """獲取歷史價格供圖表顯示"""
    skin_name = request.args.get('skin')
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT platform, price, check_time FROM price_history WHERE skin_name = ? ORDER BY check_time ASC', (skin_name,))
        rows = cursor.fetchall()
        conn.close()

        history_data = {'steam': [], 'buff': [], 'uu': []}
        for platform, price, check_time in rows:
            if platform in history_data:
                history_data[platform].append({'time': check_time[5:16], 'price': price})

        return jsonify({'success': True, 'skin_name': skin_name, 'history': history_data, 'has_data': len(rows) > 0})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/fetch_now', methods=['POST'])
def fetch_now():
    """網頁一鍵抓取功能 (呼叫 cs2_main.py 執行)"""
    global last_fetch_time
    
    current_time = time.time()
    # 防護機制：如果距離上次抓取不到 15 秒，就擋下來
    if current_time - last_fetch_time < COOLDOWN_SECONDS:
        wait_time = int(COOLDOWN_SECONDS - (current_time - last_fetch_time))
        return jsonify({'success': False, 'error': f'請等待 {wait_time} 秒後再抓取。'})

    skin_name = request.json.get('skin')
    if not skin_name:
        return jsonify({'success': False, 'error': '未提供飾品名稱'})

    # 這裡會呼叫 cs2_main，所以最上面一定要有 import cs2_main
    success, msg = cs2_main.fetch_and_save_single(skin_name)
    
    if success:
        last_fetch_time = time.time()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': msg})

if __name__ == '__main__':
    print("🚀 API 伺服器已啟動 (已成功綁定 cs2_main.py 模組)！")
    print("👉 現在你可以去資料夾點擊兩下打開 dashboard.html 了！")
    app.run(debug=True, port=5000)