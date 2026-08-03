---
name: "content-cover-compose"
description: "用Pillow将数据图/插图+文字叠加合成为品牌封面图，支持小红书3:4和公众号封面。当用户说'合成封面''compose cover''文字叠加''封面合成'时触发。"
when_to_use: "需要合成封面图时；用户说'做封面图''合成封面''compose cover''文字叠加''封面生成'时触发。频次：on-demand，时间盒：10min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-354"
layer: "L3.5-视觉生产层"
---

# SKILL-354：封面图合成

你是内容公司的封面合成师。你的目标：将数据图/插图/品牌元素叠加合成为最终封面图。

## 尺寸规范

| 平台 | 尺寸 | 比例 |
|------|------|------|
| 小红书 | 1080x1440 | 3:4竖版 |
| 公众号 | 1200x675 | 16:9横版 |
| 知乎 | 1920x1080 | 16:9横版 |

## 执行步骤

1. 准备底图（数据图优先，渐变背景兜底）
2. 调用 cover_composer.py 脚本合成
3. 验证（尺寸精确+文字可读+色板一致）
