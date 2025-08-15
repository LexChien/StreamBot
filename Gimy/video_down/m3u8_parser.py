import re
import requests
from urllib.parse import urljoin
from .config import UA, REFERER


def is_valid_m3u8(text: str) -> bool:
    lines = text.splitlines()
    return bool(lines and lines[0].startswith("#EXTM3U") and any(".ts" in l for l in lines))


def _fetch(url: str):
    headers = {"User-Agent": UA, "Referer": REFERER}
    resp = requests.get(url, headers=headers, timeout=10)
    return resp.status_code, resp.text


def validate_m3u8(url: str, *, show_list=True):
    """回傳 (status, text, final_media_url)。"""
    code, text = _fetch(url)
    if code != 200:
        return "error", f"HTTP {code}", None

    if is_valid_m3u8(text):
        return "media", text, url

    if "#EXT-X-STREAM-INF" in text:
        lines = text.splitlines()
        streams = []
        for i, line in enumerate(lines):
            if line.startswith("#EXT-X-STREAM-INF"):
                bw = _search_int(line, r"BANDWIDTH=(\d+)")
                res = _search_str(line, r"RESOLUTION=(\d+x\d+)") or "N/A"
                nxt = lines[i + 1].strip() if i + 1 < len(lines) else None
                if bw and nxt:
                    streams.append({
                        "bandwidth": bw,
                        "resolution": res,
                        "raw_path": nxt,
                        "full_url": urljoin(url, nxt),
                    })

        if streams:
            if show_list:
                print("🎞️ 偵測到多畫質選項：\n")
                for idx, s in enumerate(sorted(streams, key=lambda x: -x["bandwidth"]), start=1):
                    print(f"{idx}. {s['bandwidth']//1000:>4} kbps | {s['resolution']:<9} → {s['raw_path']}")
            best = max(streams, key=lambda x: x["bandwidth"])  # 最大 bandwidth
            print(f"\n🔀 自動選擇最高畫質：{best['full_url']}")
            return validate_m3u8(best["full_url"], show_list=show_list)

        return "master", text, None

    return "invalid", text, None


def _search_int(s: str, pat: str):
    m = re.search(pat, s)
    return int(m.group(1)) if m else None


def _search_str(s: str, pat: str):
    m = re.search(pat, s)
    return m.group(1) if m else None