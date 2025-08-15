from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from .config import UA


def launch_browser():
    """啟動 headless Chrome，先設 scopes 再開網頁。"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--user-agent={UA}")
    driver = webdriver.Chrome(options=chrome_options)
    # 先設好截取範圍，避免 get 之後才設而 miss
    driver.scopes = [r".*\\.m3u8.*"]
    return driver


def close_browser(driver):
    try:
        driver.quit()
    except Exception:
        pass