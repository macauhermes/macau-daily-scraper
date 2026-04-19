import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_macau_news(browser):
    print("[+] 正在抓取澳門日報新聞...")
    page = await browser.new_page()
    news_items = []
    try:
        # Start from homepage, it will redirect to today's date automatically
        # Then use the base URL to build page numbers
        
        page_num = 2  # node_2.htm is the first news section
        base_url = "https://www.macaodaily.com/html"
        
        while len(news_items) < 10:
            url = f"{base_url}/node_{page_num}.htm"
            print(f"    正在抓取: node_{page_num}.htm")
            
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(1500)
            
            # Extract news titles from content links
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
            
            # Safety limit: don't check more than 20 pages
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
        
        print("\n🇲🇴 澳門日報\n" + "─" * 30)
        macau = await scrape_macau_news(browser)
        if macau:
            for i, item in enumerate(macau, 1):
                print(f"{i}. {item}")
        else:
            print("未能取得澳門新聞。")

        print("\n🇺🇸 美股科技新聞\n" + "─" * 30)
        tech = await scrape_tech_news(browser)
        if tech:
            for i, item in enumerate(tech, 1):
                print(f"{i}. {item}")
        else:
            print("未能取得科技新聞。")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
