import requests
import sqlite3
import time
import random
import os
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

# ⚠️ 修改這裡：不再貼上實際的 API，而是讓程式去 .env 裡面抓！
BUFF_COOKIE = os.getenv("BUFF_COOKIE")
UUYP_TOKEN = os.getenv("UUYP_TOKEN")

# ==========================================
# 核心大網函數
# ==========================================
def fetch_buff_bulk_page(page_num):
    """抓取 BUFF 市場列表的整頁資料 (一頁 80 筆)"""
    # 這個 API 網址不再綁定 goods_id，而是直接請求第幾頁
    url = f"https://buff.163.com/api/market/goods?game=csgo&page_num={page_num}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Cookie': BUFF_COOKIE
    }
    
    try:
        print(f"🕸️ 正在撒網... 撈取 BUFF 第 {page_num} 頁資料...")
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        
        if data.get('code') == 'OK':
            items = data.get('data', {}).get('items', [])
            print(f"✅ 成功在第 {page_num} 頁撈到 {len(items)} 把武器！")
            return items
        else:
            print(f"❌ 撈取失敗，BUFF 回傳訊息: {data.get('error')}")
            return []
    except Exception as e:
        print(f"❌ 連線發生錯誤: {e}")
        return []

def save_bulk_prices(items):
    """將整網的武器一次性存入資料庫"""
    if not items: return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_count = 0
    for item in items:
        # BUFF 回傳的資料非常豐富，我們取出標準英文名稱、價格、和在售數量
        market_name = item.get('market_hash_name')
        cny_price = float(item.get('sell_min_price', 0))
        twd_price = cny_price * EXCHANGE_RATE_CNY_TO_TWD
        
        # 把最新價格寫入你的 price_history 歷史表格
        if twd_price > 0 and market_name:
            cursor.execute('''
                INSERT INTO price_history (skin_name, platform, price)
                VALUES (?, ?, ?)
            ''', (market_name, 'buff', twd_price))
            saved_count += 1
            
    conn.commit()
    conn.close()
    print(f"💾 批次儲存完畢！成功將 {saved_count} 筆最新報價寫入資料庫！\n")

# ==========================================
# 實驗啟動區塊
# ==========================================
if __name__ == "__main__":
    print("=== 🚢 啟動 BUFF 大網撈魚實驗號 ===")
    
    # 測試抓取第 1 頁與第 2 頁 (共 160 把目前最熱門的武器)
    for page in range(1, 3):
        items = fetch_buff_bulk_page(page)
        
        # 為了讓你感受大網的威力，我們印出前 3 把武器當作預覽
        if items:
            print("   🔍 漁獲預覽 (前 3 把)：")
            for i in range(min(3, len(items))):
                name = items[i].get('market_hash_name')
                price = float(items[i].get('sell_min_price', 0)) * EXCHANGE_RATE_CNY_TO_TWD
                sell_num = items[i].get('sell_num', 0) # 順便看一下有多少人在賣
                print(f"      - {name} | 最低價: NT$ {price:.2f} | 在售數量: {sell_num} 把")
            
        # 寫入資料庫
        save_bulk_prices(items)
        
        # ⚠️ 保護機制：雖然我們抓得很快，但每翻一頁一定要隨機休息一下
        # 否則 1 秒鐘翻 10 頁，BUFF 防火牆會立刻把你封鎖！
        sleep_time = random.uniform(3.0, 6.0)
        print(f"⏳ 避免被系統封鎖，休息 {sleep_time:.1f} 秒...\n")
        time.sleep(sleep_time)
        
    print("🎉 實驗大豐收！只發出了 2 次請求，就更新了 160 把武器的價格！")
    print("👉 現在你可以去 dashboard.html 搜尋最熱門的 AK-47 紅線，看看圖表是不是出來了！")