---
name: bilibili-obsidian-learning
description: 哔哩哔哩/B 站视频学习工作流。Use when the user provides a Bilibili/B站 video link and wants Codex to download video/audio, extract subtitles or transcribe audio, select high-quality keyframes, summarize the course structure, and archive a three-part Obsidian learning note by domain. Also use when fixing B站视频笔记的关键帧质量问题，例如空白页、信息显示不全、示例页、过渡页、结束页。
---

# B 站视频转 Obsidian 学习笔记

## 目标

把一个 B 站课程视频整理成 Obsidian 学习包：

1. 开篇说明：学习大纲、学完后的预期效果、使用工具说明。
2. 课程主体：精选关键帧 + 结构化知识框架。
3. 总结与反思：关键结论、思考题、迁移应用与泛化能力延伸。

优先自动发现 Obsidian vault：

- 检查当前工作区、用户文档目录和常见磁盘中的 `.obsidian` 文件夹。
- 如果能找到多个 vault，选择最匹配用户请求的 vault；不确定时询问用户。
- 如果自动发现失败，询问用户 Obsidian 仓库路径。

优先使用 vault 里已有分类目录。AI、工具、技术类视频可默认归档到：

`课程\AI工具\<视频标题>\`

## 标准流程

1. 定位 Obsidian 仓库。
   - 优先搜索 `.obsidian` 文件夹。
   - 读取 vault 顶层目录，按视频领域选择目标文件夹。
   - 只有自动发现失败时，才向用户询问路径。

2. 抓取 B 站元数据和素材。
   - 优先使用 `scripts/bili_fetch.py`。
   - 网络请求前清理失效代理环境变量：`HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`。
   - 使用浏览器 User-Agent 和视频 Referer 调用 B 站公开接口。
   - 在本地工作目录保存 `metadata.json`、`playurl.json`、`fetch_summary.json`、封面、首帧、音频和视频。

3. 生成字幕或逐字稿。
   - 先检查 B 站字幕列表。
   - 如果有字幕，优先下载并使用字幕。
   - 如果没有字幕，用 `faster-whisper` 转写音频。
   - 中文 ASR 常有同音错字，最终主笔记必须按语境校正关键术语。
   - AI/RAG 类视频常见校正词：检索、生成、向量、Embedding、向量数据库、索引、召回、重排、cross-encoder。

4. 处理音视频。
   - 使用 `imageio-ffmpeg` 获取 ffmpeg 可执行文件。
   - 转写前把音频转为 16 kHz、单声道 WAV。
   - 最终笔记不要只依赖固定间隔抽帧。

5. 筛选关键帧。
   - 先用 `scripts/make_frame_contact_sheets.py` 每 5-15 秒生成候选帧拼图。
   - 逐张查看候选帧，选择信息完整、适合作为课件页的画面。
   - 必须剔除：
     - 空白页或大面积无信息背景；
     - 动画未完成、文字或流程图缺失的半成品页面；
     - 只有示例演示、缺少通用知识含义的页面；
     - 纯过渡页或标题页，除非它能明确承担章节分隔作用；
     - 结束页、感谢页；
     - 重要文字被裁切、字幕遮挡或显示不全的画面。
   - 优先选择：大纲页、完整流程图、对比表、步骤图、概念定义页、全链路复盘页。
   - 最终关键帧放在 `assets/selected/`，主笔记只引用精选帧。

6. 生成 Obsidian 笔记。
   - 使用三段式结构：开篇说明、课程主体、总结与反思。
   - frontmatter 至少包含：来源平台、URL、bvid、标题、作者、发布时间、学习领域、处理状态、标签。
   - 图片链接使用 Obsidian 格式：`![[assets/selected/<文件名>.jpg]]`。
   - 适合流程型课程时，加入 Mermaid 流程图。
   - 原始逐字稿放在 `transcript/`，在附录中链接。
   - 不要把大型原始视频、音频复制进 Obsidian vault，除非用户明确要求。

7. 验证输出。
   - 统计主笔记图片链接，确认全部指向 `assets/selected/`。
   - 修复关键帧后，确认没有残留 `assets/frame_...` 旧链接。
   - 至少视觉检查 3 类精选帧：第一张、一个中段流程/对比页、最后一张。
   - 确认主笔记包含：
     - `## 00. 开篇说明`
     - `## 01. 课程主体`
     - `## 02. 总结与反思`

## 脚本

优先使用本 skill 的 `scripts/` 目录：

- `bili_fetch.py`：抓取元数据、封面、首帧、音频、视频、字幕。
- `process_media.py`：音频转码并抽取基准帧。
- `transcribe_audio.py`：运行 `faster-whisper`，生成逐字稿。
- `make_frame_contact_sheets.py`：生成候选关键帧拼图，便于人工/视觉筛选。
- `fix_keyframes.py`：根据时间戳清单抽取精选帧，并更新 Obsidian 笔记图片引用。
- `create_note_from_plan.py`：根据 JSON 内容计划生成三段式 Obsidian 笔记。

依赖安装优先放在任务工作区的 `.tools/python`，或使用已有 workspace dependencies。常用依赖：

`imageio-ffmpeg`, `faster-whisper`, `Pillow`

如果 Windows 权限导致包目录或模型缓存不可读，按需请求批准修复 ACL 或用提升权限运行具体命令。不要执行宽泛的破坏性命令。

## 输出结构

Obsidian vault 内：

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

本地工作区内：

```text
bilibili_downloads/<bvid>_<视频标题>/
  metadata.json
  playurl.json
  fetch_summary.json
  video.m4s
  audio.m4s
  audio_16k.wav
  candidate_frames/
  keyframes_selected/
  transcript/
```

## 最终回复

简洁报告：

- 主 Obsidian 笔记路径；
- 精选关键帧目录；
- 逐字稿目录；
- 仍然存在的限制，例如没有 B 站字幕、ASR 可能有误差。
