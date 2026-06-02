# Bilibili Obsidian Learning Skill

一个面向中文 B 站学习场景的 Codex skill，用于把哔哩哔哩课程视频整理成 Obsidian 学习笔记。

它支持：

- 抓取 B 站视频元数据、封面、音频、视频和字幕；
- 无字幕时用 `faster-whisper` 生成逐字稿；
- 抽取候选关键帧，并筛选适合学习复盘的课件页；
- 生成三段式 Obsidian 笔记：开篇说明、课程主体、总结与反思；
- 按学习领域归档到 Obsidian vault；
- 修复低质量关键帧，例如空白页、信息不完整页、示例页、过渡页和结束页。

## 安装

在 Codex 中让它安装这个 skill：

```text
安装这个 skill：
https://github.com/<your-github-username>/bilibili-obsidian-learning/tree/main/skills/bilibili-obsidian-learning
```

安装后重启 Codex，让新 skill 生效。

## 使用

```text
Use $bilibili-obsidian-learning 将这个 B 站视频整理成 Obsidian 学习笔记：https://www.bilibili.com/video/...
```

或者：

```text
用 bilibili-obsidian-learning 处理这个 B 站课程视频，并导入我的 Obsidian。
```

## 输出结构

```text
课程/<领域>/<视频标题>/
  <视频标题>.md
  assets/
    selected/
      <精选关键帧>.jpg
      selected_keyframes_manifest.json
  transcript/
    transcript.txt
    transcript.srt
    transcript.json
    逐字稿-自动识别.md
```

## 依赖

Codex 会按需安装或使用这些 Python 依赖：

- `imageio-ffmpeg`
- `faster-whisper`
- `Pillow`

如果 B 站视频没有字幕，转写模型可能需要从 Hugging Face 下载。

## 注意事项

- 请仅在符合平台规则、版权要求和个人学习用途的范围内使用。
- 默认不把大型原始视频/音频复制进 Obsidian vault，避免知识库体积膨胀。
- 自动转写可能存在同音错字，最终笔记会尽量按语境校正常见技术术语。

## License

MIT
