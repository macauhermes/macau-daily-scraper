import asyncio
import os
from playwright.async_api import async_playwright

async def scrape_macau_news(browser):
    print("[+] 正在抓取澳門日報新聞...")
    page = await browser.new_page()
    news_items = []
    try:
        await page.goto("https://www.macaoday.com/", timeout=60000, wait_until="domcontentloaded")
        # Using a more robust selector for news links
        links = await page.locator('a').all()
        for link in links:
            text = (await link.inner_text()).strip()
            href = await link.get_attribute('href')
            if text and href and len(text) > 5:
                # Clean URL
                clean_url = href.replace('https://www.macaoday.com/', '').replace('https://macaoday.com/', '')
                if clean_url.startswith('/'):
                    clean_url = clean_url.lstrip('/')
                
                item = f"{text} ({clean_url})"
                if item not in news_items:
                    news_items.append(item)
            if len(news_items) >= 10:
                break
    except Exception as e:
        print(f"[!] 澳門新聞抓取錯誤: {e}")
    return news_items

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
                item = f"{text} ({clean_url})"
                if item not in news_items:
                    news_items.append(item)
            if len(news_items) >= 10:
                break
    except Exception as e:
        print(f"[!] 科技新聞抓取錯誤: {e}")
    return news_items

async def main():
    print("========================================")
    print("🚀 開始新聞抓取任務 (Macau & Tech)")
    print("========================================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        print("\n[1/2] 正在處理：澳門日報...")
        macau = await scrape_macau_news(browser)
        if macau:
            for i, item in enumerate(macau, 1):
                print(f"{i}. {item}")
        else:
            print("  未能取得澳門新聞。")

        print("\n[2/2] 正在處理：美股科技新聞...")
        tech = await scrape_tech_news(browser)
        if tech:
            for i, item in enumerate(tech, 1):
                print(f"{i}. {item}")
        else:
            print("  未能取得科技新聞。")
            
        await browser.close()
    
    print("\n========================================")
    print("✅ 任務完成！")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(main())
