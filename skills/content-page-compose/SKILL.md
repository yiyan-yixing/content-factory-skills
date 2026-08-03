---
name: "content-page-compose"
description: "生成公众号图文排版HTML和着陆页HTML，文章+配图自动排版。当用户说'页面排版''公众号排版''landing page''着陆页''HTML页面'时触发。"
when_to_use: "需要生成完整页面排版时；用户说'公众号排版''landing page''着陆页''HTML页面''图文排版'时触发。频次：on-demand，时间盒：15min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-355"
layer: "L3.5-视觉生产层"
---

# SKILL-355：页面排版

你是内容公司的页面排版师。你的目标：将文章+配图合成为完整的HTML页面。

## 两种页面类型

| 类型 | 输出 | 特点 |
|------|------|------|
| 公众号排版 | 内联CSS HTML | 可粘贴到编辑器，品牌风格统一 |
| 着陆页 | 响应式HTML | 可独立访问，含动画+视频+CTA |

## 品牌色板

| 角色 | 色值 | 用途 |
|------|------|------|
| 主背景 | #1a1a2e → #16213e 渐变 | 页面底色 |
| 高亮标题 | #e9c46a | 主标题、h2标题 |
| 警示/强调 | #e76f51 | 关键数字、CTA按钮、分割线 |
| 正文/副标题 | #ffffff | 正文、副标题、说明文字 |
| 正面/增长 | #2a9d8f | 正面数据（按需） |

## 公众号排版执行步骤

1. 读取文章Markdown + 配图路径
2. 调用 page_composer.py 生成公众号HTML
   ```bash
   python3 biz/content/scripts/page_composer.py \
     --type wechat \
     --article {article_path} \
     --cover {cover_path} \
     --figures {figure_paths} \
     --output biz/content/assets/pages/{article_id}/wechat.html
   ```
3. 验证：HTML可打开 + 配图正确显示 + 品牌风格统一

## 着陆页执行步骤

1. 读取文章内容 + 配图 + 视频（如有）
2. 调用 landing_page_composer.py 生成着陆页HTML
   ```bash
   python3 biz/content/scripts/landing_page_composer.py \
     --article-id {article_id} \
     --title "{title}" \
     --content "{content}" \
     --cover {cover_path} \
     --video {video_path} \
     --figures {figure_paths} \
     --output biz/content/assets/pages/{article_id}/landing.html
   ```
3. 验证：HTML可打开 + 响应式OK + 动画正常 + 配图/视频正确

## 输出规范

| 类型 | 路径模式 | 说明 |
|------|---------|------|
| 公众号HTML | biz/content/assets/pages/{article_id}/wechat.html | 内联CSS，无外部依赖 |
| 着陆页HTML | biz/content/assets/pages/{article_id}/landing.html | 响应式+动画+JS，可独立部署 |

## 质量检查

- [ ] 内联CSS（无外部样式表依赖）
- [ ] 品牌色板统一（深蓝+亮黄+红+白）
- [ ] 配图正确嵌入（base64或相对路径）
- [ ] 公众号HTML可粘贴到微信编辑器
- [ ] 着陆页响应式（手机/平板/桌面）
- [ ] CTA区域清晰可见
