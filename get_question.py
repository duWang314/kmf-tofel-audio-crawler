import requests
import json
import argparse


parser = argparse.ArgumentParser(description="测试程序")
parser.add_argument("exam_unique", help="考试唯一标识")
args = parser.parse_args()

exam_unique = args.exam_unique

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

exam_unique = args.exam_unique
params = {"exam_unique": exam_unique}

try:
    resp = requests.get(url, headers=headers, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
except requests.RequestException as e:
    print(f"请求失败: {e}")
    sys.exit(1)

# 收集听力原文
questions = data.get("result", {}).get("questions", {})
audioscripts = []
for qid, qdata in questions.items():
    audioscript = qdata.get("question").get("html_content")
    if audioscript:
        audioscripts.append(audioscript)

# 清洗 html 标记

# 导出 txt 文件
txt_lines = []
script_count = len(audioscripts)

for i in range(script_count):
    script = audioscripts[i]
    txt_lines.append(script)

txt_content = "\n\n".join(txt_lines)

txt_filename = f"{exam_unique}.txt"
with open(txt_filename, "w", encoding="utf-8") as f:
    f.write(txt_content)
print(f"[INFO] 已生成题目文件: {txt_filename}")
