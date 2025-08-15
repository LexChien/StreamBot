# StreamBot

## 介紹

`Gimy` 是一個自動化工具，專為 Gimy 影片網站設計，能夠自動偵測影片頁面中的 m3u8 串流地址，並利用 ffmpeg 下載無加密的影片檔案。此腳本結合 Selenium Wire、requests 及 ffmpeg，適合需要批量下載或分析 Gimy 串流的開發者與研究者。

`Slideshare` 下載 slideshare 簡報，抓取 2048 高畫質圖片，傳存成 PDF 檔案



---

## 功能特色

- 模組化與封裝
- 自動啟動 Chrome headless 瀏覽器，攔截 m3u8 串流請求
- 支援 artplayer iframe 包裝的串流自動解析
- 檢查 m3u8 是否為 media playlist，並判斷是否可直接下載
- 下載無加密 m3u8 串流為 mp4 檔案（需安裝 ffmpeg）
- 友善命令列互動，下載進度與錯誤提示
- 顯示所有可選畫質
- 錯誤重試
- 日誌記錄
- Master Playlist 指向多種解析度
- Media Playlist 真正列出 .ts 檔案

---

## 參數
- `--router` `-r` 指定要執行的專案
- `--file` `-f` 讀取檔案，批次下載影片
- `--thread` `-t` 多線程參數，最低為 1 ，建議範圍 1~10
- `--url` `-u` 指定單一網址下載

```bash
# Gimy 單一網址
python3 main.py -r gimy -u https://gimy.ai/eps/158013-1-11.html

# Gimy 批次 + 多執行緒
python3 main.py -r gimy -f url.txt -t 2

# Slideshare 單一網址
python3 main.py -r slideshare -u https://www.slideshare.net/slideshow/aaa/36495046

# Slideshare 批次 + 多執行緒
python3 main.py -r slideshare -f url.txt -t 2
```

---

```bash
StreamBot
 |
 |_   Gimy
 |        |_   video_down/ 
 |        |        |_   __init__.py
 |        |        |_   cli.py
 |        |        |_   downloader.py
 |        |        |_   m3u8_parser.py
 |        |        |_   browser.py
 |        |_   video/ 
 |        |_   log/ 
 |        |_   main.py
 |
 |_   Slideshare
 |        |_   pdf_down/
 |        |        |_   __init__.py
 |        |        |_   config.py
 |        |        |_   download.py
 |        |        |_   sniffer.py
 |        |_   pdf/
 |        |_   log/  
 |        |_   main.py
 |
 |_   main.py
```

---

## 環境需求

- Python 3.7+
- [selenium-wire](https://github.com/wkeeling/selenium-wire)
- [selenium](https://pypi.org/project/selenium/)
- [requests](https://pypi.org/project/requests/)
- Chrome 瀏覽器及對應 [ChromeDriver](https://chromedriver.chromium.org/)
- ffmpeg（需加入環境變數）

安裝依賴：

```bash
pip install selenium-wire selenium requests
```

## 使用方法

- 安裝 Chrome 及 ChromeDriver，並將 ffmpeg 加入環境變數。
- 執行腳本：

## 注意事項
- 僅支援無加密的 m3u8 串流，若遇到 master playlist 或加密內容將提示無法下載。
- 請勿用於非法用途，僅供學術研究與技術交流。
- 若遇到瀏覽器啟動或 ffmpeg 下載失敗，請檢查環境配置。