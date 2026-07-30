---
name: "Content XHS Browser Publish / 小红书浏览器CDP发布"
description: "通过Chrome CDP自动发布笔记到小红书创作者中心。图片优先平台，需至少1张图片。用 /content-xhs-browser-publish 调用。"
skill_id: SKILL-555
version: "1.0.0"
---

# SKILL-555: 小红书浏览器CDP发布

## 概述

通过 Playwright CDP 连接已登录的 Chrome 浏览器，自动发布笔记到小红书创作服务平台 (creator.xiaohongshu.com)。

**核心差异**: 小红书是**图片优先**平台，必须上传至少1张图片才能发布。这与现有的4个纯文字CDP发布器（X/Substack/知乎/微信）完全不同。

## 前置条件

1. Chrome 已启动并开启 CDP：
   ```bash
   open -a 'Google Chrome' --args \
     --remote-debugging-port=9222 \
     --user-data-dir=/tmp/chrome-debug-profile
   ```
2. 在该 Chrome 中已登录 xiaohongshu.com（手机扫码登录）
3. 小红书无需翻墙（国内直接访问）

## 使用方式

### CLI

```bash
# 发布指定文章（自动查找图片）
python -m biz.content.publish --article XHS-01 --platform xhs-browser

# 仅保存草稿
python -m biz.content.publish --article XHS-01 --platform xhs-browser --draft-only

# 预览（dry run）
python -m biz.content.publish --article XHS-01 --platform xhs-browser --dry-run

# 直接指定文件
python -m biz.content.publish --file biz/content/pipeline/xhs-launch/XHS-01-sharpe-no-go/article.md --platform xhs-browser
```

### Python API

```python
from biz.content.publish import XhsBrowserPublisher

xhs = XhsBrowserPublisher()
result = xhs.publish("XHS-01")
# result = {"success": True, "platform": "xhs-browser", "ids": [...], "details": "..."}
```

## 发布流程

```
1. CDP 连接 Chrome
2. 导航到 creator.xiaohongshu.com/publish/publish
3. 上传图片（封面图优先，然后内容卡片图）
   └─ 文件选择器 / file input / 拖放区
4. 输入标题（≤20字）
5. 输入正文（逐行 typing）
6. 添加话题标签（从正文中提取 #话题 或使用默认）
7. 点击"发布" 或 "存草稿"
8. 获取发布后 URL
```

## 图片查找优先级

```
1. cover.png / cover.jpg — 封面图（必须第一张，XHS用首图做封面）
2. cards/card-01.png, card-02.png... — 卡片图
3. figures/*.png — 数据可视化图
4. 目录下其他 PNG/JPG — 补充图片
```

## 内容来源

| 优先级 | 路径 | 说明 |
|--------|------|------|
| 1 | `distribution/xiaohongshu/{article_id}-xiaohongshu.md` | 最终发布版 |
| 2 | `pipeline/xhs-launch/{article_id}-*/article.md` | 生产稿件 |
| 3 | `distribution/xiaohongshu/` 通用 | 回退 |

## DOM 选择器（需定期验证）

> 小红书创作者中心是 React SPA，DOM 结构可能随版本更新变化。
> 如发布失败，需在 Chrome DevTools 中重新检查选择器。

| 元素 | 选择器 | 备注 |
|------|--------|------|
| 图片上传 | `input[type="file"]` | 隐藏 file input |
| 上传触发 | `.upload-wrapper, [class*="upload"]` | 点击区域 |
| 标题输入 | `input[placeholder*="标题"], .title-input input` | ≤20字 |
| 正文编辑 | `[contenteditable="true"], .ql-editor` | 富文本编辑器 |
| 话题触发 | `button:has-text("#"), [class*="topic"]` | 话题标签 |
| 话题输入 | `input[placeholder*="话题"]` | 搜索话题 |
| 话题建议 | `[class*="topic-suggestion"]` | JS click |
| 发布按钮 | `button:has-text("发布")` | 需图片+标题 |
| 草稿按钮 | `button:has-text("存草稿")` | 可选 |

## 关键约束

- **图片必须**: 无图无法发布（发布按钮disabled）
- **标题≤20字**: 超出会被截断
- **正文无富格式**: 支持 emoji 和换行，不支持 Markdown 渲染
- **话题标签可选但推荐**: 增加发现概率
- **发布后30分钟互动**: 前3分钟窗口最大化（参考冷启动方案）
- **发布时段**: 20:00-22:00 最佳（参考冷启动方案）

## 与其他CDP发布器的差异

| 特性 | X/Substack/知乎/微信 | 小红书 |
|------|---------------------|--------|
| 内容类型 | 纯文字（Markdown→粘贴） | 图片+文字 |
| 图片上传 | 不支持 | 必须（file chooser） |
| 编辑器 | Draft.js / ProseMirror | contenteditable |
| 标题限制 | 无限制/长标题 | ≤20字 |
| 话题标签 | 无/可选 | 推荐添加 |
| 发布依赖 | 文字粘贴即可 | 需等待图片上传完成 |

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| 图片上传失败 | DOM 选择器变化 | Chrome DevTools 检查新选择器 |
| 发布按钮 disabled | 无图片或无标题 | 确保图片路径正确 |
| 标题被截断 | 超过20字 | 脚本自动截断到20字 |
| CDP连接失败 | Chrome未启动/端口不对 | 检查 --remote-debugging-port=9222 |
| 登录过期 | Cookie过期 | 在Chrome中重新扫码登录 |

## 代码路径

| 文件 | 说明 |
|------|------|
| `biz/content/publish/xhs_browser_publisher.py` | 核心发布逻辑 |
| `biz/content/publish/browser_cdp_base.py` | CDP 基类 |
| `biz/content/publish/cli.py` | CLI入口（含 xhs-browser） |
| `biz/content/publish/__init__.py` | Python API 入口 |

## 参考文档

- 小红书冷启动方案: `biz/content/pipeline/xiaohongshu-cold-start-plan.md`
- 小红书系列策划: `biz/content/pipeline/xiaohongshu-series-plan.md`
- CDP发布能力扫描: `biz/content/.claude/blackboard/optimization-cdp-status.md`
- 图片视频发布方案: `biz/content/.claude/blackboard/optimization-image-video-publish.md`
