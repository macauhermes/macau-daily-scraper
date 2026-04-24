# Macau Daily Scraper

每日自動抓取澳門日報及美股科技新聞頭條。

## 功能

- 🗞️ **澳門日報**：從 macaodaily.com 抓取本地新聞標題
- 📈 **美股科技新聞**：從 Google News 抓取科技股動態（Nvidia、Apple、Tesla 等）

## 安裝

```bash
pip install -r requirements.txt
playwright install chromium
```

## 使用

```bash
python src/scraper.py
```

## 輸出範例

```
🇲🇴 澳門日報
1. 全民閱讀十分鐘
2. 文化局：新中圖料二八年完工
...

🇺🇸 美股科技新聞
1. Best Tech Stocks to Buy in 2026: Magnificent Seven & Beyond
2. Nvidia Stock (NVDA): $1 Trillion Order Backlog
...
```

## 技術棧

- Python 3.11
- Playwright (網頁爬蟲)
- BeautifulSoup4 (HTML 解析)
