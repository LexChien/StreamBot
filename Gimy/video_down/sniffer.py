import re
import time
from urllib.parse import urlparse, parse_qs, urljoin, unquote
from .config import TIMEOUT, UA


def detect_m3u8(driver, page_url: str):
    """先用 selenium-wire 攔截，攔不到再走 HTML 後備解析。回傳 (m3u8_url, headers)。"""
    # 清掉前一頁殘留，避免誤判
    try:
        driver.requests.clear()
    except Exception:
        pass

    driver.get(page_url)
    print(f"\n⏳ 載入頁面中：{page_url}")
    time.sleep(3)
    print("🔍 掃描 m3u8 請求中...")

    # 先掃網路請求
    for _ in range(TIMEOUT):
        for req in driver.requests:
            if req.response and ".m3u8" in req.url:
                return req.url, {"Referer": page_url, "User-Agent": UA}
        time.sleep(1)

    # 攔不到就用 HTML 後備解析
    print("🧩 網路攔截無結果，啟用 HTML 後備解析…")
    html = driver.page_source

    # 1) 直接在 HTML 找完整 m3u8 URL
    m = re.search(r'(https?://[^\s\"\'<>]+\.m3u8)', html)
    if m:
        return m.group(1), {"Referer": page_url, "User-Agent": UA}

    # 2) 抓 artplayer iframe 的 url=
    ifr = re.search(r'src=[\'\"]([^\'\"]*artplayer\.html\?[^\'\"]+)[\'\"]', html, re.I)
    if ifr:
        iframe_url = urljoin(page_url, ifr.group(1))
        q = parse_qs(urlparse(iframe_url).query)
        if "url" in q and q["url"]:
            return unquote(q["url"][0]), {"Referer": page_url, "User-Agent": UA}

    # 3) 其他 data-* 場景
    m = re.search(r'data-(?:url|src)=[\'\"]([^\'\"]+\.m3u8)[\'\"]', html, re.I)
    if m:
        return urljoin(page_url, m.group(1)), {"Referer": page_url, "User-Agent": UA}

    return None, None