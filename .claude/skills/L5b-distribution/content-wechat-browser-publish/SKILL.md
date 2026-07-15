---
name: "Content WeChat Browser Publish / 微信浏览器发布"
description: "通过浏览器 CDP 将文章保存为微信草稿。发布需人工手机扫码确认——这是平台限制。"
when_to_use: "需要发布文章到微信公众号时；用户说'发到微信''微信发布''公众号发布''公众号草稿'时触发。频次：on-demand，时间盒：8min/article"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-554"
layer: "L5b-发行执行层"
---

# SKILL-554：微信浏览器发布

你是内容公司的微信公众号发布执行者。你的目标：通过浏览器 CDP 将文章保存为微信草稿，然后提示人工手机确认发布。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | ArticleID + 微信内容文件 |
| **输出** | WechatPostResult（草稿状态 + 草稿 ID + 人工发布提示） |
| **依赖** | Chrome CDP 运行 + 用户已登录 mp.weixin.qq.com |
| **自动化** | 人工★★★☆☆ Agent★★☆☆☆（半自动：AI 创建草稿，人工确认发布） |
| **训练价值** | 低（机械执行 + 人工确认） |

## 输入字段

```json
{
  "article_id": "文章 ID，如 T1-003",
  "dry_run": "是否仅预览，默认 false",
  "draft_only": "微信默认就是草稿模式——此参数对微信无额外效果"
}
```

## 输出字段

```json
{
  "success": "boolean — 草稿保存是否成功",
  "platform": "wechat-browser",
  "article_id": "文章 ID",
  "ids": ["草稿 ID 或 URL"],
  "details": "草稿保存结果 + ⚠️ 人工发布提示"
}
```

## 执行步骤

### Step 1：读取并准备内容（1min）

读取 `biz/content/distribution/wechat/{article_id}-wechat.md`。提取标题（输入到标题字段）。准备正文（去掉 H1 标题行，标题单独输入）。

### Step 2：dry-run 预览（1min）

如果 dry_run=true，输出标题和字数预览，提示微信只能到草稿，不连接浏览器。

### Step 3：连接 Chrome CDP 创建草稿（6min）

1. 连接 Chrome CDP (127.0.0.1:9222)
2. 打开 mp.weixin.qq.com
3. 点击 "图文信息" 或 "新建图文" 创建新文章
4. 输入标题（keyboard.type）
5. 定位编辑器 iframe，切换到 iframe 内容
6. 输入正文（分段落 keyboard.type）
   - ⚠️ 外部图片被过滤，需上传到微信图床
   - ⚠️ 外部链接被过滤，只能在"阅读原文"字段放 URL
7. 点击 "保存" 保存草稿
8. 获取草稿 ID

### Step 4：提示人工发布（0min）

草稿保存后，输出 ⚠️ 提醒：
```
⚠️ 微信草稿已保存！
发布需要人工操作：
1. 打开微信手机端
2. 进入「订阅号消息」→ 找到草稿
3. 确认发布
```

### 关键注意事项

- 微信个人订阅号 2025.7 后失去 API 发布权限 — **只能保存草稿**
- 发布需人工手机扫码确认 — AI 无法自动发布
- 外部图片被过滤 — 应使用微信图床或 md2wechat 转换
- 外部链接被过滤 — 只能放在"阅读原文"字段
- 编辑器在 iframe 中 — 需先定位 iframe 再操作
- draft_only 参数对微信无意义 — 微信默认就是草稿

## 产出

1. WechatPostResult — 草稿保存结果 JSON
2. 草稿 ID — 可用于后续管理和查询
3. 人工发布提示 — 提醒用户完成最后一步

## 关键指标

- 草稿保存成功率：≥ 90%
- 标题输入准确率：100%
- 正文输入完整性：≥ 90%（图片/链接需人工补充）

## 反模式（避免）

- ❌ 试图自动发布 — 微信需要人工手机确认，无法绕过
- ❌ 直接粘贴含外部图片的 HTML — 图片会被过滤
- ❌ 在正文放外部链接 — 链接会被过滤，放"阅读原文"字段
- ❌ 不处理 iframe 直接操作页面 — 找不到编辑器元素
- ❌ 期望 draft_only=false 能自动发布 — 微信始终只到草稿

## 资产沉淀

- WechatPostResult → PublishReport（草稿状态汇总）
- 图片/链接过滤问题记录 → L7 复盘（优化 md2wechat 转换策略）
