# StreamBot/main.py
import sys
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TOOLS = {
    "gimy": BASE_DIR / "Gimy" / "main.py",
    "slideshare": BASE_DIR / "Slideshare" / "main.py",
}

def main():
    if "-r" not in sys.argv and "--router" not in sys.argv:
        sys.exit(1)

    parser = argparse.ArgumentParser(description="StreamBot 總控制器", add_help=False)
    parser.add_argument(
        "-r", "--router",
        required=True,
        choices=TOOLS.keys(),
        help="選擇要使用的子專案（gimy 或 slideshare）"
    )

    # 只先解析 router，其餘參數全部原封保留
    known_args, remaining_args = parser.parse_known_args()

    tool_main = TOOLS[known_args.router]
    if not tool_main.exists():
        print(f"❌ 找不到 {known_args.router} 的 main.py")
        sys.exit(1)

    # 有些人會用 '--' 當分隔，移掉不影響
    if remaining_args and remaining_args[0] == "--":
        remaining_args = remaining_args[1:]

    # 顯示轉交訊息
    print(f"▶️ 轉交執行： {sys.executable} {tool_main} {' '.join(remaining_args)}")

    # ✨ 重點：把 cwd 設為子專案資料夾，讓相對路徑落在 Gimy/ 或 Slideshare/
    result = subprocess.run(
        [sys.executable, str(tool_main), *remaining_args],
        cwd=str(tool_main.parent),
        check=False,
    )
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()