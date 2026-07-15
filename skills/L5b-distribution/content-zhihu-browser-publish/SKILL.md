---
name: "Content Zhihu Browser Publish / 知乎浏览器发布"
description: "通过浏览器 CDP 将文章发布到知乎。直接 typing 输入内容（Draft.js 自动转换 Markdown），不支持 Markdown 粘贴或 MD 导入。"
when_to_use: "需要发布文章到知乎时；用户说'发到知乎''知乎发布''知乎文章'时触发。频次：on-demand，时间盒：8min/article"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-553"
layer: "L5b-发行执行层"
---

# SKILL-553：知乎浏览器发布

你是内容公司的知乎平台发布执行者。你的目标：通过浏览器 CDP 将文章发布到知乎专栏。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | ArticleID + 知乎内容文件 |
| **输出** | ZhihuPostResult（发布状态 + 文章 URL） |
| **依赖** | Chrome CDP 运行 + 用户已登录 zhihu.com |
| **自动化** | 人工★☆☆☆☆ Agent★★★★☆ |
| **训练价值** | 低（机械执行，但需添加话题才能发布） |

## 输入字段

```json
{
  "article_id": "文章 ID，如 T1-003",
  "dry_run": "是否仅预览，默认 false",
  "draft_only": "是否仅保存草稿，默认 false"
}
```

## 输出字段

```json
{
  "success": "boolean — 发布是否成功",
  "platform": "zhihu-browser",
  "article_id": "文章 ID",
  "ids": ["文章 URL"],
  "details": "发布结果描述"
}
```

## 执行步骤

### Step 1：读取并准备内容（1min）

读取 `biz/content/distribution/zhihu/{article_id}-zhihu.md`。如无专用文件，从 blog 文件复制。提取标题用于日志。

### Step 2：dry-run 预览（1min）

如果 dry_run=true，输出标题和字数预览，不连接浏览器。

### Step 3：连接 Chrome CDP 发布（6min）

1. 连接 Chrome CDP (127.0.0.1:9222)
2. 打开 `zhuanlan.zhihu.com/write`（⚠️ 不是 zhihu.com/writer，后者 404）
3. **scrollTo(0,0)** — 标题字段在页面顶部，需先滚动到顶
4. 输入标题到 `textarea.WriteIndex-titleInput`（⚠️ 是 TEXTAREA 不是 input！且必须先输入标题，否则发布/预览按钮禁用）
5. 点击 `[contenteditable="true"]` 编辑器，**逐行 keyboard.type 输入正文**（Draft.js 自动转换 Markdown 语法，`##` 渲染为 `<h3>`）
6. **添加话题**（发布前必须）：点击 "发布设置" → "添加话题" → 搜索 "人工智能" → 点击 `.Popover-content button` 建议（⚠️ 需用 JS click，普通 click 不响应）
7. 点击 "发布" 或保存草稿
8. 获取文章 URL（`/p/` 路径）

或直接运行引擎脚本：
```bash
python3 scripts/run_publish.py --article {article_id} --platform zhihu-browser
```

### 关键注意事项

- 知乎 `##` 渲染为 `<h3>`（标题层级偏移 +1）
- **不支持 Markdown 粘贴** — 粘贴会显示原始文本
- **不支持 MD 文件导入**（CDP 模式下 file chooser 无法触发）
- ✅ **正确方式：逐行 keyboard.type 直接输入** — Draft.js 自动转换 Markdown 语法
- 标题是 `textarea.WriteIndex-titleInput`（⚠️ 不是 input！）
- 发布/预览按钮在标题未输入时是**禁用状态**
- 必须添加话题后才能发布（"发布设置" → "添加话题"）
- 话题建议按钮需用 `evaluate("el.click()")` JS click
- 不受 GFW 限制 — zhihu.com 在中国可直接访问

## 产出

1. ZhihuPostResult — 发布结果 JSON
2. 文章 URL — 可用于传播方案和交叉引用

## 关键指标

- MD 导入成功率：N/A（CDP 模式不支持 MD 导入）
- 直接 typing 内容完整性：≥ 90%（Draft.js 自动转换）
- 发布成功率：≥ 90%

## 反模式（避免）

- ❌ 直接粘贴 Markdown 到编辑器 — 知乎会显示原始文本
- ❌ 试图通过 file chooser 上传 .md 文件 — CDP 模式下无法触发
- ❌ 用 page.fill() 输入内容 — Draft.js 不认，必须用 keyboard.type()
- ❌ 不输入标题就点发布 — 按钮是禁用状态
- ❌ 不添加话题就点发布 — 知乎要求至少一个话题
- ❌ 用普通 .click() 点话题建议 — 需用 JS click（evaluate("el.click()")）

## 🧮 引擎脚本

> 依赖 playwright（`pip install -r scripts/requirements.txt`），CDP 连接零配置。

`scripts/run_publish.py` —— 统一发行 CLI（支持 --dry-run / --draft-only / --platform）：

```bash
python3 scripts/run_publish.py --article T1-003 --platform zhihu-browser --dry-run    # 预览
python3 scripts/run_publish.py --article T1-003 --platform zhihu-browser               # 发布
python3 scripts/run_publish.py --article T1-003 --platform zhihu-browser --draft-only  # 仅草稿
python3 scripts/run_publish.py --file /path/to/article.md --platform zhihu-browser     # 指定文件
```

Step 3 的浏览器发布应通过此脚本执行；Agent 只做 Go/No-Go 判定和结果汇总。

## 资产沉淀

- ZhihuPostResult → SpreadPlan（文章 URL 用于传播链路）
- 内容完整性数据 → L7 复盘（优化 MD 格式适配）
