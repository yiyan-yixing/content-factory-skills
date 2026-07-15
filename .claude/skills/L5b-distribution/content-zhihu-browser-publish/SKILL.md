---
name: "Content Zhihu Browser Publish / 知乎浏览器发布"
description: "通过浏览器 CDP 将文章发布到知乎。必须用 MD 文件导入，不支持 Markdown 粘贴。"
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
| **训练价值** | 低（机械执行，但有 MD 导入特殊逻辑） |

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
2. 打开 zhihu.com/writer
3. 点击 "写文章" 进入编辑器
4. **清空编辑器**：selectAll + Backspace（Draft.js 状态陷阱，不清空则导入会追加到残留内容后）
5. **点击 "导入 Markdown 文档"** — ⚠️ 不能粘贴 Markdown！知乎编辑器会把 Markdown 显示为原始文本
6. 通过 file chooser 上传临时 .md 文件
7. 等待导入渲染（5 秒）
8. 检查导入内容是否完整（contenteditable 区域文本长度 > 50 字符）
9. 点击 "发布" 或保存草稿
10. 获取文章 URL

### 关键注意事项

- 知乎 `##` 渲染为 `<h3>`（标题层级偏移 +1）
- 知乎不支持 Markdown 粘贴 — **必须**用 MD 文件导入
- 导入前必须清空编辑器 — 否则新内容会追加到旧内容后
- 不受 GFW 限制 — zhihu.com 在中国可直接访问

## 产出

1. ZhihuPostResult — 发布结果 JSON
2. 文章 URL — 可用于传播方案和交叉引用

## 关键指标

- MD 导入成功率：≥ 90%
- 导入后内容完整性：≥ 95%（对比原始 MD 字数）
- 发布成功率：≥ 90%

## 反模式（避免）

- ❌ 直接粘贴 Markdown 到编辑器 — 知乎会显示原始文本
- ❌ 导入前不清空编辑器 — 新内容追加到旧内容后
- ❌ 不等导入渲染就点发布 — 内容不完整
- ❌ 试图修改导入后的标题 — 应在 MD 文件中修改再重新导入

## 资产沉淀

- ZhihuPostResult → SpreadPlan（文章 URL 用于传播链路）
- 导入完整性数据 → L7 复盘（优化 MD 格式适配）
