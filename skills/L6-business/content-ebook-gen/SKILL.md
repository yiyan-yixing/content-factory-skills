---
name: "Content Ebook Gen / 电子书生成"
description: "将已验证的 Markdown 内容系列转为标准 EPUB 电子书，包括封面生成、TOC、版权页、元数据。"
when_to_use: "需要将内容打包为电子书时；用户说'生成EPUB''电子书''ebook''打包成书'时触发。频次：on-demand (每册约10min)，时间盒：30min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-604"
layer: "L6-商业化层"
---

# SKILL-604：电子书生成 (Content Ebook Gen)

你是内容工厂的电子书制作人。你的目标：把已验证的 Markdown 内容系列转化为可发布的标准 EPUB 电子书。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | Markdown 文件 (单篇或多篇系列)、品牌色板 |
| **输出** | .epub 文件 + 封面 PNG |
| **依赖** | SKILL-603 内容产品化 (确定产品规格后执行) |
| **工具** | `biz/content/scripts/ebook_gen.py` (Python3 + ebooklib + Pillow) |
| **自动化** | 人工★☆☆☆☆ Agent★★★★★ |
| **训练价值** | 中 |

## 电子书格式规范

### EPUB 标准

| 项目 | 规格 |
|------|------|
| **标准** | EPUB 3 (OCF 容器, XHTML 内容, OPF 元数据) |
| **兼容** | EPUB 2 向后兼容 (Apple Books, Calibre, Kobo, Google Play Books) |
| **元数据** | 标题、作者、语言(zh-CN)、日期、UUID、系列名、卷号 |
| **封面** | 1600x2560 PNG (宽高比 5:8) |
| **导航** | EPUB 3 Nav 文档 + NCX (EPUB 2 兼容) |
| **CSS** | 内联样式, 使用品牌色板, 中文字体优先 |

### 不支持格式 (需额外工具)

| 格式 | 说明 | 工具 |
|------|------|------|
| **MOBI** | Amazon 旧格式, 已淘汰 | Calibre `ebook-convert input.epub output.mobi` |
| **KPF** | Amazon Kindle 新格式 | Kindle Create (桌面应用) |
| **PDF** | 固定版式, 不适合重排版 | Pandoc `pandoc input.md -o output.pdf` |

### 封面尺寸规范

| 用途 | 尺寸 | 比例 | 说明 |
|------|------|------|------|
| **EPUB 标准** | 1600 x 2560 | 5:8 | 品牌默认 |
| **Apple Books** | 1400 x 2240 | 5:8 | 自适应缩放 |
| **Amazon KDP** | 2560 x 4096 | 5:8 | 强制要求 |
| **Google Play** | 1600 x 2560 | 5:8 | 建议一致 |
| **封面预览 (利基)** | 1200 x 1800 | 2:3 | 社交媒体分享 |

## 生成流程

### Step 1: 确认产品规格 (2min)

从 SKILL-603 输出中确认:
- 书名、副标题、作者
- 系列名与卷号 (可选)
- 章节顺序与内容范围
- 有无前言/后记需要补充

### Step 2: 准备 Markdown 源文件 (3min)

确保每个章节的 Markdown 文件:
- 以 H1 (`# 标题`) 开头作为章节标题
- 使用 H2 (`## 标题`) 进行章节内分段
- 代码块用三个反引号包裹
- 图片使用标准 Markdown 语法 `![alt](path)`
- 无 YAML frontmatter 干扰 (会作为正文解析)

> 注意：当前 Markdown→HTML 转换器不支持表格、脚注等高级语法。如有特殊格式需求，直接写 HTML。

### Step 3: 运行生成脚本 (5min)

```bash
# 方式 A：从单篇 Markdown 生成
python3 biz/content/scripts/ebook_gen.py single path/to/article.md \
  -o output/book.epub \
  --title "书名" --subtitle "副标题" --author "一言一行"

# 方式 B：从目录下所有 .md 生成 (按文件名排序)
python3 biz/content/scripts/ebook_gen.py dir path/to/chapters/ \
  -o output/book.epub \
  --title "合集名" --author "一言一行" \
  --series "系列名称" --series-index 1

# 方式 C：自定义章节顺序
python3 biz/content/scripts/ebook_gen.py custom \
  -o output/book.epub \
  --title "自定义书名" --author "一言一行" \
  -- ch01.md ch02.md ch03.md appendix.md

# 添加前言/后记
python3 biz/content/scripts/ebook_gen.py custom \
  -o output/book.epub --title "书名" --author "一言一行" \
  --preface "这是前言文字..." --afterword "path/to/afterword.md" \
  -- ch01.md ch02.md ch03.md
```

### Step 4: 验证 EPUB (5min)

```bash
# 检查文件有效性和大小
ls -lh output/book.epub

# 用 Calibre 验证 (推荐)
# ebook-validate output/book.epub

# 用 Python 快速检查
python3 -c "
from ebooklib import epub
book = epub.read_epub('output/book.epub')
print(f'Title: {book.get_metadata(\"DC\", \"title\")}')
print(f'Author: {book.get_metadata(\"DC\", \"creator\")}')
print(f'Items: {len(list(book.get_items()))}')
print(f'Valid EPUB: OK')
"
```

### Step 5: 在 Apple Books 中手动检查 (可选)

双击 .epub 文件在 Apple Books 中打开，检查:
- 封面是否正常显示
- 目录是否可点击
- 中文排版是否正常
- 代码块是否美观

### Step 6: 交付产物 (2min)

将以下文件提交到产品目录:

```
biz/content/pipeline/product/{product-id}/
├── book.epub          # 可发布的 EPUB
├── book-cover.png     # 封面 PNG (1600x2560)
├── book-source.md     # 合并后的完整 Markdown (源文件副本)
└── _generation-log.md # 生成记录 (参数、日期、文件校验和)
```

## 品牌规范

### 色彩系统

| 用途 | 色值 | CSS |
|------|------|-----|
| 主背景 | 深蓝 #1a1a2e | `#1a1a2e` |
| 标题/导航 | 海军蓝 #16213e | `#16213e` |
| 强调色 | 黄色 #e9c46a | `#e9c46a` |
| 警告/促销 | 红色 #e76f51 | `#e76f51` |
| 正文 | 深灰 #333333 | `#333333` |
| 引用背景 | 浅米 #f8f6f0 | `#f8f6f0` |
| 链接 | 青绿 #2a9d8f | `#2a9d8f` |

### 排版

| 元素 | 字号 | 行高 | 字重 |
|------|------|------|------|
| 书名 (封面) | 56-72pt | 1.2 | Bold |
| H1 标题 | 1.6em | 1.4 | Bold |
| H2 标题 | 1.3em | 1.4 | SemiBold |
| 正文 | 1em | 1.8 | Regular |
| 代码 | 0.85em | 1.4 | Mono |

字体优先级: `PingFang SC, Heiti SC, -apple-system, BlinkMacSystemFont, sans-serif`

### 封面模板

封面图尺寸 1600x2560, 包含:
- 深蓝渐变背景 (顶#1a1a2e → 底#16213e)
- 左上角黄色三角装饰
- 右下角深色圆形装饰
- 顶部+底部品牌色细线
- 白字主标题 (居中偏上)
- 黄字副标题 (居中)
- 红色底色条 + 作者名 (居中偏下)
- 底部版权年份

## 验证检查清单

完成每本电子书后，逐项检查：

```
□ EPUB 文件可以在 Apple Books 中正常打开
□ 封面图片正常显示 (无拉伸/变形)
□ 目录页完整、链接可点击
□ 所有章节内容完整 (无截断/缺失)
□ 中文排版正常 (字体、行距、段落间距)
□ 代码块使用等宽字体
□ 引用区块有黄色左边框
□ 标题层级正确 (H1 → H2)
□ 版权页信息准确 (年份、作者)
□ 元数据正确 (书名、作者、语言)
□ 文件大小合理 (< 5MB 纯文本/ < 50MB 含大量图片)
□ 封面 PNG 同时另存一份用于营销
```

## 与 SKILL-603 联动说明

**SKILL-603 (内容产品化)** 输出 ProductSpec → **SKILL-604 (电子书生成)** 执行生产。

典型工作流:

```
@content-chief-editor 确认选题
     │
     ▼
SKILL-603: 输出产品规格
  - 产品形态: 电子书
  - 书名: "《AI 量化交易实战》"
  - 定价: 29.9 元
  - 章节: [T1-001, T1-002, T1-003, T1-004] (4章)
  - 前言/后记: 需要撰写
     │
     ▼
SKILL-604: 执行生产
  - 准备 Markdown → 运行 ebook_gen.py
  - 生成封面 → 生成 EPUB
  - 验证 → 交付
     │
     ▼
交付产物 → 进入发行管道
  - 自有平台、微信小店、知识付费平台
```

SKILL-603 中应填写 `电子书 → 使用 SKILL-604 生成` 作为生产步骤。

## 反模式 (避免)

- ❌ 直接使用原始连载标题 (应该用产品化标题)
- ❌ 章节无 H1 标题 (脚本依赖 H1 提取章节名)
- ❌ 封面使用非品牌色板 (破坏品牌一致性)
- ❌ 跳过验证直接交付 (EPUB 常见问题: 中文乱码、封面缺失)
- ❌ 忽略 MOBI/KPF 需求 (如果需要上架 Amazon Kindle, 额外用 Calibre 或 Kindle Create 转换)

## 资产沉淀

- 每本电子书生成脚本的运行日志 → `biz/content/pipeline/product/{id}/_generation-log.md`
- 封面 PNG 同步复用为营销素材
- EPUB 文件成品存档用于多平台发布
