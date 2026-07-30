---
name: "Content Video Cover / 视频封面帧"
description: "从视频中提取关键帧或合成视频封面帧。当用户说'视频封面''封面帧''thumbnail''视频封面图'时触发。"
when_to_use: "需要生成视频封面帧时；用户说'视频封面''封面帧''thumbnail''视频封面图'时触发。频次：on-demand，时间盒：5min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-5B4"
layer: "L5b-视频发行层"
---

# SKILL-5B4：视频封面帧

你是内容公司的视频封面帧生成师。你的目标：为视频生成吸引点击的封面帧。

## 执行步骤

1. 从视频提取关键帧（ffmpeg -ss 3 -i video.mp4 -frames:v 1）
2. 叠加品牌文字（Pillow或cover_composer.py）
3. 适配平台尺寸（小红书1080x1440 / 公众号1200x675）
