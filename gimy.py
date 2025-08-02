
import re
import time
import subprocess
import requests
from urllib.parse import urlparse
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path

# --- 設定區 ---
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
REFERER = "https://gimy.ai/"
FFMPEG_BIN = "ffmpeg"  # 確保已加入環境變數或使用完整路徑
TIMEOUT = 30

# --- 判斷是否為 media playlist ---
def is_valid_m3u8(text):
    lines = text.splitlines()
    return lines and lines[0].startswith("#EXTM3U") and any(".ts" in l for l in lines)

# --- 啟動瀏覽器 ---
def launch_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--user-agent={UA}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.scopes = [r".*\.m3u8.*"]
    return driver

# --- 偵測 m3u8 串流 ---
def detect_m3u8(driver, url):
    driver.get(url)
    print("⏳ 載入頁面中...")
    time.sleep(3)

    print("🔍 掃描 m3u8 請求中...")
    for _ in range(TIMEOUT):
        for req in driver.requests:
            if req.response and ".m3u8" in req.url:
                return req.url, dict(req.headers)
        time.sleep(1)
    return None, None

# --- 嘗試抓取內容並驗證格式 ---
def validate_m3u8(url):
    try:
        headers = {"User-Agent": UA, "Referer": REFERER}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            if is_valid_m3u8(resp.text):
                return "media", resp.text
            elif "#EXT-X-STREAM-INF" in resp.text:
                return "master", resp.text
            else:
                return "invalid", resp.text
        else:
            return "error", f"HTTP {resp.status_code}"
    except Exception as e:
        return "error", str(e)

# --- 啟動 ffmpeg 下載 ---
def download_with_ffmpeg(url, output):
    print(f"⏬ 開始下載: {output}")
    cmd = [
        FFMPEG_BIN,
        "-user_agent", UA,
        "-referer", REFERER,
        "-http_persistent", "false",
        "-i", url,
        "-c", "copy",
        output
    ]
    try:
        subprocess.run(cmd, check=True)
        print("✅ ffmpeg 下載成功")
    except subprocess.CalledProcessError as e:
        print("❌ ffmpeg 下載失敗:", e)

# --- 主程序 ---
def main():
    video_url = input("請輸入 Gimy 影片網址：\n> ").strip()
    driver = launch_browser()
    try:
        m3u8_url, headers = detect_m3u8(driver, video_url)
        if not m3u8_url:
            print("❌ 找不到 m3u8 請求")
            return
        
        if "artplayer.html?url=" in m3u8_url:
            match = re.search(r"url=(https[^&]+)", m3u8_url)
            if match:
                real_m3u8 = match.group(1)
                print(f"🧠 偵測到 artplayer iframe 包裝，實際串流為：{real_m3u8}")
                m3u8_url = real_m3u8

        print(f"✅ 偵測到 m3u8：{m3u8_url}")
        status, content = validate_m3u8(m3u8_url)

        if status == "media":
            print("✅ 無加密，可直接使用 ffmpeg")
            outname = Path(urlparse(video_url).path).name + ".mp4"
            download_with_ffmpeg(m3u8_url, outname)
        elif status == "master":
            print("❌ 不是 media playlist（可能為 master）")
        elif status == "invalid":
            print("❌ 這不是有效的 media playlist 或已加密")
        else:
            print("❌ 無法載入 m3u8:", content)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
