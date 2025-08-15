import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from pdf_down.download import download_slideshare_as_pdf

def main():
    parser = argparse.ArgumentParser(description="Slideshare 下載工具")
    parser.add_argument("-u", "--url", help="指定單一 Slideshare 網址下載")
    parser.add_argument("-f", "--file", help="從檔案批次讀取網址下載（每行一個 URL）")
    parser.add_argument("-t", "--thread", type=int, default=1, help="下載執行緒數（至少 1）")
    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("請使用 -u 或 -f 指定下載來源")

    urls = []
    if args.url:
        urls.append(args.url.strip())
    if args.file:
        p = Path(args.file)
        if not p.exists():
            parser.error(f"找不到檔案：{p}")
        urls.extend(u.strip() for u in p.read_text(encoding="utf-8").splitlines() if u.strip())

    threads = max(1, args.thread)
    if threads == 1:
        for u in urls:
            download_slideshare_as_pdf(u)
    else:
        with ThreadPoolExecutor(max_workers=threads) as exe:
            futs = {exe.submit(download_slideshare_as_pdf, u): u for u in urls}
            for f in as_completed(futs):
                try:
                    f.result()
                except Exception as e:
                    print(f"❌ {futs[f]} 下載失敗：{e}")

# if __name__ == "__main__":
#     main()

# ==== 主程式 ====
if __name__ == "__main__":
    url = input("請輸入 Slideshare 網址：\n> ").strip()
    if not url:
        print("❌ 未輸入網址，結束。")
    else:
        download_slideshare_as_pdf(url)