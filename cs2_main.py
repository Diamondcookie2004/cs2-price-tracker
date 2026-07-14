import requests
import sqlite3
import os
from urllib.parse import quote
from dotenv import load_dotenv

# 🌟 啟動套件，讓程式去讀取隱藏的 .env 檔案
load_dotenv()

# ==========================================
# 1. 參數設定區
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 將資料庫路徑綁定在程式同一個資料夾下
DB_PATH = os.path.join(BASE_DIR, 'cs2_skins.db')
EXCHANGE_RATE_CNY_TO_TWD = 4.45

# 安全讀取環境變數
BUFF_COOKIE = os.getenv("BUFF_COOKIE")
UUYP_TOKEN = os.getenv("UUYP_TOKEN")

# ==========================================
# 2. 共用資料庫操作
# ==========================================
def get_skin_info_from_db(skin_name):
    """從資料庫中獲取飾品的跨平台 ID"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT buff_id, uu_id FROM skins WHERE name = ?", (skin_name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"buff_id": row[0], "uu_id": row[1]}
    return None

def save_price_to_db(skin_name, platform, price):
    """將抓到的單筆價格存入歷史紀錄表"""
    if price <= 0:
        return 
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO price_history (skin_name, platform, price)
        VALUES (?, ?, ?)
    ''', (skin_name, platform, price))
    conn.commit()
    conn.close()

# ==========================================
# 3. [功能 A] 單筆跨平台精準查詢 (給網頁即時查詢用)
# ==========================================
def get_steam_price_twd(market_hash_name):
    """獲取 Steam 台灣區 (TWD) 最低售價"""
    encoded_name = quote(market_hash_name)
    url = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency=30&market_hash_name={encoded_name}"
    
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data.get('success'):
            price_str = data.get('lowest_price', '0')
            clean_price = float(price_str.replace('NT$', '').replace(',', '').strip())
            return clean_price
    except Exception as e:
        print(f"   [除錯] Steam API 異常: {e}")
    return 0

def get_buff_price_twd(buff_id):
    """獲取 Buff 最低售價並轉換為 TWD"""
    if not buff_id: return 0
    url = f"https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id={buff_id}&page_num=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': BUFF_COOKIE
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        if data.get('code') == 'OK':
            items = data.get('data', {}).get('items', [])
            if items:
                cny_price = float(items[0].get('price', 0))
                return cny_price * EXCHANGE_RATE_CNY_TO_TWD
    except Exception as e:
        print(f"   [除錯] Buff API 異常: {e}")
    return 0

def get_uu_price_twd(uu_id):
    """獲取悠悠飾品最低售價並轉換為 TWD"""
    if not uu_id: return 0
    url = "https://api.youpin898.com/api/homepage/pc/goods/market/queryOnSaleCommodityList"
    auth_token = UUYP_TOKEN if UUYP_TOKEN.startswith("Bearer ") else f"Bearer {UUYP_TOKEN}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/json',
        'Authorization': auth_token,
        'Deviceid': 'f538b826-d07f-4d98-b30c-a650c77896b5',
        'Platform': 'pc'
    }
    payload = {"gameId": "730", "listType": "10", "templateId": str(uu_id), "sortType": 0, "pageIndex": 1, "pageSize": 10}
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        data = res.json()
        if str(data.get('Code')) == '0':
            items = data.get('Data', [])
            if items:
                cny_price = float(items[0].get('price', 0))
                return cny_price * EXCHANGE_RATE_CNY_TO_TWD
    except Exception as e:
        print(f"   [除錯] 悠悠 API 異常: {e}")
    return 0

def fetch_and_save_single(skin_name):
    """單筆查詢主程式：提供給 app.py 呼叫"""
    try:
        db_info = get_skin_info_from_db(skin_name)
        if not db_info:
            return False, '資料庫中找不到此飾品 ID'
            
        buff_id, uu_id = db_info['buff_id'], db_info['uu_id']
        
        steam_price = get_steam_price_twd(skin_name)
        buff_price = get_buff_price_twd(buff_id)
        uu_price = get_uu_price_twd(uu_id)
        
        save_price_to_db(skin_name, 'steam', steam_price)
        save_price_to_db(skin_name, 'buff', buff_price)
        save_price_to_db(skin_name, 'uu', uu_price)
        
        return True, '抓取成功'
    except Exception as e:
        return False, str(e)

# ==========================================
# 4. [功能 B] BUFF 大量批次抓取 (給未來的自動化排程用)
# ==========================================
def fetch_buff_bulk_page(page_num):
    """抓取 BUFF 市場列表的整頁資料 (一頁 80 筆)"""
    url = f"https://buff.163.com/api/market/goods?game=csgo&page_num={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Cookie': BUFF_COOKIE
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        if data.get('code') == 'OK':
            return data.get('data', {}).get('items', [])
    except Exception as e:
        print(f"批次連線發生錯誤: {e}")
    return []

def save_bulk_prices(items):
    """將整網的武器一次性存入資料庫"""
    if not items: return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved_count = 0
    
    for item in items:
        market_name = item.get('market_hash_name')
        cny_price = float(item.get('sell_min_price', 0))
        twd_price = cny_price * EXCHANGE_RATE_CNY_TO_TWD
        
        if twd_price > 0 and market_name:
            cursor.execute('''
                INSERT INTO price_history (skin_name, platform, price)
                VALUES (?, ?, ?)
            ''', (market_name, 'buff', twd_price))
            saved_count += 1
            
    conn.commit()
    conn.close()
    return saved_count