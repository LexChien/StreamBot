import re
import time
import subprocess
import requests
import argparse
from urllib.parse import urlparse
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

# --- 設定區 ---
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
REFERER = "https://gimy.ai/"
FFMPEG_BIN = "ffmpeg"
TIMEOUT = 30

def is_valid_m3u8(text):
    lines = text.splitlines()
    return lines and lines[0].startswith("#EXTM3U") and any(".ts" in l for l in lines)

def launch_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument(f"--user-agent={UA}")
    driver = webdriver.Chrome(options=chrome_options)
    driver.scopes = [r".*\.m3u8.*"]
    return driver

def detect_m3u8(driver, url):
    driver.get(url)
    print(f"\n⏳ 載入頁面中：{url}")
    time.sleep(3)
    print("🔍 掃描 m3u8 請求中...")
    for _ in range(TIMEOUT):
        for req in driver.requests:
            if req.response and ".m3u8" in req.url:
                return req.url, dict(req.headers)
        time.sleep(1)
    return None, None

def validate_m3u8(url):
    try:
        headers = {"User-Agent": UA, "Referer": REFERER}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return "error", f"HTTP {resp.status_code}"
        text = resp.text
        # Case 1: media playlist（可以直接下載）
        if is_valid_m3u8(text):
            return "media", text
        # Case 2: master playlist（多解析度）
        elif "#EXT-X-STREAM-INF" in text:
            lines = text.splitlines()
            stream_info = []

            for i, line in enumerate(lines):
                if line.startswith("#EXT-X-STREAM-INF"):
                    bw_match = re.search(r'BANDWIDTH=(\d+)', line)
                    res_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else None
                    if bw_match and next_line:
                        stream_info.append({
                            "bandwidth": int(bw_match.group(1)),
                            "resolution": res_match.group(1) if res_match else "N/A",
                            "raw_path": next_line,
                            "full_url": urljoin(url, next_line)
                        })
            if stream_info:
                # 🎞️ 顯示所有畫質選項
                print("🎞️ 偵測到多畫質選項：\n")
                sorted_info = sorted(stream_info, key=lambda x: -x["bandwidth"])
                for idx, stream in enumerate(sorted_info, start=1):
                    print(f"{idx}. {stream['bandwidth'] // 1000} kbps | {stream['resolution']} → {stream['raw_path']}")

                # 🔀 選最高畫質（最大 bandwidth）
                best_stream = sorted_info[0]
                print(f"\n🔀 自動選擇最高畫質：{best_stream['full_url']}")
                return validate_m3u8(best_stream["full_url"])

            return "master", text
        # Case 3: 非法 m3u8
        else:
            return "invalid", text
    except Exception as e:
        return "error", str(e)

def download_with_ffmpeg(url, output):
    print(f"⏬ 開始下載：{output}")
    log_path = Path(str(output)).with_suffix(".log")
    cmd = [
        FFMPEG_BIN,
        "-user_agent", UA,
        "-referer", REFERER,
        "-http_persistent", "false",
        "-timeout", "10000000",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-err_detect", "ignore_err",
        "-i", url,
        "-c", "copy",
        str(output)
    ]
    print("執行指令：", " ".join(cmd))
    with open(log_path, "w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True
        )

        for line in iter(process.stdout.readline, ''):
            print(line, end='')          # 即時顯示在畫面上
            log_file.write(line)         # 同時寫入 log 檔
        process.stdout.close()
        returncode = process.wait()

        if returncode == 0:
            print(f"\n✅ ffmpeg 下載成功，log 已儲存：{log_path}\n")
        else:
            print(f"\n❌ ffmpeg 下載失敗，請查看 log：{log_path}\n")

def process_video_url(driver, video_url):
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

def threaded_process(video_url):
    driver = launch_browser()
    try:
        process_video_url(driver, video_url)
    finally:
        driver.quit()

def main():
    parser = argparse.ArgumentParser(description="Gimy 影片自動下載工具")
    parser.add_argument('--file', '-f', help='包含影片網址的文字檔，每行一個 URL')
    parser.add_argument('--thread', '-t', type=int, default=1, help='使用的下載執行緒數，預設為 1')
    args = parser.parse_args()

    # 限制最小為 1
    if args.thread < 1:
        print("❌ --thread 參數必須為 ≥ 1")
        return

    # 單一輸入模式
    if not args.file:
        video_url = input("請輸入 Gimy 影片網址：\n> ").strip()
        driver = launch_browser()
        try:
            process_video_url(driver, video_url)
        finally:
            driver.quit()
        return

    # 批次處理模式
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ 找不到指定檔案：{args.file}")
        return

    urls = [line.strip() for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"📄 讀取網址數量：{len(urls)}，執行緒數：{args.thread}")

    # 使用 ThreadPoolExecutor 處理多線程
    with ThreadPoolExecutor(max_workers=args.thread) as executor:
        futures = [executor.submit(threaded_process, url) for url in urls]
        for future in as_completed(futures):
            future.result()  # 可加入 try/except 紀錄錯誤

if __name__ == "__main__":
    main()