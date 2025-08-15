import re
from urllib.parse import urlparse
from pathlib import Path
from .m3u8_parser import validate_m3u8
from .downloader import download_with_ffmpeg
from .sniffer import detect_m3u8


def process_video_url(driver, page_url: str):
    # 第一步：抓 m3u8
    m3u8_url, _ = detect_m3u8(driver, page_url)
    if not m3u8_url:
        print("❌ 找不到 m3u8 請求")
        return

    # 特殊包裝（artplayer iframe）
    if "artplayer.html?url=" in m3u8_url:
        m = re.search(r"url=(https[^&]+)", m3u8_url)
        if m:
            real_m3u8 = m.group(1)
            print(f"🧠 偵測到 artplayer iframe 包裝，實際串流為：{real_m3u8}")
            m3u8_url = real_m3u8

    print(f"✅ 偵測到 m3u8：{m3u8_url}")

    # 第二步：驗證 m3u8，必要時遞歸挑選最高畫質
    status, content = validate_m3u8(m3u8_url, show_list=True)

    if status == "media":
        print("✅ 無加密，可直接使用 ffmpeg")
        outname = Path(urlparse(page_url).path).name + ".mp4"
        download_with_ffmpeg(m3u8_url, outname)
    elif status == "master":
        print("❌ 不是 media playlist（可能為 master）")
    elif status == "invalid":
        print("❌ 這不是有效的 media playlist 或已加密")
    else:
        print("❌ 無法載入 m3u8:", content)