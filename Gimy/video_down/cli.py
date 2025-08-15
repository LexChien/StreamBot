import re
from urllib.parse import urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from .browser import launch_browser, close_browser
from .sniffer import detect_m3u8
from .m3u8_parser import validate_m3u8
from .downloader import download_with_ffmpeg


def _process_one(driver, page_url: str):
    m3u8_url, _ = detect_m3u8(driver, page_url)
    if not m3u8_url:
        print("❌ 找不到 m3u8 請求")
        return

    print(f"✅ 偵測到 m3u8：{m3u8_url}")
    status, _text, final_media_url = validate_m3u8(m3u8_url, show_list=True)

    if status == "media" and final_media_url:
        print("✅ 無加密，可直接使用 ffmpeg")
        outname = Path(urlparse(page_url).path).name + ".mp4"
        download_with_ffmpeg(final_media_url, outname)
    elif status == "master":
        print("❌ 不是 media playlist（可能為 master）")
    elif status == "invalid":
        print("❌ 這不是有效的 media playlist 或已加密")
    else:
        print("❌ 無法載入 m3u8:", _text)


def run(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Gimy 影片自動下載工具（模組化等效版）")
    parser.add_argument('--file', '-f', help='包含影片網址的文字檔，每行一個 URL')
    parser.add_argument('--url',  '-u', help='單一影片網址')
    parser.add_argument('--thread', '-t', type=int, default=1, help='下載執行緒數（>=1）')
    args = parser.parse_args(argv)

    if args.thread < 1:
        print("❌ --thread 參數必須為 ≥ 1")
        return 1

    # --url：單一網址模式
    if args.url:
        driver = launch_browser()
        try:
            _process_one(driver, args.url.strip())
        finally:
            close_browser(driver)
        return 0

    # --file：批次模式
    if args.file:
        p = Path(args.file)
        if not p.exists():
            print(f"❌ 找不到指定檔案：{args.file}")
            return 1
        urls = [line.strip() for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
        print(f"📄 讀取網址數量：{len(urls)}，執行緒數：{args.thread}")

        if args.thread == 1:
            driver = launch_browser()
            try:
                for u in urls:
                    _process_one(driver, u)
            finally:
                close_browser(driver)
        else:
            def worker(u):
                d = launch_browser()
                try:
                    _process_one(d, u)
                finally:
                    close_browser(d)
            with ThreadPoolExecutor(max_workers=args.thread) as exe:
                futs = [exe.submit(worker, u) for u in urls]
                for f in as_completed(futs):
                    f.result()
        return 0

    # 互動模式（備用）
    try:
        page_url = input("請輸入 Gimy 影片網址：\n> ").strip()
    except (EOFError, KeyboardInterrupt):
        return 1

    driver = launch_browser()
    try:
        _process_one(driver, page_url)
    finally:
        close_browser(driver)
    return 0