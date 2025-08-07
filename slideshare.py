import re
import requests
import io
import time
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def extract_id_from_url(url):
    match = re.search(r'/(\d+)(?:/)?$', url)
    return match.group(1) if match else "slideshare"

def extract_slideshare_images_from_html(html):
    """
    從整個 HTML 原始碼中找出所有 slidesharecdn 的 JPG 圖片
    """
    candidates = re.findall(r'https://image\.slidesharecdn\.com/[^\s"]+?-(?:728|1024|2048)\.jpg', html)
    return sorted(set(candidates))  # 去重後排序

def download_slideshare_as_pdf(url):
    output_pdf = extract_id_from_url(url) + ".pdf"

    # 使用 headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    driver = webdriver.Chrome(options=options)

    print(f"🔍 載入頁面中: {url}")
    driver.get(url)
    time.sleep(3)
    html = driver.page_source
    driver.quit()

    image_urls = extract_slideshare_images_from_html(html)

    if not image_urls:
        print("❌ 沒有抓到任何圖片。")
        return

    print(f"✅ 偵測到 {len(image_urls)} 張圖片，開始下載...")

    pil_images = []
    for idx, img_url in enumerate(image_urls):
        print(f"⬇ 下載第 {idx+1} 張: {img_url}")
        for attempt in range(3):
            try:
                response = requests.get(img_url, timeout=10)
                image = Image.open(io.BytesIO(response.content)).convert("RGB")
                pil_images.append(image)
                break
            except Exception as e:
                print(f"⚠ 下載失敗，重試中 ({attempt+1}/3)...")
                time.sleep(1)

    if not pil_images:
        print("❌ 所有圖片都下載失敗，PDF 未建立。")
        return

    print(f"📄 合併為 PDF：{output_pdf}")
    pil_images[0].save(output_pdf, save_all=True, append_images=pil_images[1:])
    print(f"🎉 完成：{output_pdf}")

# ==== 主程式 ====
if __name__ == "__main__":
    url = input("請輸入 Slideshare 網址：\n> ").strip()
    if not url:
        print("❌ 未輸入網址，結束。")
    else:
        download_slideshare_as_pdf(url)