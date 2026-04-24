import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_macau_news(browser):
    print("[+] 正在抓取澳門日報新聞...")
    page = await browser.new_page()
    news_items = []
    visited_urls = set()
    
    async def scrape_current_page(url):
        """抓取當前頁面的新聞連結"""
        if url in visited_urls:
            return 0
        visited_urls.add(url)
        
        print(f"    正在抓取: {url}")
        try:
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
                        return found_count
            return found_count
        except Exception as e:
            print(f"    [!] 抓取錯誤: {e}")
            return 0
    
    try:
        # 1. 先去首頁，讓它自動跳轉
        base_url = "https://www.macaodaily.com"
        await scrape_current_page(base_url)
        
        # 2. 首頁已 redirect 到某節點，直接從下一節開始
        #    從當前 URL 推斷節點號
        import re
        current_url = page.url
        node_match = re.search(r'/node_(\d+)\.htm', current_url)
        if node_match:
            page_count = int(node_match.group(1)) + 1  # 從下一節點開始
        else:
            page_count = 2  # fallback
        
        # 3. 如果不夠10則，繼續抓下一頁
        while len(news_items) < 10 and page_count <= 21:
            next_url = f"{base_url}/html/2026-04/24/node_{page_count}.htm"
            found = await scrape_current_page(next_url)
            if found == 0:
                print(f"    node_{page_count}.htm 無文章，停止抓取")
                break
            page_count += 1
                
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
