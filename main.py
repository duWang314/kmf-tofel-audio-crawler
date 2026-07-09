import sys
import os
import random
import time
import subprocess
import requests


def main():
    # 1. 处理命令行参数
    if len(sys.argv) < 2:
        print("用法: python main.py <exam_unique>")
        sys.exit(1)
    exam_unique = sys.argv[1]

    # 2. 请求数据
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
        print(f"请求失败: {e}")
        sys.exit(1)

    data = resp.json()
    questions = data.get("result", {}).get("questions", {})
    if not questions:
        print("未找到题目数据")
        sys.exit(1)

    # 3. 收集所有音频 URL
    audio_urls = []
    for qid, qdata in questions.items():
        for audio in qdata.get("audio", []):
            url_ = audio.get("url")
            if url_:
                audio_urls.append(url_)

    if not audio_urls:
        print("没有找到任何音频 URL")
        sys.exit(1)

    print(f"共找到 {len(audio_urls)} 个音频文件")

    # 4. 下载音频并重命名为 0.mp3, 1.mp3, ...
    temp_files = []
    for idx, audio_url in enumerate(audio_urls):
        filename = f"{idx}.mp3"
        print(f"下载 {filename} ...")
        try:
            r = requests.get(audio_url, stream=True, timeout=30)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            temp_files.append(filename)
            print(f"已保存 {filename}")
        except requests.RequestException as e:
            print(f"下载 {audio_url} 失败: {e}")
            sys.exit(1)

        # 随机等待 3~5 秒（最后一次不需要等待，也可以等待，按需求）
        if idx < len(audio_urls) - 1:
            wait_time = random.uniform(3, 5)
            print(f"等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)

    # 5. 生成 FFmpeg 列表文件，每个文件出现 3 次
    list_filename = "filelist.txt"
    with open(list_filename, "w", encoding="utf-8") as f:
        for idx in range(len(temp_files)):
            # 每个文件重复 3 次
            for _ in range(3):
                f.write(f"file '{idx}.mp3'\n")

    # 6. 调用 FFmpeg 合并
    output_filename = f"{exam_unique}.mp3"
    cmd = [
        "ffmpeg",
        "-f", "concat",          # 使用 concat demuxer
        "-safe", "0",
        "-i", list_filename,
        "-acodec", "libmp3lame", # 统一使用 MP3 编码器
        "-b:a", "192k",          # 固定比特率（可根据需要调整）
        "-ar", "44100",          # 统一采样率为 44100 Hz
        "-ac", "2",              # 统一为立体声（若原文件多为单声道可改为 1）
        output_filename
    ]
    print(f"正在合并为 {output_filename} ...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"合并成功: {output_filename}")
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg 执行失败: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("未找到 ffmpeg，请确保已安装并添加到系统 PATH")
        sys.exit(1)

    # 7. 清理临时文件（可选）
    for fname in temp_files:
        try:
            os.remove(fname)
        except OSError:
            pass
    try:
        os.remove(list_filename)
    except OSError:
        pass

    print("完成！")


if __name__ == "__main__":
    main()
