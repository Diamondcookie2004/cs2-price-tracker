import requests
import time
import random
import sqlite3
from urllib.parse import quote
import os
from dotenv import load_dotenv

# 🌟 啟動套件，讓程式去讀取隱藏的 .env 檔案
load_dotenv()
# ⚠️ 修改這裡：不再貼上實際的 API，而是讓程式去 .env 裡面抓！
BUFF_COOKIE = os.getenv("BUFF_COOKIE")
UUYP_TOKEN = os.getenv("UUYP_TOKEN")

# ==========================================
# 1. 參數設定區
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 將資料庫路徑綁定在程式同一個資料夾下
DB_PATH = os.path.join(BASE_DIR, 'cs2_skins.db')

EXCHANGE_RATE_CNY_TO_TWD = 4.45

# 你現在想測試追蹤的飾品 (必須與 Steam 名稱完全一致)
# 我們先挑兩個測試，成功後你可以無限增加！
TARGET_SKINS = [
    "AK-47 | Redline (Field-Tested)",
    "M4A1-S | Black Lotus (Minimal Wear)"
    "AK-47 | Elite Build (Factory New)"
]

# ==========================================
# 2. 資料庫操作函數
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
    """將抓到的價格存入歷史紀錄表"""
    if price <= 0:
        return # 抓取失敗或價格為0則不儲存，保持資料庫乾淨
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO price_history (skin_name, platform, price)
        VALUES (?, ?, ?)
    ''', (skin_name, platform, price))
    conn.commit()
    conn.close()

# ==========================================
# 3. 各平台爬蟲函數 (已整合除錯後的 Headers)
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/json',
        'Authorization': auth_token,
        'Origin': 'https://www.youpin898.com',
        'Deviceid': 'f538b826-d07f-4d98-b30c-a650c77896b5',
        'Deviceuk': '5HwikZPaHncugGanaQqkw66vWXh3mKamg3eqtBy4M9Pcm98CidywazgKKgfBwUP1P',
        'Platform': 'pc',
        'Apptype': '1',
        'App-Version': '5.26.0',
        'Appversion': '5.26.0',
        'Secret-V': 'h5_v1',
        'Uk': '5FDLM4skZo9bz3lNKkG6c4Bun2E5kQ2v5C2B92oSp4t5G8gda7sm3gFQ608QsPd1E'
    }
    
    payload = {
        "gameId": "730",
        "listType": "10",
        "templateId": str(uu_id), 
        "listSortType": 1,
        "sortType": 0,
        "pageIndex": 1,
        "pageSize": 10
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        data = res.json()
        
        # 悠悠 API 使用大寫 Code, Data
        if str(data.get('Code')) == '0':
            items = data.get('Data', [])
            if items:
                cny_price = float(items[0].get('price', 0))
                return cny_price * EXCHANGE_RATE_CNY_TO_TWD
        elif str(data.get('Code')) == '-1':
            print(f"   [警告] 悠悠回傳系統繁忙，請稍後再試或延長休息時間")
    except Exception as e:
        print(f"   [除錯] 悠悠 API 異常: {e}")
    return 0

def fetch_and_save_single(skin_name):
    """
    這個函數是爬蟲的核心模組：提供給 app.py 呼叫，或是自己獨立執行
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT buff_id, uu_id FROM skins WHERE name = ?", (skin_name,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return False, '資料庫中找不到此飾品 ID'
            
        buff_id, uu_id = row
        
        steam_price = get_steam_price_twd(skin_name)
        buff_price = get_buff_price_twd(buff_id)
        uu_price = get_uu_price_twd(uu_id)
        
        # 只要有任何一個平台成功抓到，就存入資料庫
        if steam_price > 0: cursor.execute("INSERT INTO price_history (skin_name, platform, price) VALUES (?, ?, ?)", (skin_name, 'steam', steam_price))
        if buff_price > 0: cursor.execute("INSERT INTO price_history (skin_name, platform, price) VALUES (?, ?, ?)", (skin_name, 'buff', buff_price))
        if uu_price > 0: cursor.execute("INSERT INTO price_history (skin_name, platform, price) VALUES (?, ?, ?)", (skin_name, 'uu', uu_price))
        
        conn.commit()
        conn.close()
        return True, '抓取成功'
    except Exception as e:
        return False, str(e)

# ==========================================
# 獨立測試 / 批次執行區塊
# ==========================================
if __name__ == '__main__':
    print("=== Main 爬蟲程式獨立執行測試 ===")
    test_skins = ["AK-47 | Redline (Field-Tested)"]
    for skin in test_skins:
        print(f"正在抓取 {skin} ...")
        success, msg = fetch_and_save_single(skin)
        print(f"結果: {msg}")
        time.sleep(2)
# ==========================================
# 4. 執行主程式
# ==========================================
if __name__ == "__main__":
    print("=== 開始跨平台商品價格對比 (寫入資料庫版) ===")
    
    for skin in TARGET_SKINS:
        print("-" * 40)
        print(f"📦 正在查詢 [{skin}] ...")
        
        # 從資料庫提取 ID
        db_info = get_skin_info_from_db(skin)
        if not db_info:
            print("   ❌ 資料庫中找不到此飾品，請確認名稱是否與 Steam 一致")
            continue
            
        buff_id = db_info['buff_id']
        uu_id = db_info['uu_id']
        
        # 爬取價格
        steam_price = get_steam_price_twd(skin)
        buff_price = get_buff_price_twd(buff_id)
        uu_price = get_uu_price_twd(uu_id)
        
        # 顯示結果
        print(f"   👉 Steam 最低價: {'NT$ {:.2f}'.format(steam_price) if steam_price else '獲取失敗'}")
        print(f"   👉 Buff  最低價: {'NT$ {:.2f}'.format(buff_price) if buff_price else '獲取失敗'}")
        print(f"   👉 悠悠  最低價: {'NT$ {:.2f}'.format(uu_price) if uu_price else '獲取失敗'}")
        
        # 寫入資料庫歷史紀錄表
        save_price_to_db(skin, 'steam', steam_price)
        save_price_to_db(skin, 'buff', buff_price)
        save_price_to_db(skin, 'uu', uu_price)
        print("   💾 已將成功抓取的價格寫入資料庫 price_history 表")
        
        # 隨機休息，避免被封鎖 (8到15秒)
        sleep_time = random.uniform(8.0, 15.0)
        print(f"   ⏳ 休息 {sleep_time:.1f} 秒...")
        time.sleep(sleep_time)

    print("\n=== 價格對比任務結束 ===")