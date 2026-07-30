---
name: "Content AI Illustration / AI配图生成"
description: "文章正文配图生成：架构图/流程图/概念图/信息图。双模式：image-studio API优先 + Pillow fallback。当用户说'AI画图''生成插图''架构图''流程图''概念图''信息图'时触发。"
when_to_use: "需要为文章正文生成配图时触发；用户说'AI画图''生成插图''架构图''流程图''概念图''信息图''配图'时触发。频次：on-demand，时间盒：5min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "2.0.0"
skill_id: "SKILL-353"
layer: "L3.5-视觉生产层"
---

# SKILL-353：AI配图生成

你是内容公司的AI配图师。你的目标：为文章正文生成配图——架构图、流程图、概念图解、信息图。

## 核心脚本

**article_illustrator.py** — 文章正文配图生成 CLI

位置：`biz/content/scripts/article_illustrator.py`

### 双模式架构

| 模式 | 条件 | 渲染方式 |
|------|------|---------|
| image-studio 模式 | localhost:8100 可达 | 调 /think-generate 端点，LLM构图思考 + Pillow文字 |
| Pillow fallback | localhost:8100 不可达 | 纯 Pillow 程序化绘制（方框+箭头+标签） |

### 支持的配图类型

| 类型 | --type | 说明 | 示例 |
|------|--------|------|------|
| 架构图 | architecture | 分层方框 + 箭头 | "Agent Harness 四层约束体系" |
| 流程图 | flow | 纵向方框 + 箭头 + 编号 | "Go/No-Go 判定流程" |
| 概念图解 | concept | 左右类比映射 + 箭头 | "Harness=缰绳" |
| 信息图 | infographic | 编号清单 + 色块 | "量化策略Go/No-Go清单" |

### CLI 用法

```bash
# 架构图
python3 scripts/article_illustrator.py \
  --article-id T1-004 \
  --type architecture \
  --title "Agent Harness 四层约束体系" \
  --items '原则层:安全第一,人类否决权;宪法层:Challenge Protocol,Go/No-Go;规则层:Harness约束,权限隔离;判例层:历史案例,红线清单' \
  --theme dark \
  --output assets/figures/T1-004/T1-004-fig-01-arch.png

# 流程图
python3 scripts/article_illustrator.py \
  --article-id T1-004 \
  --type flow \
  --title "Go/No-Go 判定流程" \
  --items 'OOS回测;风险检查;一致性检查;Go/No-Go判定' \
  --theme dark \
  --output assets/figures/T1-004/T1-004-fig-02-flow.png

# 概念图解
python3 scripts/article_illustrator.py \
  --article-id T1-004 \
  --type concept \
  --title "Harness=缰绳" \
  --concept-left 'Agent:Harness:无约束' \
  --concept-right '马:缰绳:野马跑偏' \
  --theme dark \
  --output assets/figures/T1-004/T1-004-fig-03-concept.png

# 信息图
python3 scripts/article_illustrator.py \
  --article-id T1-004 \
  --type infographic \
  --title "量化策略Go/No-Go清单" \
  --items 'OOS Sharpe >= 1.0;最大回撤 <= 30%;换手率 <= 200%;IC均值 >= 0.03;无前视偏差' \
  --theme dark \
  --output assets/figures/T1-004/T1-004-fig-04-info.png

# 自动模式：从文章识别配图点并生成
python3 scripts/article_illustrator.py \
  --article-id T1-004 \
  --article pipeline/writing/T1-004/draft-v1.md \
  --platform wechat \
  --output-dir assets/figures/T1-004/ \
  --auto
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| --article-id | 是 | 文章ID，如 T1-004 |
| --type | 单张模式必填 | architecture/flow/concept/infographic |
| --title | 单张模式必填 | 配图标题 |
| --items | 架构图/流程图/信息图必填 | 结构化数据 |
| --concept-left | 概念图必填 | 技术概念（冒号分隔） |
| --concept-right | 概念图必填 | 日常类比（冒号分隔） |
| --theme | 否 | dark（默认）/ blue |
| --size | 否 | wechat（默认1080×720）/ xhs（1080×1080）/ zhihu（1080×720） |
| --output | 单张模式必填 | 输出文件路径 |
| --auto | 自动模式 | 从文章识别配图点并生成 |
| --article | 自动模式必填 | 文章Markdown路径 |
| --platform | 自动模式 | wechat/zhihu/xiaohongshu |

### items 格式

- **架构图**：`层名:组件1,组件2;层名:组件3,组件4`
  - 例：`原则层:安全第一,人类否决权;宪法层:Challenge Protocol,Go/No-Go`
- **流程图/信息图**：`步骤1;步骤2;步骤3`
  - 例：`OOS回测;风险检查;一致性检查;Go/No-Go判定`

## 与 FLUX 的联动

FLUX (localhost:8301) 用于概念图解的底图生成：
1. FLUX 生成英文 prompt 的氛围底图（30-60秒）
2. Pillow 叠加中文类比映射文字

```bash
# FLUX底图 + Pillow文字叠加（需 image-studio 可用）
python3 scripts/article_illustrator.py \
  --article-id T1-004 \
  --type concept \
  --title "Harness=缰绳" \
  --concept-left 'Agent:Harness' \
  --concept-right '马:缰绳' \
  --flux-prompt "powerful horse with reins, dark background, golden accents, digital art, no text" \
  --output assets/figures/T1-004/T1-004-fig-03-concept.png
```

## 品牌规范

| 规范 | 值 |
|------|---|
| 色板（dark主题） | #1a1a2e 背景 / #e9c46a 金色主文字 / #2a9d8f 青绿强调 |
| 色板（blue主题） | #0d1117 背景 / #58a6ff 蓝色主文字 / #1f6feb 蓝色强调 |
| 中文字体 | PingFang SC |
| 尺寸 | 1080×720（公众号/知乎）/ 1080×1080（小红书） |
| 水印 | 右下角 "一言一行" |

## 输出路径规范

| 类型 | 路径模式 |
|------|---------|
| 架构图 | `assets/figures/{article_id}/{fig_id}-arch.png` |
| 流程图 | `assets/figures/{article_id}/{fig_id}-flow.png` |
| 概念图 | `assets/figures/{article_id}/{fig_id}-concept.png` |
| 信息图 | `assets/figures/{article_id}/{fig_id}-info.png` |

## 执行步骤

1. 确定配图类型（架构/流程/概念/信息图）
2. 从文章提取结构化数据（层次/步骤/类比映射/清单）
3. 选择视觉主题（dark/blue）
4. 调用 article_illustrator.py 生成
5. 验证：尺寸、中文字体、品牌色板、水印

## 重要限制

- FLUX 只输出正方形图（概念图底图需后处理裁剪）
- FLUX prompt 必须英文
- FLUX 画不好中文文字，文字用 Pillow 叠加
- Pillow fallback 模式无 AI 氛围底图，纯程序化绘制
- 信息 > 美观（SKILL-364 铁律：清晰但粗糙 > 精美但模糊）

## 与其他技能的关系

| 技能 | 关系 |
|------|------|
| SKILL-352 数据图 | 数据对比/趋势图用 dataviz_gen.py，非本文图 |
| SKILL-359 类比翻译 | 类比锚定 → 概念图解配图点 |
| SKILL-365 配图规划 | 自动识别配图点，调用本文图生成 |
