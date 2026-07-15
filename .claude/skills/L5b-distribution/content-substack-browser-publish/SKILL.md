---
name: "Content Substack Browser Publish / Substack 浏览器发布"
description: "通过浏览器 CDP 将文章发布到 Substack。绕过 GFW（Chrome 代理）、免费、无需 API。"
when_to_use: "需要发布文章到 Substack 时；用户说'发到Substack''Substack发布''newsletter发布'时触发。频次：on-demand，时间盒：10min/article"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-552"
layer: "L5b-发行执行层"
---

# SKILL-552：Substack 浏览器发布

你是内容公司的 Substack 平台发布执行者。你的目标：通过浏览器 CDP 将文章发布到 Substack，绕过 GFW 封锁。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | ArticleID + 博客文件 |
| **输出** | SubstackPostResult（发布状态 + 文章 URL） |
| **依赖** | Chrome CDP 运行 + 用户已登录 substack.com + PAC 代理 |
| **自动化** | 人工★☆☆☆☆ Agent★★★★★ |
| **训练价值** | 低（机械执行） |

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
  "platform": "substack-browser",
  "article_id": "文章 ID",
  "ids": ["文章 URL"],
  "details": "发布结果描述"
}
```

## 执行步骤

### Step 1：读取并解析内容（2min）

读取博客文件，解析 YAML frontmatter 和 Markdown 正文。提取 title、subtitle、body。Frontmatter subtitle 优先于行内 bold subtitle。

### Step 2：dry-run 预览（1min）

如果 dry_run=true，输出标题、副标题、正文字数预览，不连接浏览器。

### Step 3：连接 Chrome CDP 发布（7min）

1. 连接 Chrome CDP (127.0.0.1:9222) — Chrome 已配置 PAC 代理绕过 GFW
2. 打开 Substack publication URL
3. 点击 "New post"
4. 输入标题（keyboard.type, delay=40ms）— Draft.js 编辑器
5. 输入副标题（Tab 键切换到 subtitle 字段）
6. 输入正文（分段落 keyboard.type，段落间 Enter+Enter）
7. 点击 "Publish" 或 "Save draft"
8. 确认发布对话框（如有）
9. 获取文章 URL

## 产出

1. SubstackPostResult — 发布结果 JSON
2. 文章 URL — 可用于传播方案和交叉引用

## 关键指标

- 标题提取成功率：100%
- 发布成功率：≥ 90%
- 每篇文章耗时：≤ 10 分钟

## 反模式（避免）

- ❌ 用 python-substack API — 被墙（substack.com 在中国无法直接访问）
- ❌ 用 page.fill() 输入文本 — Draft.js 不认
- ❌ 一次性输入超长正文 — Draft.js 会卡死，需分段输入
- ❌ 不等 PAC 代理就绪就导航 — 会超时

## 资产沉淀

- SubstackPostResult → SpreadPlan（文章 URL 用于传播链路）
- 发布耗时数据 → L7 复盘（优化发布效率）
