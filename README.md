CS2 跨平台飾品比價儀表板 CS2 Price Tracker

專案簡介
這是一個基於 Python 與 Flask 開發的 Counter-Strike 2 飾品比價系統。
能夠自動抓取並整合 Steam 社群市場、網易 BUFF 與悠悠有品的即時價格。
系統會自動將人民幣轉換為新台幣，幫助玩家輕鬆比較跨平台的價差與尋找購買時機。

核心功能
跨平台即時比價：一鍵獲取 Steam、BUFF、悠悠有品三方最低售價。
自動匯率轉換：內建人民幣至新台幣轉換邏輯。
歷史價格追蹤：採用 SQLite 資料庫紀錄查詢歷史，利於長期價格走勢觀察。
網頁儀表板介面：提供簡潔的網頁介面，無需透過終端機即可快速查詢。
授權金鑰安全防護：使用 .env 隔離敏感的授權憑證，確保帳號安全。

技術架構
後端技術：Python 3, Flask, SQLite3
前端技術：HTML, Vanilla JavaScript, Fetch API
爬蟲技術：Requests, urllib

快速啟動指南

步驟一：安裝依賴套件
請確保電腦已安裝 Python 3，並在終端機執行以下指令安裝所需套件
pip install flask flask-cors requests python-dotenv

步驟二：設定環境變數
在專案根目錄建立一個 .env 檔案，並填入你的平台授權碼
BUFF_COOKIE="你的 BUFF COOKIE"
UUYP_TOKEN="你的 UUYP TOKEN"

步驟三：初始化資料庫
如果你是第一次執行此專案，請先建立資料庫與測試資料
python init_db.py

步驟四：啟動網頁伺服器
python app.py
啟動後，直接在瀏覽器開啟 dashboard.html 即可開始查詢價格。

免責聲明
本專案僅供學術交流與程式開發練習使用。
請勿用於高頻率的惡意抓取，以免違反各平台的服務條款導致帳號遭到封鎖。