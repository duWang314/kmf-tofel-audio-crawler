import sys
import os
import random
import time
import subprocess
import argparse
import requests
import re

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, USLT
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


def get_args_parser():
    parser = argparse.ArgumentParser(description="下载托福音频并合并，支持插入静音与生成对照字幕")
    parser.add_argument("exam_unique", help="考试（每次练习）唯一标识")
    parser.add_argument("-s", "--silence", type=float, default=0.0,
                        help="每个音频之间插入的静音秒数，仅接受 0 ~ 20，支持小数（默认 0）")
    parser.add_argument("-r", "--repeat", type=int, default=3,
                        help="每个音频重复次数，仅接受 1 ~ 10（默认 3）")
    parser.add_argument("-k", "--keep", action="store_true", help="保留过程文件")
    return parser


def download_audio(url, filename):
    """下载单个音频文件"""
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"[ERROR] 下载 {url} 失败: {e}")
        return False


def get_audio_duration(file_path):
    """使用 ffprobe 获取音频文件的精确时长（秒）"""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stdout.strip()
        if "duration=" in output:
            output = output.split("=")[1]
        return float(output)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
        # 降级处理：若获取失败则默认返回一个预估时间（避免程序崩溃）
        print(f"[WARNING] ffprobe 获取精确时长失败（{e}），将返回一个预设时间：3 秒")
        return 3.0


def format_lrc_time(seconds):
    """将秒数格式化为 LRC 歌词时间戳 [mm:ss.xx]"""
    minutes = int(seconds // 60)
    seconds_part = seconds % 60
    centiseconds = int((seconds_part * 100) % 100)
    return f"[{minutes:02d}:{int(seconds_part):02d}.{centiseconds:02d}]"


def clean_html(raw_html):
    """去除听力原文中可能存在的 HTML 标签"""
    if not raw_html:
        return ""
    clean_re = re.compile('<[^>]+>')
    return re.sub(clean_re, '', raw_html).strip()


def generate_silence_mp3(duration_sec, output_file="silence.mp3"):
    """使用 FFmpeg 生成指定时长的静音 MP3 文件"""
    if duration_sec <= 0:
        return None
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(duration_sec),
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-y",
        output_file
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 生成静音文件失败: {e.stderr}")
        return None
    except FileNotFoundError:
        print("[ERROR] 未找到 ffmpeg，请确保已安装并添加到系统 PATH")
        return None


def embed_lyrics_to_mp3(mp3_file, lrc_content):
    """使用 mutagen 将 LRC 歌词写入 MP3 的 USLT (Unsynchronized lyrics) 帧"""
    if not MUTAGEN_AVAILABLE:
        print("\n[NOTICE] 未安装 mutagen 库，歌词未直接嵌入 MP3 文件中。")
        print("[NOTICE] 你可以运行 'pip install mutagen' 安装该库以启用内置歌词功能。")
        return
    
    try:
        audio = MP3(mp3_file)
        if audio.tags is None:
            audio.add_tags()
        # 将 LRC 文本作为歌词帧写入
        audio.tags.add(USLT(encoding=3, lang='eng', desc='Lyrics', text=lrc_content))
        audio.save()
        print("[INFO] 已成功将歌词嵌入 MP3 文件的元数据中。")
    except Exception as e:
        print(f"[INFO] 嵌入歌词至 MP3 失败: {e}")


def main():
    parser = get_args_parser()
    args = parser.parse_args()

    exam_unique = args.exam_unique

    silence_sec = args.silence
    if silence_sec < 0 or silence_sec > 20:
        silence_sec = parser.get_default("silence")
        print(f"[WARNING] 音频间隔超出范围，将选用默认：{silence_sec} 秒")

    repeat_times = args.repeat
    if repeat_times < 1 or repeat_times > 10:
        repeat_times = parser.get_default("repeat")
        print(f"[WARNING] 重复次数超出范围，将选用默认：{repeat_times} 次")

    keep_flag = args.keep

    print(f"[INFO] 参数已确认，题目标识为 {exam_unique}，每个音频重复 {repeat_times} 次，间隔 {silence_sec} 秒，保存过程文件：{keep_flag}")

    # 1. 请求数据
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Authorization": "Bearer tal173REGnYH8xzOOFrhGEzVG5ZWxFG-bJi2UZ_A-qaXAVkU-OwgndBoiWUkQI5vBJOYzXBZyUjm8RH5TftuZBKNHtCnJv0E7sMhokeP9OKjnyhh46oQS-giN8nmq0ccuwQLFdmhzX8Dj6r51DNb9bbRqQ1M-5BbiaS_XHVmFD6pj6oSseo1WAlR9IZKlIZGmRgnWcOCQ-4Z14cmm04dZyJsJJjQA8",
        "Connection": "keep-alive",
        "K-Product-Line": "toefl-web",
        "Origin": "https://toefl.kmf.com",
        "Referer": "https://toefl.kmf.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
        "k-platform": "web",
        "sec-ch-ua": "\"Not;A=Brand\";v=\"8\", \"Chromium\";v=\"150\", \"Microsoft Edge\";v=\"150\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }
    url = "https://api.kmf.com/toefl-app/practice/report"
    params = {"exam_unique": exam_unique}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[ERROR] 请求失败: {e}")
        sys.exit(1)

    data = resp.json()
    questions = data.get("result", {}).get("questions", {})
    if not questions:
        print("[ERROR] 未找到题目数据")
        sys.exit(1)

    # 2. 收集音频 URL 和听力原文
    audio_urls = []
    audioscripts = []
    
    # 按照题目顺序提取音频和文本
    for qid, qdata in questions.items():
        # 收集音频
        for audio in qdata.get("audio", []):
            url_ = audio.get("url")
            if url_:
                audio_urls.append(url_)
        
        # 收集文本（进行 HTML 清洗）
        html_content = qdata.get("question", {}).get("html_content")
        if html_content:
            audioscripts.append(clean_html(html_content))

    if not audio_urls:
        print("[ERROR] 没有找到任何音频 URL")
        sys.exit(1)

    print(f"[INFO] 共找到 {len(audio_urls)} 个音频文件")

    # 3. 下载音频，命名为 0.mp3, 1.mp3, ...
    temp_files = []
    for idx, audio_url in enumerate(audio_urls):
        filename = f"{idx}.mp3"
        print(f"[INFO] 下载 {filename} ...")
        if not download_audio(audio_url, filename):
            sys.exit(1)
        temp_files.append(filename)
        print(f"[INFO] 已保存 {filename}")

        # 随机等待 3~5 秒（最后一次无需等待）
        if idx < len(audio_urls) - 1:
            wait_time = random.uniform(3, 5)
            print(f"[INFO] 等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)

    # 4. 若需要静音，生成静音文件
    silence_file = None
    if silence_sec > 0:
        silence_file = "silence.mp3"
        print(f"[INFO] 生成 {silence_sec} 秒静音文件...")
        if not generate_silence_mp3(silence_sec, silence_file):
            sys.exit(1)

    # 5. 精确计算时间线并生成 LRC 歌词内容
    print("[INFO] 正在计算音频时间线并生成歌词...")
    lrc_lines = []
    current_time = 0.0

    for idx, temp_file in enumerate(temp_files):
        # 获取当前音频的精确时长
        dur = get_audio_duration(temp_file)
        script = audioscripts[idx] if idx < len(audioscripts) else ""

        # 重复 repeat_times 次（与合并音频的逻辑对齐）
        for repeat_idx in range(repeat_times):
            # 记录当前段落开始的时间戳并关联文本
            start_stamp = format_lrc_time(current_time)
            lrc_lines.append(f"{start_stamp}{script} (Rep {repeat_idx + 1}/{repeat_times})")
            
            # 累加音频时长
            current_time += dur

            # 如果设置了静音秒数，则在静音期间插入一条空提示，防止上一句歌词一直停留在屏幕上
            if silence_sec > 0:
                silence_stamp = format_lrc_time(current_time)
                lrc_lines.append(f"{silence_stamp}[Silence Interval]")
                current_time += silence_sec

    lrc_content = "\n".join(lrc_lines)

    # 6. 生成 FFmpeg 合并列表文件
    list_filename = "filelist.txt"
    with open(list_filename, "w", encoding="utf-8") as f:
        for i in range(len(temp_files)):
            for _ in range(repeat_times):
                f.write(f"file '{i}.mp3'\n")
                if silence_file:
                    f.write(f"file '{silence_file}'\n")

    # 7. 调用 FFmpeg 合并音频
    output_filename = f"{exam_unique}.mp3"
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", list_filename,
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        "-ar", "44100",
        "-ac", "2",
        "-y",
        output_filename
    ]
    print(f"[INFO] 正在合并为 {output_filename} ...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"[INFO] 合并成功: {output_filename}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] FFmpeg 执行失败: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("[ERROR] 未找到 ffmpeg，请确保已安装并添加到系统 PATH")
        sys.exit(1)

    # 8. 保存外部 LRC 文件并嵌入 MP3 元数据中
    lrc_filename = f"{exam_unique}.lrc"
    with open(lrc_filename, "w", encoding="utf-8") as lf:
        lf.write(lrc_content)
    print(f"[INFO] 已生成外部字幕文件: {lrc_filename}")

    # 尝试将歌词写入 MP3 内部
    embed_lyrics_to_mp3(output_filename, lrc_content)

    # 9. 清理临时文件
    if not keep_flag:
        print("[INFO] 正在清除过程文件(使用 -k 或 --keep 选项以保留)...")
        for fname in temp_files:
            try:
                os.remove(fname)
            except OSError:
                pass
        if silence_file and os.path.exists(silence_file):
            try:
                os.remove(silence_file)
            except OSError:
                pass
        try:
            os.remove(list_filename)
        except OSError:
            pass
        try:
            os.remove(lrc_filename)
        except OSError:
            pass

    print("[INFO] 完成！")


if __name__ == "__main__":
    main()
