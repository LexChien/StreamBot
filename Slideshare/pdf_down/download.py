import re
import io
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image

from .sniffer import fetch_html, extract_slideshare_images_from_html
from .config import PDF_DIR, LOG_DIR


def extract_id_from_url(url: str) -> str:
    """
    取 URL 最後一段，只保留數字；抓不到則回 'slideshare'
    例如 https://.../080-120640059 -> 080120640059
    """
    path = urlparse(url).path.strip("/")
    slug = path.split("/")[-1] if path else ""
    digits_only = re.sub(r"\D", "", slug)
    return digits_only if digits_only else "slideshare"

def _open_logger(stem: str):
    """回傳 (log_path, tee_func)；tee 會同時印到終端並寫入該 log 檔"""
    log_path = LOG_DIR / f"{stem}.log"
    log_file = open(log_path, "a", encoding="utf-8")

    def tee(msg: str):
        line = f"{msg}\n"
        print(msg)
        log_file.write(line)
        log_file.flush()

    def close():
        try:
            log_file.close()
        except Exception:
            pass

    return log_path, tee, close

def download_slideshare_as_pdf(url: str):
    """單一 URL 的下載流程：抓圖→合併 PDF，並寫入同名 log"""
    stem = extract_id_from_url(url)
    output_pdf = PDF_DIR / f"{stem}.pdf"
    log_path, tee, _close = _open_logger(stem)

    tee(f"===== [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 開始處理：{url}")
    tee(f"📄 輸出 PDF：{output_pdf}")
    tee(f"🧾 Log 檔案：{log_path}")

    try:
        html = fetch_html(url)
    except Exception as e:
        tee(f"❌ 瀏覽器載入失敗：{e}")
        _close()
        return

    image_urls = extract_slideshare_images_from_html(html)
    if not image_urls:
        tee("❌ 沒有抓到任何圖片。")
        _close()
        return

    tee(f"✅ 偵測到 {len(image_urls)} 張圖片，開始下載...")

    pil_images = []
    for idx, img_url in enumerate(image_urls, start=1):
        tee(f"⬇ 下載第 {idx} 張: {img_url}")
        ok = False
        for attempt in range(3):
            try:
                resp = requests.get(img_url, timeout=10)
                resp.raise_for_status()
                image = Image.open(io.BytesIO(resp.content)).convert("RGB")
                pil_images.append(image)
                ok = True
                break
            except Exception as e:
                tee(f"⚠ 下載失敗，重試中 ({attempt+1}/3)... 錯誤：{e}")
                time.sleep(1)
        if not ok:
            tee("❌ 圖片下載多次失敗，略過該張。")

    if not pil_images:
        tee("❌ 所有圖片都下載失敗，PDF 未建立。")
        _close()
        return

    try:
        tee(f"📄 合併為 PDF：{output_pdf.name}")
        if len(pil_images) == 1:
            pil_images[0].save(output_pdf)
        else:
            pil_images[0].save(output_pdf, save_all=True, append_images=pil_images[1:])
        tee(f"🎉 完成：{output_pdf}")
    except Exception as e:
        tee(f"❌ PDF 保存失敗：{e}")
    finally:
        _close()