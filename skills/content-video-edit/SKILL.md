---
name: "Content Video Edit / 视频剪辑"
description: "用ffmpeg/moviepy将分镜素材合成为完整短视频，支持TTS配音/BGM/字幕烧录。当用户说'剪辑视频''合成视频''moviepy''视频编辑'时触发。"
when_to_use: "需要剪辑视频时；用户说'剪辑视频''合成视频''moviepy剪辑''视频制作''配音''BGM'时触发。频次：on-demand，时间盒：20-30min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "2.0.0"
skill_id: "SKILL-5B2"
layer: "L5b-视频发行层"
---

# SKILL-5B2：视频剪辑（增强版）

你是内容公司的剪辑师。你的目标：将分镜脚本和素材合成为完整短视频，支持 TTS 配音合成、BGM 背景音乐叠加、字幕烧录。

前置技能：`SKILL-5B1`（短视频分镜脚本）产出 JSON 分镜文件。本技能接收该 JSON，完成从素材到成片的全部流程。

## 技术栈

- **moviepy 2.1.1** — Python 视频剪辑库（画面拼接、音频叠加、字幕烧录）
- **ffmpeg 7.1.1** — 底层编解码
- **OpenAI TTS API** — AI 配音生成（tts-1 模型）
- **Pillow** — 文字帧/字幕帧的位图渲染

---

## 一、TTS 配音集成规则

### 1.1 OpenAI TTS API 调用

使用 OpenAI `tts-1` 模型生成配音音频。调用格式（curl）：

```bash
# 基础调用
curl https://api.openai.com/v1/audio/speech \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "配音文本内容",
    "voice": "alloy",
    "speed": 1.0,
    "response_format": "mp3"
  }' \
  --output assets/audio/voiceover.mp3
```

**集中分镜文本再调用**：整段配音应合并为一个请求（避免分段产生不一致的语速/音色），单次请求上限 4096 字符。超出时按自然段落拆分为多个请求，用 `concat` 拼接。

拆分规则：
```
一段配音 = 所有配音字段合并 + 情感标记去除（API 不识别 [疑问] 等标记，仅保留纯文本）
[TTS input] = 去除情感标记 [xxx] 和停顿标记 | 和 || 后的纯文本
```

**批量脚本模板**（适用于多分段）：

```bash
#!/bin/bash
# 从脚本 JSON 提取 voiceover text，分段生成 TTS
SCRIPT_JSON="assets/videos/T1-004/script.json"
OUTPUT_DIR="assets/audio/T1-004"
mkdir -p "$OUTPUT_DIR"

# 整段配音（推荐 — 一致性更好）
jq -r '.voiceover.text // empty' "$SCRIPT_JSON" | \
  while IFS= read -r text; do
    # 去除情感标记和停顿标记
    clean_text=$(echo "$text" | sed 's/\[[^]]*\]//g; s/|//g')
    if [ -n "$clean_text" ]; then
      curl -s https://api.openai.com/v1/audio/speech \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$(jq -n --arg t "$clean_text" '{
          model: "tts-1", input: $t, voice: "alloy",
          speed: 1.0, response_format: "mp3"
        }')" \
        --output "$OUTPUT_DIR/voiceover.mp3"
      break
    fi
  done
```

### 1.2 语速选择

| 内容情绪 | 语速 | 适用场景 |
|---------|------|---------|
| 标准讲述 | 1.0x | 主线叙事、讲解分析、数据解读 |
| 钩子/急迫 | 1.1x~1.2x | 开头钩子帧、紧迫感段落、快节奏高潮 |
| 情感/深沉 | 0.9x | 低沉段落、重要结论、情感升华 |
| CTA | 1.0x~1.1x | 结尾号召，正常偏快带热情 |

**经验规则**：
- 钩子帧配音比正常快 10-15%，制造紧迫感
- 数据/结论段落降速到 0.95x，让关键词被听清
- 不要整段用同一个语速 — 情绪上升时加速，下沉时减速

### 1.3 音色选择

| 音色 | 英文名 | 推荐场景 | 适用内容类型 |
|------|--------|---------|------------|
| 合金 | alloy | 技术讲解、数据分析、中性叙事 | 技术教程、量化分析、研究报告 |
| 新星 | nova | 热情 Vlog、生活记录、兴奋分享 | 旅行Vlog、产品体验、日常记录 |
| 寓言 | fable | 故事叙述、情感深沉、慢节奏叙事 | 品牌故事、人生感悟、深度解读 |
| 回音 | echo | 低沉冷静、权威感、严肃内容 | 警示内容、严肃讨论、深度分析 |
| 光辉 | shimmer | 温暖亲切、女性叙事、柔和语调 | 亲子内容、生活分享、温馨Vlog |
| 珊瑚 | coral | 中性温暖、平衡、通用型 | 综合内容、多类型通用 |

**选择优先级**：
```
技术/量化内容 → alloy (最稳)
Vlog/旅行/亲子 → nova (最贴合)
品牌故事/叙事 → fable (有厚度)
警示/深度内容 → echo (有力量)
温馨/生活分享 → shimmer (温暖感)
不确定 → alloy (中性不翻车)
```

### 1.4 音频文件格式管理

**目录规范**：
```
assets/
└── audio/
    └── {project_id}/
        ├── voiceover.mp3    # TTS 配音（主要音频轨）
        └── (future: per-shot segments)
```

**文件命名规则**：
```
{project_id}-voiceover.mp3       # 整段配音
{project_id}-bgm-{style}.mp3     # 背景音乐
{project_id}-shot-{n}.mp3        # 逐镜配音（需拆分时）
```

**格式标准**：
- 输入：OpenAI TTS API 输出 `.mp3`（默认 44.1kHz, 单声道）
- 临时文件：`tempfile.NamedTemporaryFile(suffix='.mp3')` 用于缓存
- 最终成品：视频内嵌 AAC 音频（`audio_codec='aac'`）

---

## 二、分镜 JSON 音频字段

`video_editor.py` v2.0 支持通过分镜 JSON 的顶层字段加载音频。格式如下：

### 2.1 voiceover 字段

```json
{
  "voiceover": {
    "path": "assets/audio/T1-004/voiceover.mp3",
    "volume": 1.0,
    "language": "zh-CN",
    "text": "[疑问] 你知道90%的策略为什么失败吗？"
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | string | 是 | TTS 音频文件路径，相对于项目根目录 |
| volume | float | 否 | 配音音量，0.0~1.0，默认 1.0 |
| language | string | 否 | 语言，默认 zh-CN |
| text | string | 否 | 配音原文（仅用于记录/质量检查，不参与合成） |

### 2.2 bgm 字段

```json
{
  "bgm": {
    "path": "assets/audio/bgm/ambient-tech.mp3",
    "volume": 0.2,
    "fade_in": 0.5,
    "fade_out": 1.5
  }
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | string | 是 | BGM 音频文件路径 |
| volume | float | 否 | BGM 音量，0.0~1.0，默认 0.2 |
| fade_in | float | 否 | 淡入秒数，默认 0.5 |
| fade_out | float | 否 | 淡出秒数，默认 1.5 |

### 2.3 完整 JSON 示例

```json
{
  "title": "量化策略为什么失败",
  "shots": [
    {"id": 1, "duration_sec": 3, "type": "text-hook", "visual": "90%的策略都失败了", "subtitle": "为什么？"},
    {"id": 2, "duration_sec": 8, "type": "dataviz", "visual": "柱状图", "subtitle": "OOS Sharpe排名", "video_path": "assets/animations/sharpe.mp4"},
    {"id": 3, "duration_sec": 5, "type": "image", "visual": "收益曲线", "subtitle": "差距一目了然", "image_path": "assets/images/curve.png"},
    {"id": 4, "duration_sec": 4, "type": "cta", "visual": "关注我，每周拆解一个策略", "subtitle": ""}
  ],
  "voiceover": {
    "path": "assets/audio/T1-004/voiceover.mp3",
    "volume": 1.0
  },
  "bgm": {
    "path": "assets/audio/bgm/ambient-tech.mp3",
    "volume": 0.2
  }
}
```

---

## 三、视频合成流程

### 3.1 命令模板

完整合成命令：

```bash
python3 biz/content/scripts/video_editor.py \
  --script assets/videos/T1-004/script.json \
  --output assets/videos/T1-004/final.mp4 \
  --resolution 1080x1920
```

分步调试时，可先生成无音频版本（分镜 JSON 不包含 voiceover/bgm 字段）：

```bash
# 无音频 — 用于视觉检查
python3 biz/content/scripts/video_editor.py \
  --script assets/videos/T1-004/script_nosound.json \
  --output assets/videos/T1-004/visual_only.mp4 \
  --resolution 1080x1920

# 带音频 — 用于终审
python3 biz/content/scripts/video_editor.py \
  --script assets/videos/T1-004/script_full.json \
  --output assets/videos/T1-004/final.mp4 \
  --resolution 1080x1920
```

### 3.2 多段素材拼接规则

`video_editor.py` 自动按 `shots` 数组顺序拼接。素材优先级：

```
video_path (mp4) > image_path (png/jpg) > 品牌文字帧 (自动生成)
```

**各 shot_type 的预期素材：**

| 类型 | 预期素材 | 无素材时兜底 | 推荐时长 |
|------|---------|------------|---------|
| dataviz | dataviz_animate.py 生成的 mp4 | "数据加载中..." 文字帧 | 6-10s |
| image | PNG/JPG 图片 | 品牌深蓝背景 + text | 4-6s |
| text-hook | 无（自动生成） | 品牌深蓝背景 + 黄色大字 | 3-5s |
| cta | 无（自动生成） | 品牌深蓝背景 + 红色大字 | 3-4s |

**dataviz 动画预生成命令：**

```bash
python3 biz/content/scripts/dataviz_animate.py \
  --type bar-grow \
  --data '[["策略A",3.2],["策略B",2.8],["策略C",1.5]]' \
  --columns '策略,OOS Sharpe' \
  --title '17个策略OOS Sharpe' \
  --duration 8 \
  --fps 24 \
  --output assets/animations/sharpe.mp4 \
  --brand-colors
```

### 3.3 转场规则

`video_editor.py` 当前按 `cut`（硬切）拼接所有镜头。如需转场效果，在合成后通过 ffmpeg 后处理添加：

| 转场 | 命令 | 适用场景 |
|------|------|---------|
| 硬切 (cut) | 默认，无需处理 | 节奏快、信息密集、数据间切换 |
| 淡入 (fade-in) | `ffmpeg -i in.mp4 -vf "fade=t=in:st=0:d=0.5" out.mp4` | 开场第一个镜头 |
| 淡出 (fade-out) | `ffmpeg -i in.mp4 -vf "fade=t=out:st={end-1.5}:d=1.5" out.mp4` | 结尾最后一个镜头 |
| 交叉溶解 (dissolve) | `ffmpeg -i a.mp4 -i b.mp4 -filter_complex "xfade=transition=fade:duration=0.5:offset={offset}"` | 节奏放缓、情感过渡 |

**转场选择规则：**
```
开篇第一镜 → fade-in (0.5s)
中间连续数据 → cut (保持节奏)
段落切换 → cut 或 dissolve (视情绪)
收尾最后一镜 → fade-out (1.5s)
CTA 前 → cut (不减弱号召力)
```

> 注意：每个镜头 JSON 中的 `transition` 字段当前为记录用途，实际转场需通过手动 ffmpeg 后处理实现。计划在 v2.1 中实现自动转场渲染。

### 3.4 分辨率适配

| 画面比例 | 分辨率 | 适用平台 | 应用场景 |
|---------|--------|---------|---------|
| 9:16 竖屏 | `1080x1920` | 小红书、抖音、视频号、YouTube Shorts | 手机短视频（默认） |
| 16:9 横屏 | `1920x1080` | B站、YouTube、知乎视频 | PC/电视端内容 |
| 1:1 方屏 | `1080x1080` | 小红书笔记内嵌、Instagram Feed | 信息流嵌入、图文+视频混合 |

```bash
# 竖屏（默认）
python3 video_editor.py --script script.json --output out.mp4 --resolution 1080x1920

# 横屏
python3 video_editor.py --script script.json --output out.mp4 --resolution 1920x1080

# 方屏
python3 video_editor.py --script script.json --output out.mp4 --resolution 1080x1080
```

**自适应规则**：当分镜 JSON 未指定 resolution 时，默认竖屏 `1080x1920`。多个分辨率的素材会被统一缩放到目标分辨率（`clip.resized(resolution)`）。

### 3.5 平台目标时长

| 平台 | 推荐时长 | 最长时间 | 策略 |
|------|---------|---------|------|
| 小红书 | 30-60s | 90s | 信息密度高，前3秒定生死 |
| 抖音 | 15-30s | 60s | 极快节奏，每5秒一个信息点 |
| 视频号 | 30-90s | 180s | 可稍长，适合深度内容 |
| 快手 | 15-45s | 60s | 兼顾节奏与信息量 |
| YouTube Shorts | 15-60s | 60s | 上限严格，15-30s 最佳 |
| B站横屏 | 60-180s | 300s | 可做中长深度视频 |

**时长控制规则**：
1. 总时长由 `shots` 中所有 `duration_sec` 之和决定
2. 优先做短不做长 — 去掉所有"有趣但没必要"的镜头
3. 配音时长必须 ≤ 视频总时长（确保音频不截断）
4. 如果配音时长 > 视频时长，增加过渡镜头或延长现有镜头

---

## 四、BGM 选择规则

### 4.1 情绪→BGM 风格映射

| 内容情绪 | BGM 风格 | 乐器特征 | 建议关键词 | 避免 |
|---------|---------|---------|----------|------|
| 技术/叙事/教程 | Ambient, Electronic, Cinematic | 氛围合成器、低音弦乐、轻柔律动 | "ambient tech", "cinematic documentary" | 强节奏、人声采样 |
| 旅行/Vlog/活力 | Indie Pop, Acoustic, Ukulele | 吉他、钢琴、轻快鼓点 | "upbeat ukulele", "happy indie" | 沉重、低音过重 |
| 产品展示/种草 | Modern Pop, 节奏感 | 电音、拍手、明快钢琴 | "modern pop", "product showcase" | 悲伤、忧郁 |
| 深度分析/严肃 | Ambient Dark, Piano | 低音提琴、弱钢琴、白噪音 | "dark ambient", "serious documentary" | 欢快、流行 |
| 数据可视化/金融 | Tech Minimal, Lo-fi | 电子鼓点、低频脉冲、极简旋律 | "minimal tech", "lofi study" | 人声、情绪激烈 |
| 亲子/温馨 | Soft Piano, Acoustic | 钢琴、弦乐、轻柔吉他 | "soft piano", "family warm" | 强节奏、电子音 |
| 开头钩子 | 无或极弱 | — | 前3秒通常不加BGM | 任何干扰性声音 |

### 4.2 音量控制

**自动混音规则**（video_editor.py 自动处理）：

| 场景 | 配音音量 | BGM 音量 | 效果 |
|------|---------|---------|------|
| 旁白进行中 | 1.0 (0dB) | 0.15~0.20 (-15dB~-14dB) | 人声清晰，BGM 作为背景氛围 |
| 纯画面/无旁白 | — | 0.25~0.35 (-12dB~-9dB) | BGM 抬起补充画面情绪 |
| CTA 段 | 1.0 (0dB) | 0.10~0.15 (-20dB~-16dB) | CTA 最突出 |
| 钩子帧（前3秒） | 1.0 | 0.05~0.10 (-26dB~-20dB) | 或纯画面不加BGM |

**标准配置**（JSON 中的 bgm.volume）：
```
BGM 有旁白时：0.20  （平衡：听得见但不抢）
BGM 无旁白时：0.30  （音乐更明显）
仅氛围音时：  0.10  （几乎听不到的底噪）
```

### 4.3 淡入淡出规范

BGM 默认不自动淡入淡出（保持原始音乐起始段）。如需处理，使用 ffmpeg 后处理：

```bash
# BGM 淡入 0.5s + 淡出 1.5s（作用于最终视频的音频轨）
ffmpeg -i final_with_bgm.mp4 \
  -af "afade=t=in:st=0:d=0.5,afade=t=out:st={end-1.5}:d=1.5" \
  -c:v copy \
  final_with_fade.mp4
```

**标准时间**：
```
淡入 (fade-in):  0.5s  — 温和进入，不明显
淡出 (fade-out): 1.5s  — 缓收尾，不突兀
段落间:          1.0s  — 如视频内部分段，段落间淡出再淡入
```

**何时必做淡入淡出**：
- 开场第一个镜头 → 淡入（不然 BGM 突然响起很突兀）
- 结尾 CTA 结束时 → 淡出（不然戛然而止）
- 过渡段（场景切换） → 淡出再淡入

---

## 五、字幕规则

### 5.1 中文字幕

| 属性 | 值 | 说明 |
|------|-----|------|
| 字体 | PingFang SC Bold | 系统自带，粗体确保可读 |
| 字号（竖屏 9:16） | 32pt | 1080x1920 分辨率 |
| 字号（横屏 16:9） | 28pt | 1920x1080 分辨率 |
| 字号（方屏 1:1） | 30pt | 1080x1080 分辨率 |
| 颜色 | #ffffff 白色 | 高对比 |
| 背景 | 半透明黑条 (rgba 0,0,0,160) | 底部 80px 高 |

### 5.2 英文字幕

| 属性 | 值 | 说明 |
|------|-----|------|
| 字体 | SF Pro 或 Helvetica | 系统英文首选字体 |
| 字号 | 28pt（竖屏）/ 24pt（横屏） | 略小于中文 |
| 颜色 | #ffffff 白色 | 高对比 |
| 背景 | 同中文字幕 | 统一视觉 |

双语字幕时，英文放在中文下方，字号小 2pt。

### 5.3 位置规则

```
底部 10-15% 区域，不遮挡关键画面
                                   ┌──────────┐
                                   │          │
                                   │  画面内容 │
                                   │   (85-90%)│
                                   │          │
                                   ├──────────┤
                                   │ ████████  │  ← 半透明黑条 (80px高)
                                   │  字幕文字  │  ← 居中对齐
                                   └──────────┘
                                   bottom: 40px 边距
```

**相对位置参数**：
```python
sub_clip = sub_clip.with_position(('center', 0.85), relative=True)
# 0.85 = 距离顶部 85%（即底部 15%）
```

### 5.4 显示规则

**每行字符限制**：
```
中文：每行 ≤ 15 个汉字
英文：每行 ≤ 35 个字符（含空格）
```

**换行规则**：
```
长字幕拆分示例：
❌ "这个量化策略在实盘交易中表现非常出色并且回撤很小"
   （22个字，超限 — 观众读不完）

✅ 拆分两行：
   "这个量化策略在实盘交易中"
   "表现非常出色并且回撤很小"
   （每行 ≤ 15字）
```

**CTA 帧不叠加字幕**：`video_editor.py` 默认跳过 cta 类型的字幕叠加（`shot_type != 'text-hook'` 条件中不含 cta）。

**text-hook 帧不叠加字幕**：文案已显示在画面中央，叠加字幕会冗余。

### 5.5 同步规则

字幕文本通过 `shots[].subtitle` 字段设置，时长自动跟随 `duration_sec`。每帧字幕独立，不重叠。

**与 TTS 时间同步**：
```
字幕显示时长 ≈ 配音朗读该段所需时长

计算公式：
  字幕时长(s) = 该段字数 / 语速(字/秒)
  示例：10个字 / 3字/秒(180字/分钟) ≈ 3.3秒
```

**检查点**：
- 快速段落（钩子帧） → 字幕显示时间≥2秒（否则读不完）
- 慢速段落（结论）   → 字幕显示时间≤6秒（否则分散注意力）
- 字幕与配音内容一致 → 逐行对照检查

---

## 六、质量检查清单

执行完视频合成后，逐项检查。任何一项不合格都需要返工。

### 6.1 视觉检查

- [ ] 视频分辨率正确（与 --resolution 参数一致）
- [ ] 品牌色板一致（深蓝背景 `#1a1a2e`、黄色文字 `#e9c46a`、红色CTA `#e76f51`）
- [ ] 没有无画面段落（所有镜头都有 visual/video_path/image_path）
- [ ] dataviz 动画流畅播放，没有中断或闪烁
- [ ] 图片素材分辨率适配（没有拉伸变形）
- [ ] 开场钩子帧画面简洁有力（≤7字关键视觉）
- [ ] CTA 帧品牌红色 + 大字突出

### 6.2 听感检查

- [ ] 配音清晰可听，没有爆音/破音/电流声
- [ ] BGM 没有盖过旁白（BGM 音量应在 0.15~0.25 之间）
- [ ] 配音与画面时长匹配（音频没有被截断）
- [ ] 配音语速与内容情绪匹配（钩子帧偏快，结论段偏慢）
- [ ] 配音音色与内容类型匹配（技术类用 alloy，Vlog 类用 nova）
- [ ] 无明显环境噪音
- [ ] CTA 段配音音量正常，语速适中

### 6.3 节奏检查

- [ ] 总时长在目标平台范围内（小红书 30-60s / 抖音 15-30s / Reels 15-60s）
- [ ] 前 3 秒有钩子（信息密度高 > 后续段落）
- [ ] 每 15 秒有一个信息点或情绪变化
- [ ] 没有超过 10 秒的单一镜头（长镜头需要配音持续支撑）
- [ ] 结尾 3 秒是 CTA 帧
- [ ] 快慢节奏交替合理（不是全快或全慢）

### 6.4 字幕检查

- [ ] 字幕没有错别字
- [ ] 每行 ≤ 15 个中文字 / ≤ 35 个英文字符
- [ ] 字幕与配音同步（时长匹配）
- [ ] 字幕不遮挡关键画面元素
- [ ] 字幕字体清晰可读（白色 + 半透明黑底）
- [ ] CTA 和 text-hook 没有多余字幕

---

## 七、完整工作流（6步）

从分镜到成片的完整 6 步流程：

```
Step 1 ─── 输入分镜 JSON
           │ 来源：SKILL-5B1 产出的 script.json
           │ 检查：shots 数组完整、voiceover/bgm 字段可选
           ↓
Step 2 ─── 收集素材
           │ a. 数据动画：dataviz_animate.py 生成 mp4
           │ b. 图片素材：截图/AI配图/设计稿
           │ c. BGM：从资源库选择匹配情绪的曲目
           │ 输出：assets/animations/, assets/images/, assets/audio/bgm/
           ↓
Step 3 ─── 生成 TTS 配音
           │ a. 从 script.json 提取配音文本
           │ b. 选择语速 (1.0x) 和音色 (alloy/nova/...)
           │ c. 调用 OpenAI TTS API 生成 voiceover.mp3
           │ 输出：assets/audio/{project_id}/voiceover.mp3
           ↓
Step 4 ─── 合成视频
           │ a. 更新 script.json（填充 voiceover.path, bgm.path）
           │ b. 运行 video_editor.py 合成
           │ 输出：{project_id}/final.mp4 (含视觉/配音/BGM)
           ↓
Step 5 ─── 后期处理（可选）
           │ a. 转场效果（ffmpeg 后处理加 fade-in/fade-out）
           │ b. 音频微调（ffmpeg 后处理音量平衡）
           │ c. 字幕同步检查
           │ 输出：{project_id}/final_tuned.mp4
           ↓
Step 6 ─── 质量检查 + 输出
           │ a. 对照检查清单逐项过
           │ b. 不合格 → 回到 Step 2/3/4 调整
           │ c. 合格 → 输出最终 mp4
           输出：{project_id}/{platform}_final.mp4
```

### 一键合成脚本模板

```bash
#!/bin/bash
# 需手动填入以下变量
PROJECT_ID="T1-004"
SCRIPT_JSON="assets/videos/${PROJECT_ID}/script.json"
OUTPUT="assets/videos/${PROJECT_ID}/final.mp4"
RESOLUTION="1080x1920"

# Step 2: 生成数据动画（如有 dataviz 镜头）
# python3 biz/content/scripts/dataviz_animate.py ...

# Step 3: 生成 TTS（如 voiceover.path 不存在）
# ...curl OpenAI...

# Step 4: 合成
python3 biz/content/scripts/video_editor.py \
  --script "$SCRIPT_JSON" \
  --output "$OUTPUT" \
  --resolution "$RESOLUTION"

echo "=== Done: $OUTPUT ==="
echo "请执行 Step 5+6 质量检查"
```

---

## 八、工具对接速查

```bash
# ─── 数据动画生成 ───
python3 biz/content/scripts/dataviz_animate.py \
  --type bar-grow \
  --data '[["策略A",3.2],["策略B",2.8]]' \
  --columns '策略,OOS Sharpe' \
  --title '策略对比' \
  --duration 8 \
  --output assets/animations/bar.mp4 \
  --brand-colors

# ─── TTS 配音生成（OpenAI API） ───
curl -s https://api.openai.com/v1/audio/speech \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"tts-1","input":"配音文本","voice":"alloy","speed":1.0}' \
  --output assets/audio/voiceover.mp3

# ─── 视频合成（无音频，视觉检查用） ───
python3 biz/content/scripts/video_editor.py \
  --script assets/script_nosound.json \
  --output assets/visual_only.mp4 \
  --resolution 1080x1920

# ─── 视频合成（完整版，含 TTS + BGM） ───
python3 biz/content/scripts/video_editor.py \
  --script assets/script.json \
  --output assets/final.mp4 \
  --resolution 1080x1920

# ─── ffmpeg 转场：淡入 + 淡出 ───
ffmpeg -i final.mp4 \
  -vf "fade=t=in:st=0:d=0.5,fade=t=out:st=28.5:d=1.5" \
  -af "afade=t=in:st=0:d=0.5,afade=t=out:st=28.5:d=1.5" \
  -c:v libx264 -c:a aac \
  final_with_fade.mp4
```

---

## 附录：常见问题与排查

### Q1: 合成时提示 "No module named moviepy"
```bash
pip install moviepy pillow numpy
```

### Q2: BGM 没有声音
- 检查 `bgm.path` 文件是否存在
- 检查 `bgm.volume` 是否 > 0（默认 0.2）
- 确认 `.mp3` 文件格式正确（用播放器测试）
- 查看控制台是否有 `Warning: BGM audio load failed` 信息

### Q3: 配音与画面不同步
- 确保配音总时长 ≤ 视频总时长
- 检查配音文件是否被截断（`tts.subclip(0, video_clip.duration)`）
- 语速与字幕长度不匹配时，调整 `duration_sec` 或配音文本

### Q4: 最终文件播放没有音频轨道
- 旧版 JSON 格式（纯数组）不触发音频叠加 → 改用新版字典格式
- 检查是否有 `has_audio = True` 的输出信息
- 用 `ffprobe final.mp4` 查看是否有 `Audio` stream

### Q5: BGM 循环播放有明显接缝
- BGM 文件本身应是无缝循环版（或尾部有足够淡出）
- 在 BGM 文件选择时优先选择标注 "loop" 的版本
- 如无 loop 版本，在视频淡出段开始前让 BGM 自然结束
