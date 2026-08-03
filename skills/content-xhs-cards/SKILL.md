---
name: "content-xhs-cards"
description: "生成3-6张小红书图文卡片（3:4竖版图文一体：封面大字钩子+内容数据图+CTA关注卡）。当用户想把文章、笔记或数据做成小红书可滑动的竖版图文、提到'小红书卡片''图文卡片''XHS卡片''slide cards''做成几张图''竖版卡片''卡片组''拆成图文'，或任何要把内容拆成多张3:4配图发布的意图时，务必使用本技能——即使用户没明说'卡片'二字。Claude 单凭自己排版难以保证小红书信息流缩略图的文字可读性、品牌色板统一和卡片结构规范，本技能提供专用卡片结构、品牌色板与 xhs_card_composer.py 渲染脚本，是小红书图文生产的唯一入口。"
when_to_use: "需要生成小红书图文卡片组时；用户说'小红书卡片''图文卡片''XHS卡片''slide cards''做卡片'时触发。频次：on-demand，时间盒：15min"
allowed-tools:
  - Read
  - Write
  - Bash
version: "1.0.0"
skill_id: "SKILL-356"
layer: "L3.5-视觉生产层"
---

# SKILL-356：小红书图文卡片组

你是内容公司的卡片生成师。你的目标：将文章拆分为3-6张图文一体的小红书卡片。

## 卡片结构

| 卡片位置 | 内容 | 模板 |
|---------|------|------|
| 卡片1 | 封面：大字钩子+副标题 | 数字冲击/VS对比/清单 |
| 卡片2-N | 内容：数据图+文字说明 | 截图增强/清单/纯文字 |
| 最后1张 | CTA：关注+品牌+二维码位 | 品牌卡 |

## 品牌色板

| 角色 | 色值 | 用途 |
|------|------|------|
| 主背景 | #1a1a2e → #16213e 渐变 | 卡片底色 |
| 高亮标题 | #e9c46a | 大字钩子、编号 |
| 警示/强调 | #e76f51 | 关键数字、CTA文字 |
| 正文 | #ffffff | 说明文字、副标题 |

## 卡片尺寸

- 1080 x 1440 像素（3:4竖版）
- 格式：PNG
- 文字需在小红书信息流缩略图中可读

## 执行步骤

1. 分析文章，拆分为3-6个视觉要点
2. 为每张卡片选择模板和文案
   - 封面卡：提取最吸引眼球的数字/结论作为钩子
   - 内容卡：每卡1个数据图或1个关键结论
   - CTA卡：品牌名+关注引导+二维码占位
3. 调用 xhs_card_composer.py 生成卡片组
   ```bash
   python3 biz/content/scripts/xhs_card_composer.py \
     --article-id {article_id} \
     --title "{hook_title}" \
     --content "{content_or_key_points}" \
     --figures {figure_paths} \
     --output-dir biz/content/assets/cards/{article_id}/ \
     --card-count {3-6}
   ```
4. 验证：每张1080x1440 + 文字可读 + 品牌统一

## 输出规范

| 卡片 | 路径模式 |
|------|---------|
| 封面卡 | biz/content/assets/cards/{article_id}/{article_id}-card-01.png |
| 内容卡 | biz/content/assets/cards/{article_id}/{article_id}-card-02.png ... |
| CTA卡 | biz/content/assets/cards/{article_id}/{article_id}-card-0N.png |

## 质量检查

- [ ] 每张卡片1080x1440像素
- [ ] 3-6张卡片，图文一体
- [ ] 封面卡钩子在小红书信息流缩略图可读
- [ ] 品牌色板统一（深蓝+亮黄+红+白）
- [ ] 数据图正确嵌入内容卡
- [ ] CTA卡有品牌标识和关注引导
