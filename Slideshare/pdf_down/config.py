from pathlib import Path

# 錨定到「Slideshare 子專案」根目錄，不吃當前工作目錄
BASE_DIR = Path(__file__).resolve().parents[1]
PDF_DIR = BASE_DIR / "pdf"
LOG_DIR = BASE_DIR / "log"
PDF_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)