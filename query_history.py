import sqlite3

def check_price_history(skin_name):
    print(f"\n=== 📊 正在查詢 [{skin_name}] 的歷史價格 ===")
    
    # 連線到你的資料庫
    conn = sqlite3.connect('cs2_skins.db')
    cursor = conn.cursor()
    
    # 使用 SQL 語法：從 price_history 表格中抓取資料
    # ORDER BY check_time DESC 代表「最新抓到的價格排在最上面」
    cursor.execute('''
        SELECT platform, price, check_time 
        FROM price_history 
        WHERE skin_name = ? 
        ORDER BY check_time DESC
    ''', (skin_name,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("   ❌ 資料庫裡還沒有這把武器的價格紀錄喔！")
        print("   (請先確定你的 cross_platform_tracker.py 有成功跑過並存入資料)")
        return
        
    print(f"{'平台':<10} | {'價格 (TWD)':<15} | {'紀錄時間'}")
    print("-" * 50)
    
    for row in rows:
        platform = row[0]
        price = row[1]
        check_time = row[2]
        
        # 把平台名稱轉換成好看一點的中文
        if platform == 'steam': display_platform = 'Steam'
        elif platform == 'buff': display_platform = 'Buff'
        elif platform == 'uu': display_platform = '悠悠有品'
        else: display_platform = platform
        
        print(f"{display_platform:<10} | NT$ {price:<11.2f} | {check_time}")
    print("==================================================\n")

if __name__ == "__main__":
    # 在這裡換成你想要查詢的武器名稱
    # 記得，你的 cross_platform_tracker.py 必須先跑過，資料庫裡才會有東西！
    
    target_skin = "AK-47 | Redline (Field-Tested)"
    check_price_history(target_skin)
    
    target_skin_2 = "M4A1-S | Black Lotus (Minimal Wear)"
    check_price_history(target_skin_2)