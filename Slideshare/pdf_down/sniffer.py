import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def fetch_html(url: str) -> str:
    """用 headless Chrome 載入頁面並回傳 HTML"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        print(f"🔍 載入頁面中: {url}")
        driver.get(url)
        time.sleep(3)
        return driver.page_source
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

def extract_slideshare_images_from_html(html: str):
    """
    從 HTML 找出 slidesharecdn 的 JPG 圖片清單（去重＋排序）
    例：...-1-2048.jpg, ...-2-2048.jpg
    """
    candidates = re.findall(
        r'https://image\.slidesharecdn\.com/[^\s"\'<>]+?-(?:728|1024|2048)\.jpg',
        html
    )
    urls = sorted(set(candidates), key=_natural_key)
    return urls

def _natural_key(s: str):
    """根據頁碼做自然排序（盡量從檔名抓到最後的數字）"""
    m = re.search(r'-(\d+)-(?:728|1024|2048)\.jpg$', s)
    if m:
        try:
            return (0, int(m.group(1)))
        except Exception:
            pass
    return (1, s)