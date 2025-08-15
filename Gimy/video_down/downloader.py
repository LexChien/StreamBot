import subprocess
from pathlib import Path
from .config import FFMPEG_BIN, UA, REFERER

VIDEO_DIR = Path("video")
LOG_DIR = Path("log")
VIDEO_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

def download_with_ffmpeg(m3u8_url: str, output):
    # output = Path(str(output))
    # log_path = output.with_suffix(".log")
    output = VIDEO_DIR / output
    log_path = LOG_DIR / Path(output.stem + ".log")

    cmd = [
        FFMPEG_BIN,
        "-user_agent", UA,
        "-referer", REFERER,
        "-http_persistent", "false",
        "-timeout", "10000000",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "5",
        "-err_detect", "ignore_err",
        "-i", m3u8_url,
        "-c", "copy",
        str(output)
    ]

    print(f"⏬ 開始下載：{output.name}")
    print("執行指令：", " ".join(cmd))

    with open(log_path, "w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )
        for line in iter(proc.stdout.readline, ''):
            print(line, end='')
            log_file.write(line)
        proc.stdout.close()
        code = proc.wait()
        if code == 0:
            print(f"\n✅ ffmpeg 下載成功，log 已儲存：{log_path}\n")
        else:
            print(f"\n❌ ffmpeg 下載失敗，請查看 log：{log_path}\n")