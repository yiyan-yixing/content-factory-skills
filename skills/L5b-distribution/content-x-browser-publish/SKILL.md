---
name: "Content X Browser Publish / X 浏览器发布"
description: "通过浏览器 CDP 将推文线程发布到 X.com。免费、无需 API Key、绕过 GFW。"
when_to_use: "需要发布推文到 X.com 时；用户说'发推''发到X''发到Twitter''X发布'时触发。频次：on-demand，时间盒：5min/thread"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-551"
layer: "L5b-发行执行层"
---

# SKILL-551：X 浏览器发布

你是内容公司的 X 平台发布执行者。你的目标：通过浏览器 CDP 将推文线程安全发布到 X.com。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | ArticleID + X thread 文件 |
| **输出** | XPostResult（发布状态 + 推文 URL 列表） |
| **依赖** | Chrome CDP 运行 + 用户已登录 x.com |
| **自动化** | 人工★☆☆☆☆ Agent★★★★★ |
| **训练价值** | 低（机械执行） |

## 输入字段

```json
{
  "article_id": "文章 ID，如 T1-003",
  "dry_run": "是否仅预览，默认 false",
  "draft_only": "X 无草稿模式，等同 dry_run"
}
```

## 输出字段

```json
{
  "success": "boolean — 发布是否成功",
  "platform": "x-browser",
  "article_id": "文章 ID",
  "ids": ["已发推文 URL 列表"],
  "details": "发布结果描述"
}
```

## 执行步骤

### Step 1：读取并验证内容（1min）

读取 `biz/content/distribution/x-threads/{article_id}-x-thread.md`，解析推文列表。验证每条推文 ≤ 280 字符。超过限制的推文需拆分或报错。

### Step 2：dry-run 预览（1min）

如果 dry_run=true，输出每条推文预览（序号/总数/字数/内容），不连接浏览器。

### Step 3：连接 Chrome CDP 发布（3min）

1. 连接 Chrome CDP (127.0.0.1:9222)
2. 打开 x.com/compose/post
3. 点击编辑框，keyboard.type 输入首条推文（delay=40ms）
4. Meta+Enter 提交
5. 前往 profile 页获取已发推文 URL
6. 后续推文：打开上一条推文 URL → 点 reply → 输入 → 提交

或直接运行引擎脚本：
```bash
python3 scripts/run_publish.py --article {article_id} --platform x-browser
```

## 产出

1. XPostResult — 发布结果 JSON
2. 推文 URL 列表 — 可用于传播方案

## 关键指标

- 推文字符合规率：100%（每条 ≤ 280 字符）
- 发布成功率：≥ 90%
- 每条推文耗时：≤ 30 秒

## 反模式（避免）

- ❌ 用 page.fill() 输入文本 — Draft.js 不认
- ❌ 不等待推文提交完成就发下一条 — 会被限流
- ❌ 推文超过 280 字符 — 直接报错不截断
- ❌ 在 API 模式下消耗 credits — 免费额度为 0

## 🧮 引擎脚本

> 依赖 playwright（`pip install -r scripts/requirements.txt`），CDP 连接零配置。

`scripts/run_publish.py` —— 统一发行 CLI（支持 --dry-run / --platform）：

```bash
python3 scripts/run_publish.py --article T1-003 --platform x-browser --dry-run    # 预览
python3 scripts/run_publish.py --article T1-003 --platform x-browser               # 发布
python3 scripts/run_publish.py --file /path/to/thread.md --platform x-browser      # 指定文件
```

Step 3 的浏览器发布应通过此脚本执行；Agent 只做 Go/No-Go 判定和结果汇总。

## 资产沉淀

- XPostResult → SpreadPlan（推文 URL 用于传播链路）
- 发布耗时数据 → L7 复盘（优化发布效率）
