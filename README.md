### 简述

该 Python 脚本可以爬取 https://toefl.kmf.com/n/toefl2026 上的音频，合并成单个 mp3 文件并嵌入 lrc 格式的字幕

截止至 2026.7.10 可以正常使用

### 准备工作

使用前需要安装依赖。

Python 依赖：

```cmd
pip install requests mutagen
```

外部依赖（ffmpeg，用于处理音频）：

```cmd
winget install Gyan.FFmpeg
```

### 使用方法

在学而思国际上做听力练习或口语练习中的复述题时，可以使用此工具爬取音频资料与听力原文。建议先自己做一遍，留有印象后再保存音频。

具体使用方法为：

1. 做题时，可以看到浏览器显示的网址形如：https://toefl.kmf.com/toefl-practice/agent/normal/178360755489676916/29/d2q9mj
2. 其中的 178360755489676916 就是本次练习的 `exam_unique`
3. 以 `python main.py 178360755489676916 -s 3` 的形式调用此脚本，就可以得到一个整合的音频文件，其中每个小音频文件连续重复播放三次（方便磨耳朵），间隔 3 秒
4. 音频文件将会自动嵌入听力原文（字幕 / 歌词），要想查看，可以使用 MusicPlayer2（Windows）或是 Musicolet（Android）
5. 特别的，如果希望看到题目的解析，请访问 https://toefl.kmf.com/toefl-practice/report/2026/<exam_unique>，例如 https://toefl.kmf.com/toefl-practice/report/2026/178360755489676916

### TODO

#### 实现全自动批改

做完的题目（口语题）似乎也可以批量获取到自己的答题语音，将其爬下来交给 Gemini 批改，后期也可以写 SKILL、调 api 等等

思路：

用户输入 `--get-prompt <Authorization>` 选项时，无视其他所有参数（如果有，给警告），仅爬取歌词和回答并整合回答音频，最后将歌词稍作处理，打印在控制台上作为提示词
