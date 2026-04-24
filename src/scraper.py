import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_macau_news(browser):
    print("[+] 正在抓取澳門日報新聞...")
    page = await browser.new_page()
    news_items = []
    try:
        # 直接去首頁，會自動跳轉到今日日期頁面
        base_url = "https://www.macaodaily.com"
        
        print(f"    正在抓取: {base_url}")
        await page.goto(base_url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        
        # 取得 redirect 後的 URL，提取日期路徑
        current_url = page.url
        print(f"    跳轉到: {current_url}")
        
        # 從 URL 提取日期路徑，例如 /html/2026-04/24/
        import re
        date_match = re.search(r'/html/(\d{4}-\d{2}/\d{2})/', current_url)
        if not date_match:
            print("[!] 無法取得日期路徑")
            return []
        date_path = date_match.group(1)  # e.g., "2026-04/24"
        html_base = f"{base_url}/html/{date_path}"
        
        # 從首頁抓取新聞連結
        links = await page.locator('a[href*="content_"]').all()
        for link in links:
            text = (await link.inner_text()).strip()
            if text and len(text) > 5 and text not in news_items:
                news_items.append(text)
                if len(news_items) >= 10:
                    break
        
        # 如果不夠10則，嘗試抓取更多頁面 (從 node_3 開始，因為首頁已是 node_2)
        page_num = 3
        while len(news_items) < 10:
            url = f"{html_base}/node_{page_num}.htm"
            print(f"    正在抓取: node_{page_num}.htm")
            
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            
            links = await page.locator('a[href*="content_"]').all()
            found_count = 0
            for link in links:
                text = (await link.inner_text()).strip()
                if text and len(text) > 5 and text not in news_items:
                    news_items.append(text)
                    found_count += 1
                    if len(news_items) >= 10:
                        break
            
            if found_count == 0:
                print(f"    node_{page_num}.htm 無文章，停止抓取")
                break
                
            page_num += 1
            if page_num > 21:
                break
                
    except Exception as e:
        print(f"[!] 澳門新聞抓取錯誤: {e}")
    return news_items[:10]

async def scrape_tech_news(browser):
    print("[+] 正在抓取美股科技新聞...")
    page = await browser.new_page()
    news_items = []
    # Using Google News for tech trends
    url = "https://news.google.com/search?q=tech+stocks+nvidia+apple+tesla&hl=en-US&gl=US&ceid=US:en"
    try:
        await page.goto(url, timeout=60000, wait_until="networkidle")
        # Google News article links often have 'a' tags within 'article'
        links = await page.locator('a').all()
        for link in links:
            text = (await link.inner_text()).strip()
            href = await link.get_attribute('href')
            if text and href and len(text) > 15:
                if href.startswith('./'):
                    href = "https://news.google.com" + href
                
                # Cleanify relatively simple
                clean_url = href.split('?')[0] # Remove tracking params
                if text not in news_items:
                    news_items.append(text)
            if len(news_items) >= 10:
                break
    except Exception as e:
        print(f"[!] 科技新聞抓取錯誤: {e}")
    return news_items

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        print("\n\n🇲🇴 澳門日報")
        macau = await scrape_macau_news(browser)
        if macau:
            for i, item in enumerate(macau, 1):
                print(f"{i}. {item}")
        else:
            print("未能取得澳門新聞。")

        print("\n\n🇺🇸 美股科技新聞")
        tech = await scrape_tech_news(browser)
        if tech:
            for i, item in enumerate(tech, 1):
                print(f"{i}. {item}")
        else:
            print("未能取得科技新聞。")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
