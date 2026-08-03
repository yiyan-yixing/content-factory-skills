---
name: "content-video-script"
description: "将文章内容拆解为30-90秒短视频分镜脚本。当用户说'视频脚本''分镜''短视频脚本''script'时触发。"
when_to_use: "需要编写短视频脚本时；用户说'写视频脚本''分镜脚本''短视频script''做视频'时触发。频次：on-demand，时间盒：15min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "2.0.0"
skill_id: "SKILL-5B1"
layer: "L5b-视频发行层"
---

# SKILL-5B1：短视频分镜脚本（增强版）

你是内容公司的短视频编剧。你的目标：将文章精华浓缩为30-90秒可执行的分镜脚本，直接对接 `video_editor.py` 完成自动合成。

## 一、标准分镜表

### 10 字段分镜表模板

| 镜头# | 时长(s) | 画面描述 | 字幕 | 配音/音频 | 转场方式 | 镜头类型 | 运镜方式 | 素材来源 | 备注 |
|-------|---------|---------|------|----------|---------|---------|---------|---------|------|
| 1 | 3 | [画面文字描述] | [屏幕文字] | [配音文本] | fade-in | 特写 | 固定 | 文字帧/gif/图 | 钩子帧 |
| 2 | 5 | [场景动作描述] | [字幕行] | [旁白] | cut | 中景 | 推 | 图片/视频素材 | — |

### JSON 输出格式（对接 video_editor.py）

```json
{
  "title": "视频标题",
  "duration_sec": 45,
  "resolution": "1080x1920",
  "brand": {
    "bg": "#1a1a2e",
    "accent": "#e9c46a",
    "cta": "#e76f51",
    "white": "#ffffff"
  },
  "shots": [
    {
      "id": 1,
      "duration_sec": 3,
      "type": "text-hook",
      "visual": "90%的人不知道：你的数据分析白做了",
      "subtitle": "数据陷阱真相",
      "video_path": null,
      "image_path": null,
      "transition": "fade-in",
      "camera": "fixed",
      "audio": "旁白-正常语速",
      "emotion": "[疑问]"
    },
    {
      "id": 2,
      "duration_sec": 6,
      "type": "dataviz",
      "visual": "柱状图逐条生长：17个策略Sharp对比",
      "subtitle": "OOS Sharpe排名",
      "video_path": "assets/videos/T1-004/sharpe-animation.mp4",
      "image_path": null,
      "transition": "cut",
      "camera": "fixed",
      "audio": "旁白-正常语速",
      "emotion": "[强调]"
    },
    {
      "id": 3,
      "duration_sec": 5,
      "type": "image",
      "visual": "策略收益曲线对比截图",
      "subtitle": "收益差距一目了然",
      "video_path": null,
      "image_path": "assets/images/T1-004/equity-curve.png",
      "transition": "slide-left",
      "camera": "push-in",
      "audio": "旁白-稍快",
      "emotion": "[转折]"
    },
    {
      "id": 4,
      "duration_sec": 4,
      "type": "cta",
      "visual": "关注我，每周拆解一个量化策略",
      "subtitle": "一键三连",
      "video_path": null,
      "image_path": null,
      "transition": "zoom-out",
      "camera": "fixed",
      "audio": "口播-热情",
      "emotion": "[兴奋]"
    }
  ],
  "voiceover": {
    "speed": "180-220字/分钟",
    "language": "zh-CN"
  },
  "bgm": {
    "track": "upbeat-tech",
    "volume": 0.3
  }
}
```

字段说明：
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 镜头序号，从1开始 |
| duration_sec | int | 镜头时长，单位秒 |
| type | string | 镜头类型: text-hook / dataviz / image / cta |
| visual | string | 画面描述（video_editor.py 无素材时渲染为文字帧） |
| subtitle | string | 底部字幕文本（可选，cta类型默认不叠加） |
| video_path | string\|null | 视频素材路径，优先使用 |
| image_path | string\|null | 图片素材路径，次优先使用 |
| transition | string | 转场方式: fade-in / cut / slide-left / zoom-out |
| camera | string | 镜头语言: fixed / push-in / pan / track |
| audio | string | 音频说明 |
| emotion | string | 配音情感标记 |

## 二、时长规则体系

### 前 3 秒钩子帧（定生死）

前3秒决定了视频的完播率。钩子必须出现在第1个镜头。

**4 种钩子类型：**

| 类型 | 示例 | 适用场景 |
|------|------|---------|
| 痛点问题 | "你的模型训练了72小时，结果过拟合了？" | 技术教程、问题解决类 |
| 惊人数据 | "90%的量化策略在实盘第一周就死了" | 数据驱动、认知冲击 |
| 反直觉声明 | "你越优化参数，策略死得越快" | 认知刷新、观点冲突 |
| 悬念提问 | "如果我告诉你一个因子就能跑赢组合，你信吗？" | 故事叙事、揭秘类 |

**钩子帧创建规则：**
1. 开头用疑问句或数字（触发好奇心）
2. 语速比正常快10-15%（紧迫感）
3. 画面简洁，不超过7个字的关键视觉
4. 字幕用大号加粗黄色字体（`font_size: 64, color: #e9c46a`）

### 每 15 秒信息点规则

人的注意力曲线大约每15秒下降一次。必须每15秒给出一个"信息浪"重新抓住注意力。

| 时间段 | 信息密度 | 情感曲线 | 画面节奏 |
|--------|---------|---------|---------|
| 0-3s | 极高 | 钩子 | 快切/紧张 |
| 3-15s | 高 | 持续吸引 | 正常 |
| 15-30s | 中 | 建立信任 | 慢切 |
| 30-45s | 中高 | 案例/数据高潮 | 正常偏快 |
| 45-60s | 中 | 解决方案 | 慢切 |
| 60-90s | 高 | 收束+CTA | 渐快至结尾 |

### 结尾 3 秒 CTA 规则

结尾必须包含一个明确的行动号召，时长3秒。

**CTA 类型：**
| 类型 | 示例 | 使用时机 |
|------|------|---------|
| 关注引导 | "关注我，每周拆解一个策略" | 干货型内容 |
| 评论引导 | "你认为哪个因子最强？评论区告诉我" | 互动型内容 |
| 下期预告 | "下期拆解：如何用MLP构建因子" | 连载型内容 |
| 资源引导 | "完整代码在评论区置顶" | 工具型内容 |

**CTA 帧规则：**
- 画面：大号加粗文字，品牌红色 `#e76f51`
- 字幕：不叠字幕（避免干扰）
- 配乐音量提升20%
- 语速正常偏慢，有停顿

### 整体时长控制

| 平台 | 目标时长 | 最长 |
|------|---------|------|
| 小红书视频 | 30-60s | 90s |
| 抖音 | 15-60s | 120s |
| 视频号 | 30-90s | 180s |
| B站 | 60-180s | 300s |
| YouTube Shorts | 15-60s | 60s |

规则：控制在目标区间的中位数。优先做短不做长——去掉所有"有趣但没必要"的信息。

## 三、镜头语言规则

### 景别交替公式

全景/中景/特写的交替创造视觉节奏。避免连续两个同景别镜头。

**标准交替模式：**
```
特写 → 中景 → 全景 → 特写 → 中景 → ...
```

**景别定义：**

| 景别 | 画面范围 | 情感效果 | 使用时机 |
|------|---------|---------|---------|
| 特写 (Close-up) | 人脸/局部/细节 | 亲密、紧张、强调 | 钩子帧、数据关键点、情感高潮 |
| 中景 (Medium) | 半身/主体+背景 | 自然、讲述、过渡 | 旁白讲解、对话、中间段落 |
| 全景 (Wide/Long) | 全身/场景全貌 | 开阔、气势、环境 | 开场定调、数据对比、场景切换 |
| 大特写 (Extreme CU) | 眼睛/手指/极细节 | 非常紧张、悬疑 | 悬念钩子、关键结论 |

**Vlog 叙事流推荐交替：**
```
全景(开场环境) → 中景(人物出现) → 特写(情感瞬间) → 中景(叙事推进) → 全景(场景切换) → 特写(关键画面) → 中景(结尾)
```

**技术讲解推荐交替：**
```
特写(钩子/标题) → 中景(问题引入) → 全景(数据/图表演示) → 特写(关键数据点) → 中景(解决方案) → 特写(CTA/结论)
```

**产品展示推荐交替：**
```
全景(产品全貌) → 特写(产品细节/亮点) → 中景(使用场景) → 特写(效果对比) → 全景(场景收束) → 特写(CTA)
```

### 运镜方式选择规则

| 运镜 | 英文 | 效果 | 使用时机 | 实现方式 |
|------|------|------|---------|---------|
| 推 | Push-in | 聚焦、强调、紧迫 | 数据揭示、关键结论、情绪高潮 | 素材缩放动画 |
| 拉 | Pull-out | 放开、全局感、释然 | 场景定调、节奏放缓、结尾收束 | 素材反向缩放 |
| 摇 | Pan | 展示环境、建立空间感 | 全景交接、场景平移、行进感 | 横向/纵向平移动画 |
| 移 | Track | 身临其境、伴随感 | 跟随主体、展示过程、Vlog开头 | 视频素材本身的镜头 |

**运镜与情绪匹配：**
```
[兴奋] → 推 (Push-in) 快速、向前推进
[低沉] → 拉 (Pull-out) 缓慢、向后拉开
[转折] → 摇 (Pan) 平移切换到新场景
[疑问] → 固定 (Fixed) 静止、让观众聚焦文字
[强调] → 推 (Push-in) 缓慢但坚定的推进
```

### 镜头节奏规则

| 节奏类型 | 镜头平均时长 | 情感效果 | 适用段落 |
|---------|------------|---------|---------|
| 快切 (Fast cut) | 2-3s | 紧张、兴奋、急促 | 开头钩子、数据冲击、CTA前 |
| 正常 (Normal) | 4-6s | 自然、流畅、讲述 | 中间叙事、讲解分析 |
| 慢切 (Slow cut) | 6-10s | 稳重、深思、沉浸 | 情感段落、深入分析、B-roll |

**节奏变化公式：**
```
快切(钩子) → 慢切(铺垫) → 正常(主体) → 快切(高潮) → 慢切(结尾) → 快切(CTA)
```

文字帧（text-hook/cta）建议 3-5s，数据帧（dataviz）建议 6-10s，图片帧（image）建议 4-6s。

## 四、AI 视频匹配规则（Runway Gen-3/Gen-4）

### 画面描述 → AI 视频 Prompt 转换

将分镜中的 `visual` 字段转换为 AI 视频生成平台的 prompt。转换公式：

```
[镜头类型], [主体], [动作], [环境], [光线], [氛围], [风格], [画质]
```

**结构模板：**
```
{镜别} shot of {主体}, {动作描述}, {环境背景}, {光线条件} lighting, {情感氛围} atmosphere, {视觉风格} style, {画质参数}
```

**示例：**

| 画面描述字段 | AI 视频 Prompt |
|-------------|---------------|
| "缆车穿过云层" | "Wide shot of cable car ascending through white clouds, misty mountain peaks in background, golden hour lighting, cinematic atmosphere, photorealistic style, 4k" |
| "代码在终端跑动" | "Close-up shot of code scrolling on dark terminal screen, green text on black background, dramatic lighting from screen glow, tech atmosphere, cyberpunk aesthetic, 4k 60fps" |
| "柱状图逐条生长" | "Medium shot of bar chart animating bar by bar, dark blue background, yellow and red bars, data visualization style, smooth animation, 4k" |
| "人物在黄山山顶看日出" | "Medium shot of a person standing on mountain peak watching sunrise, vast sea of clouds below, warm golden light on face, epic cinematic atmosphere, photorealistic style, 4k" |
| "手指点击屏幕" | "Extreme close-up of finger tapping smartphone screen, UI interface glowing, shallow depth of field, futuristic tech vibe, 4k macro shot" |

### 静态图 → 动态视频 Prompt 规则

当只有静态图片素材时，将其"动起来"：

| 素材类型 | 动态化策略 | 推荐运镜 | 示例 Prompt |
|---------|-----------|---------|-------------|
| 截图/图表 | 缓慢推入，突出关键区域 | Push-in slow | "Slow push-in on data chart, text becoming readable, subtle particle effects, cinematic" |
| 风景照片 | 缓慢平移，制造纵深感 | Pan slow | "Slow horizontal pan across mountain landscape, mist moving, clouds drifting, cinematic 4k" |
| 人物照片 | 缩放至局部表情 | Zoom-in slow | "Slow zoom to eyes, subtle micro-movements, portrait atmosphere, shallow depth of field" |
| 产品照片 | 环绕旋转展示 | Orbit | "Slow orbit around product, rotating 360 degrees, studio lighting, product photography style" |
| 多图拼接 | Ken Burns 效果，从一张过渡到另一张 | Cross-zoom | "Ken Burns style crossfade between images, slow dramatic transitions, documentary style" |

### 复用已有素材时的 Fallback 规则

```
1. 检查 image_path 或 video_path 是否存在
2. 如果存在 → 直接复用（优先选择）
3. 如果不存在但有替代素材 → 使用替代素材 + 标注"素材替换"
4. 如果完全没有素材 → 用文字帧兜底（video_editor.py 自动渲染品牌背景+文字）
5. 如果有数据需要动画化 → 调用 dataviz_animate.py 生成动画mp4
```

**素材来源优先级：**
```
已拍摄视频素材 > 已拍摄照片 > AI生成视频(Runway) > 数据动画(dataviz_animate.py) > 品牌文字帧(兜底)
```

## 五、配音稿写作规则

### 语速控制

| 类型 | 语速 | 适用场景 |
|------|------|---------|
| 标准讲述 | 180-200 字/分钟 | 主线叙事、讲解 |
| 快速 | 200-220 字/分钟 | 钩子、CTA、急迫段落 |
| 慢速 | 160-180 字/分钟 | 情感段落、重要结论 |

**字数计算公式：**
```
总配音字数 = 语速 × 分钟数
示例：180字/分钟 × 45秒 = 180 × 0.75 = 135字
```

### 情感标记系统

在配音稿中嵌入情感标记，控制 AI 配音的情感表达和语调。

| 标记 | 含义 | 语速 | 音量 | 语调变化 |
|------|------|------|------|---------|
| `[兴奋]` | 兴奋、热情 | 快+20 | 高 | 上扬 |
| `[低沉]` | 低沉、严肃 | 慢-15 | 低 | 下降 |
| `[转折]` | 转折、对比 | 正常→快 | 正常→高 | V形变化 |
| `[疑问]` | 疑问、好奇 | 慢-10 | 正常 | 末尾上扬 |
| `[强调]` | 强调、重点 | 慢-20 | 高 | 加重 |

**使用规则：**
1. 每段配音稿至少包含 1 个情感标记
2. 不要连续使用同一个情感标记
3. `[转折]` 后必须接不同情感（如 `[转折]→[兴奋]` 或 `[转折]→[低沉]`）

### 停顿标记系统

| 标记 | 时长 | 使用时机 |
|------|------|---------|
| `|` | 短停 0.5s | 分句、列表项之间、自然呼吸 |
| `||` | 长停 1s | 段落之间、重要数据前、情感转换前 |

**示例：**
```
[疑问] 你知道吗？| 90%的量化策略都在实盘第一周失效 ||
[转折] 但今天我要告诉你一个 | 让策略存活超过一年的方法
```

### 中文配音稿 + 英文字幕双语规则

```
配音稿：中文（zh-CN）— AI 配音的主语言
字幕：英文（en）— 视频合成时渲染的底部字幕
```

**格式示例：**
```json
{
  "voiceover": {
    "language": "zh-CN",
    "speed": 180,
    "text": "[疑问] 你知道90%的量化策略为什么失败吗？|| 不是因子不够好，| 是过拟合。"
  },
  "subtitles": [
    {"shot_id": 1, "zh": "你知道90%的策略为什么失败吗？", "en": "Why do 90% of strategies fail?"},
    {"shot_id": 2, "zh": "不是因子不够好", "en": "It's not the factors"},
    {"shot_id": 3, "zh": "是过拟合", "en": "It's overfitting"}
  ]
}
```

## 六、内容类型子模板

### 6a. Vlog 叙事流模板（旅行/亲子/日常）

**结构：** 开场 → 出发 → 体验 → 收尾（5-7 个分镜段）

| 段落 | 镜号 | 时长 | 类型 | 画面描述 | 配音 | 情感 |
|------|------|------|------|---------|------|------|
| 开场钩子 | 1 | 3s | text-hook | "黄山归来不看岳，但带孩子去是另一回事" | 你知道带孩子爬黄山是什么体验吗？| [疑问] |
| 场景定调 | 2 | 5s | image | 黄山远景/缆车全景 | 我们早上4:30就起床了 | [兴奋] |
| 出发过程 | 3 | 6s | image | 高铁站/车厢/孩子看书 | 5小时高铁，| 孩子自己安排了旅程 | [低沉]→[转折] |
| 核心体验 | 4-5 | 10s | video | 登山/云海/迎客松 | 爬到光明顶那一刻，| 什么都值了 | [兴奋] |
| 情感升华 | 6 | 5s | image | 山顶全家福/日落 | 有些风景，| 只有亲自走上去才能看到 | [低沉] |
| CTA | 7 | 3s | cta | "关注我，带你看更大的世界" | [兴奋] 关注我，| 带你看更大的世界！ | [兴奋] |

**适用场景：** 旅行Vlog、亲子游记、日常记录
**推荐时长：** 45-60s
**推荐分辨率：** 1080x1920（竖屏）或 1080x1080（方屏）
**素材需求：** 5-8张照片 + 1-2段短视频片段

### 6b. 技术讲解模板（教程/数据分析/知识分享）

**结构：** 痛点 → 方案 → 数据 → CTA（4-6 个分镜段）

| 段落 | 镜号 | 时长 | 类型 | 画面描述 | 配音 | 情感 |
|------|------|------|------|---------|------|------|
| 痛点钩子 | 1 | 3s | text-hook | "你每天都在用错误的方式做数据分析" | [疑问] 你做完数据分析，| 老板说"所以呢？" | [疑问] |
| 问题展开 | 2 | 8s | dataviz | 条形图：90%的分析报告没有 actionable insight | [强调] 研究发现：| 90%的数据分析报告 | 没有可执行的结论 | [强调] |
| 方案讲解 | 3 | 8s | image | 流程图/对比图：Before vs After | [转折] 正确的方法是先问问题，| 再找数据 || 而不是反过来 | [转折] |
| 数据验证 | 4 | 8s | dataviz | 柱状图逐条生长：用对方法后效果提升 | [兴奋] 同样的数据，| 换一种分析框架 || 结论清晰度提升300% | [兴奋] |
| 总结收束 | 5 | 5s | text-hook | 核心结论：先问题后数据 | [低沉] 记住：| 分析的价值不在数据多，| 在问题对 | [低沉] |
| CTA | 6 | 3s | cta | "关注我，学习高效数据分析" | [兴奋] 关注我，| 学会真正的数据分析！ | [兴奋] |

**适用场景：** 技术文章精华、数据分析、教程简化
**推荐时长：** 35-45s
**推荐分辨率：** 1080x1920（竖屏）
**素材需求：** 1-2张数据图 + 1-2段动画（dataviz_animate.py 生成）+ 文字帧

**何时使用 dataviz 类型：**
- 有量化对比数据（如 before/after、排名、增长率）
- 需要展示随时间变化的趋势
- 数据点之间需要视觉比较（柱状图/条形图）
- 使用 `dataviz_animate.py --type bar-grow` 生成逐条生长的动画

### 6c. 产品/景点展示模板（种草/评测/探店）

**结构：** 预告 → 展示 → 亮点 → 行动（5-7 个分镜段）

| 段落 | 镜号 | 时长 | 类型 | 画面描述 | 配音 | 情感 |
|------|------|------|------|---------|------|------|
| 预告钩子 | 1 | 3s | text-hook | "我找到了一个99%的人不知道的黄山玩法" | [兴奋] 99%的人爬黄山都爬错了 || 今天告诉你真正的打开方式 | [兴奋] |
| 环境展示 | 2 | 5s | image | 黄山全景/云海/晨光 | [低沉] 大多数人早上8点到山脚，| 排2小时索道 || 我们4:30出发 | [低沉]→[转折] |
| 核心亮点 | 3-4 | 10s | image | 孩子登顶照/迎客松/猴子观海 | [兴奋] 不到6点就在光明顶看日出了！|| 整个山顶就我们几个 | [兴奋] |
| 实用信息 | 5 | 6s | text-hook | "攻略要点：提前订票+早起+错峰" | [转折] 关键就三点：|| 提前订票 | 早起 | 错峰 | [转折] |
| 效果展示 | 6 | 5s | image | 悠闲照片/不排队/美景 | [低沉] 别人在排队，| 我们在拍照 || 这就是早起的奖励 | [低沉] |
| CTA | 7 | 3s | cta | "收藏这份攻略，下次用得上" | [兴奋] 收藏这份攻略！|| 下次去黄山你一定用得上 | [兴奋] |

**适用场景：** 景点评测、产品开箱、探店推荐、攻略分享
**推荐时长：** 30-45s
**推荐分辨率：** 1080x1920（竖屏）或 1080x1080（方屏/小红书）
**素材需求：** 6-10张照片 + 快节奏剪辑
**特点：** 分镜密度高（每镜2-5s），信息量大，节奏快

## 七、分镜脚本质量检查清单

### 视觉检查

- [ ] 每个分镜段都有 `visual` 画面描述（不允许空画面）
- [ ] 没有连续两个同景别镜头（遵守交替公式）
- [ ] 前3秒有钩子帧（text-hook 类型）
- [ ] 关键数据点有 dataviz 或 image 支撑
- [ ] 素材来源已标注（video_path / image_path / 文字帧兜底）
- [ ] 品牌色板已应用（深蓝背景、黄色强调、红色CTA）

### 听觉检查

- [ ] 每段配音都有情感标记（[兴奋]/[低沉]/[转折]/[疑问]/[强调]）
- [ ] 配音字数在语速范围内（180-220 字/分钟）
- [ ] 有停顿标记（`|` 短停、`||` 长停）
- [ ] BGM 有规划（track 和 volume 字段）
- [ ] CTA 段落配音语速比正常偏慢

### 节奏检查

- [ ] 总时长在目标区间内（30-90s 小红书默认）
- [ ] 每15秒有一个信息点/节奏变化
- [ ] 快切和慢切段落合理交替
- [ ] 结尾3秒是 CTA 帧
- [ ] 没有超过10秒的单一镜头

### 平台适配检查

| 平台 | 分辨率 | 字幕风格 | 时长范围 | 检查 |
|------|--------|---------|---------|------|
| 小红书 | 1080x1920 竖屏 | 底部居中，圆角 | 30-60s | [ ] |
| 抖音 | 1080x1920 竖屏 | 底部居中，加粗 | 15-60s | [ ] |
| 视频号 | 1080x1920 竖屏 | 底部居中 | 30-90s | [ ] |
| B站 | 1920x1080 横屏 | 中下偏左，白底黑边 | 60-180s | [ ] |
| YouTube Shorts | 1080x1920 竖屏 | 底部居中，可双语 | 15-60s | [ ] |

## 八、常见问题与反模式

### ❌ 反模式

**反模式1：分镜只有文字没有画面描述**
```
// ❌ 错误
{"type": "text-hook", "visual": "你知道90%的策略都失败吗？"}
// ✅ 正确
{"type": "text-hook", "visual": "你知道90%的策略都失败吗？", "subtitle": "令人震惊的数据"}
```
画面描述是整个分镜的核心——它决定 AI 如何理解这一帧。纯文字帧也必须有视觉说明。

**反模式2：配音稿没有情感标记**
```
// ❌ 错误
"你知道90%的策略为什么失败吗？不是因子不够好，是过拟合。"
// ✅ 正确
"[疑问] 你知道90%的策略为什么失败吗？| [转折] 不是因子不够好，|| [强调] 是过拟合。"
```
没标记的配音是平的，AI 配音会像机器人念稿。情感标记是人声感的灵魂。

**反模式3：没有考虑转场**
```
// ❌ 错误 — 所有镜头都用 cut
[cut, cut, cut, cut, cut]
// ✅ 正确 — 开场fade-in，中间合理交替
[fade-in, cut, cut, slide-left, cut, zoom-out]
```
转场是视觉节奏的一部分。全用 cut 等于没有节奏。

**反模式4：素材来源空白**
```
// ❌ 错误
{"image_path": null, "video_path": null}
// ✅ 正确 — 至少标注素材状态
{"image_path": null, "video_path": "TBD", "visual": "黄山缆车云海（需拍摄或AI生成）"}
```
标注 "TBD" 或者备注说明素材状态。空字段会在合成时被忽略，导致画面空洞。

**反模式5：时间分配失衡**
```
// ❌ 错误 — 开场5s太短，中间35s太长，结尾1s太仓促
5s + 35s + 1s
// ✅ 正确 — 钩子3s，主体35s，CTA 3s
3s + 35s + 3s
```
经典黄金比例：3s 钩子 + 主体 (80%) + 3s CTA。不要头重脚轻或尾巴仓促。

### ✅ 正确做法示例

```
// 完整的优质分镜
{
  "shots": [
    {
      "id": 1, "duration_sec": 3, "type": "text-hook",
      "visual": "90%的人不知道：数据分析的正确姿势",
      "subtitle": "你中招了吗？",
      "video_path": null, "image_path": null,
      "transition": "fade-in", "camera": "fixed",
      "emotion": "[疑问]",
      "notes": "品牌深蓝背景，黄色大字居中，字体64px"
    },
    {
      "id": 2, "duration_sec": 8, "type": "dataviz",
      "visual": "柱状图逐条生长：用对方法 vs 错误方法 效果对比",
      "subtitle": "效果提升300%",
      "video_path": "assets/animations/bar-compare.mp4",
      "image_path": null,
      "transition": "cut", "camera": "push-in",
      "emotion": "[强调]",
      "notes": "调用 dataviz_animate.py --type bar-grow 生成"
    }
  ],
  "voiceover": {
    "text": "[疑问] 你做完数据分析，老板说'所以呢'？| [强调] 90%的人都会犯这个错 || [转折] 今天教你三步做出有价值的分析",
    "speed": 200
  },
  "resolution": "1080x1920"
}
```

## 九、执行流程速查

```
用户输入（文章/主题）
    ↓
Step 1: 提取核心信息 → 1个钩子 + 3-5个数据点 + 1个CTA
    ↓
Step 2: 选择内容模板 → Vlog / 技术讲解 / 产品展示
    ↓
Step 3: 填写10字段分镜表 → 4-7个分镜段
    ↓
Step 4: 配音稿写作 → 加入情感标记 + 停顿标记
    ↓
Step 5: 质量检查 → 视觉/听觉/节奏/平台适配
    ↓
Step 6: 输出 JSON → 直接对接 video_editor.py
    ↓
可选: 调用 video_editor.py --script script.json --output output.mp4
```

## 十、工具对接速查

```bash
# 1. 数据动画生成
python3 biz/content/scripts/dataviz_animate.py \
  --type bar-grow \
  --data '[...]' \
  --columns '策略,Sharpe' \
  --title '策略对比' \
  --duration 8 \
  --output assets/animation.mp4 \
  --brand-colors

# 2. 视频合成
python3 biz/content/scripts/video_editor.py \
  --script assets/script.json \
  --output assets/final.mp4 \
  --resolution 1080x1920
```

## 附录：术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 分镜 | Storyboard | 视频的视觉蓝图，每个镜头的详细描述 |
| 钩子 | Hook | 视频前3秒吸引注意力的内容 |
| CTA | Call to Action | 行动号召，引导用户关注/评论/收藏 |
| 转场 | Transition | 镜头之间的切换方式 |
| 运镜 | Camera Movement | 镜头运动方式（推拉摇移） |
| 景别 | Shot Size | 镜头取景范围（特写/中景/全景） |
| 字幕 | Subtitle | 画面底部文字，辅助理解 |
| 配音 | Voiceover | 旁白/解说音频 |
| BGM | Background Music | 背景音乐 |
| B-roll | B-roll | 辅助画面，穿插在主画面之间 |
