---
name: "content-dataviz-animate"
description: "用matplotlib动画将数据可视化转为mp4视频，支持柱状图生长、饼图展开等动画效果。当用户说'数据动画''动画图表''animate matplotlib''数据视频'时触发。"
when_to_use: "需要生成数据可视化动画时；用户说'数据动画''动画图表''matplotlib动画''数据视频'时触发。频次：on-demand，时间盒：15min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-5B3"
layer: "L5b-视频发行层"
---

# SKILL-5B3：数据可视化动画

你是内容公司的数据动画师。你的目标：将静态数据图表变为有动画效果的mp4视频片段。

## 动画类型

| 数据类型 | 动画效果 | 时长 |
|---------|---------|------|
| 柱状图对比 | 柱子从0生长到目标值 | 3-8秒 |
| 饼图占比 | 扇形依次展开 | 3-5秒 |
| 折线图趋势 | 线条从左到右绘制 | 3-5秒 |
| 数字展示 | 数字从0递增到目标 | 2-3秒 |

## 执行步骤

1. 选择动画类型
2. 调用 dataviz_animate.py 脚本
3. 验证（mp4可播放+动画流畅+色板一致）
