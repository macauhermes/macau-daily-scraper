import asyncio
import os
import re
import subprocess
import time
from datetime import date
from html import unescape
from playwright.async_api import async_playwright


def curl_get(url, referer=None):
    """使用 curl 抓取頁面原始 HTML"""
    headers = [
        'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    if referer:
        headers.append(f'Referer: {referer}')
    
    cmd = ['curl', '-s', '-L', '--max-time', '15'] + \
          [h for h in headers] + [url]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def clean_text(text):
    """清理文字：移除多餘空白、HTML entities"""
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_article_links(html):
    """
    從 node 頁面提取所有 (href, title) 組合
    HTML 格式: <a href=content_XXXX.htm>...<div...id=mpXXXX>標題</div>
    """
    # 匹配 href=content_XXXX.htm 並捕獲標題
    pattern = r'href=(content_\d+\.htm)[^>]*>(?:<[^>]+>)*([^<]+)'
    matches = re.findall(pattern, html)
    return [(href, clean_text(title)) for href, title in matches if title.strip()]


def extract_nav_links(html):
    """從 node 頁面提取上一版/下一版連結"""
    prev_links = []
    next_links = []
    
    for match in re.finditer(r'<a[^>]*class=preart[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
        href = match.group(1)
        content = match.group(2)
        text = re.sub(r'<[^>]+>', '', content).replace('&nbsp;', '').strip()
        if '上一版' in text or '上頁' in text:
            prev_links.append(href)
        if '下一版' in text or '下頁' in text:
            next_links.append(href)
    
    return prev_links, next_links


def extract_article_body(html_content):
    """
    從新聞內文頁 HTML 中提取完整正文
    HTML 格式：正文在 <founder-content>...</founder-content> 標籤內
    """
    if not html_content:
        return ""

    # 找 <founder-content>...</founder-content>
    match = re.search(r'<founder-content>(.*?)</founder-content>', html_content, re.DOTALL)
    if not match:
        return ""

    content = match.group(1)

    # 換行符處理
    text = re.sub(r'</?P[^>]*>', '\n', content)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    text = re.sub(r'\s+', ' ', text)

    # 分行並清理
    lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 10]

    # 移除導航/頁腳行（只移除包含完整頁腳關鍵詞的行）
    lines = [l for l in lines if
        '上一篇' not in l and '下一篇' not in l and
        '本版標題' not in l and '澳门日报' not in l]

    return '\n'.join(lines)


def extract_summary(body_text, char_limit=40):
    """
    從完整正文生成 30-40 字中文摘要
    """
def extract_summary(body_text, char_limit=40):
    """
    從完整正文取前 char_limit 字作為摘要
    （最終由 AI cronjob 再次總結，無需完美）
    """
    if not body_text:
        return ""
    # 返回完整正文，由 AI cronjob 再次總結
    return body_text[:2000].strip()


async def scrape_macau_news(browser):
    """
    澳門日報新聞爬蟲 - 兩層次抓取：
    1. 從首頁進入，按「下一版」順序收集頭 3 個 node 頁面
    2. 進入每則 content_XXXX.htm（新聞內文頁）抓取 30 字摘要
    """
    print("[+] 正在抓取澳門日報新聞...")
    
    # 動態取得今天日期
    today = date.today()
    year = today.year
    month = f"{today.month:02d}"
    day = f"{today.day:02d}"
    date_str = f"{year}-{month}-{day}"
    base_url = "https://www.macaodaily.com"
    base_page_url = f"{base_url}/html/{year}-{month}/{day}"
    
    news_articles = []
    visited_article_urls = set()
    visited_nodes = set()
    
    print(f"[+] 日期：{date_str}")
    
    # Step 1: 從首頁進入，找到第一個 node
    print("[+] 正在進入首頁...")
    homepage_html = curl_get(base_url, referer=None)
    if not homepage_html:
        print("[!] 無法訪問首頁")
        return []
    
    # 從首頁找今天的 node_2 連結
    # 格式: <a href=..../node_2.htm> 之類
    first_node_match = re.search(r'href="?[^"]*node_2\.htm', homepage_html)
    if first_node_match:
        print("[+] 找到 node_2 入口")
    
    # Step 2: 從 node_2 開始，通過「下一版」順序收集頭 3 個 node
    current_node = "node_2.htm"
    max_nodes = 3  # 只收集頭 3 版
    
    page_count = 0
    
    while current_node and page_count < max_nodes:
        if current_node in visited_nodes:
            break
        visited_nodes.add(current_node)
        
        node_url = f"{base_page_url}/{current_node}"
        print(f"\n    [→] 第 {page_count + 1} 版：{current_node}")
        
        html = curl_get(node_url, referer=base_url)
        
        if not html or '404' in html[:500] or '您訪問的期刋不存在' in html[:500]:
            print(f"    [!] 頁面不存在或錯誤")
            break
        
        # 提取內容文章連結（含標題）
        article_links = extract_article_links(html)
        print(f"    [+] 找到 {len(article_links)} 則新聞")
        
        # 進入每則新聞內文頁抓取 30 字摘要
        for href, title_from_list in article_links:
            article_url = f"{base_page_url}/{href}"
            if article_url in visited_article_urls:
                continue
            visited_article_urls.add(article_url)
            
            article_html = curl_get(article_url, referer=node_url)
            if not article_html:
                continue

            # 兩步驟：先取完整正文，再生成摘要
            article_body = extract_article_body(article_html)
            article_summary = extract_summary(article_body, char_limit=40)

            if article_summary:
                article_title = title_from_list if title_from_list else href.replace('content_', '').replace('.htm', '')
                news_articles.append({
                    "title": article_title,
                    "summary": article_summary,
                    "url": article_url
                })
                print(f"        [✓] {article_title}")
        
        if page_count >= max_nodes - 1:
            break
        
        # 提取下一版連結
        _, next_links = extract_nav_links(html)
        if next_links:
            current_node = next_links[0]
        else:
            print(f"    [O] 無下一版連結")
            break
        
        page_count += 1
        time.sleep(0.3)
    
    print(f"\n[+] 共抓取 {len(news_articles)} 則新聞")
    return news_articles


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
            for i, article in enumerate(macau, 1):
                print(f"\n{i}. 【{article['title']}】")
                print(f"   {article['summary']}")
                print(f"   [原文：{article['url']}]")
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
