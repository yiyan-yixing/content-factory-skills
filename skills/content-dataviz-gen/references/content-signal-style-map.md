# Content Signal → 视觉风格选型表

> 从 baoyu-skills 三源蒸馏：baoyu-article-illustrator Content Type → Preset Recommendations、baoyu-cover-image auto-selection.md 信号→维度映射、baoyu-xhs-images Content Type → Style+Layout 映射。
> 按一言一行内容线定制：量化/AI工具/个人成长/博物馆/城市/读书。

## 信号关键词检测

| 信号 | 配图Type | Type→Structure | 推荐Style | Style→Render | 推荐Palette | Palette代码 | 适用平台 |
|-------|---------|---------------|-----------|-------------|------------|------------|---------|
| 失败/全No-Go/被否 | number-impact | data-impact | bold-graphic | bold | 品牌深蓝 | brand-dark | XHS+微信 |
| 对比/横评/VS | comparison | comparison | technical-schematic | technical | 品牌深蓝 | brand-dark | XHS+知乎 |
| 教程/步骤/how-to | list | progression | hand-drawn-edu | hand-drawn | 马卡龙 | macaron | XHS |
| 数据/趋势/曲线 | line-chart | progression | technical-schematic | technical | 品牌深蓝 | brand-dark | 全平台 |
| 概念/解释/为什么 | infographic | dense-info | hand-drawn-edu | hand-drawn | 暖色 | warm | 微信+知乎 |
| 截图/实测/IDE | screenshot-enhanced | data-impact | technical-schematic | technical | 品牌深蓝 | brand-dark | XHS |
| 故事/成长/历程 | scene | narrative | craft-handmade | craft | 暖色 | warm | XHS+微信 |
| 流程/架构/系统 | flowchart | progression | technical-schematic | technical | 品牌深蓝 | brand-dark | 微信+知乎 |
| 时间线/演变 | timeline | progression | minimal | minimal | 品牌深蓝 | brand-dark | 全平台 |
| 热力/因子/暴露 | heatmap | hierarchy | technical-schematic | technical | 品牌深蓝 | brand-dark | 知乎 |

> Type→Structure / Style→Render / Palette代码 三列是与 visual-style-meta-model.md 的术语桥接。
> prompt 文件中统一使用 meta-model 的 Structure/Render/Palette 英文代码。

## Type 定义

| Type | 说明 | 数据图脚本 | → Structure |
|------|------|-----------|------------|
| number-impact | 大数字+冲击文字 | cover_composer.py --template number-impact | data-impact |
| comparison | 左右对比/横评表 | comparison_matrix.py / cover_composer.py --template vs-compare | comparison |
| list | 编号清单 | cover_composer.py --template list | progression |
| line-chart | 折线/净值曲线 | dataviz_gen.py --type line | progression |
| infographic | 信息图布局 | dataviz_gen.py (bar/pie/funnel/heatmap) | dense-info |
| screenshot-enhanced | 截图+标注 | cover_composer.py --template screenshot-enhanced | data-impact |
| scene | 场景概念图 | AI生成(FLUX) + Pillow文字叠加 | narrative |
| flowchart | 流程/架构图 | AI生成 或 手写SVG | progression |
| timeline | 时间线 | dataviz_gen.py --type line (变体) | progression |
| heatmap | 热力图/因子暴露图 | dataviz_gen.py --type heatmap | hierarchy |

## Style 定义（从baoyu 22种蒸馏为5种）

| Style | → Render | 原始baoyu对应 | 色板特征 | 适用场景 |
|-------|---------|-------------|---------|---------|
| bold-graphic | bold | bold-graphic + corporate-memphis | 高对比+粗线+强色块 | 数据冲击、失败叙事 |
| technical-schematic | technical | technical-schematic + pop-laboratory | 网格+等宽字体+数据标注 | 横评、流程、架构 |
| hand-drawn-edu | hand-drawn | hand-drawn-edu + chalkboard | 手绘风+粉笔+暖色 | 教程、科普、入门 |
| craft-handmade | craft | craft-handmade + morandi-journal | 柔和+莫兰迪+纸质 | 故事、成长、体验 |
| minimal | minimal | minimal + ikea-manual | 极简+大量留白+功能导向 | 时间线、清单、对比 |

## Palette 定义

| Palette | 代码 | 色值 | 适用 |
|---------|------|------|------|
| 品牌深蓝 | brand-dark | #1a1a2e + #e9c46a + #e76f51 + #ffffff | 量化/技术/数据 |
| 马卡龙 | macaron | #F5F0E8 + #A8D8EA + #B5E5CF + #E8655A | 教程/入门/生活 |
| 暖色 | warm | #FFECD2 + #ED8936 + #F6AD55 + #A0522D | 故事/成长/体验 |
| 霓虹 | neon | #1A1025 + #00F5FF + #FF00FF + #FFFF00 | 科技/赛博/前沿 |

## 按内容线快速选型

> 以下默认值由信号关键词表推导，修改信号映射时同步更新。

| 内容线 | 默认Style(Render) | 默认Palette | 高频Type(→Structure) | 备注 |
|--------|-------------------|------------|---------------------|------|
| 量化交易 | technical-schematic(technical) | 品牌深蓝(brand-dark) | line-chart→progression / heatmap→hierarchy / number-impact→data-impact | 数据驱动，品牌色板全覆盖 |
| AI工具 | technical-schematic(technical) | 品牌深蓝(brand-dark) | comparison / flowchart→progression / screenshot-enhanced→data-impact | 横评+架构图为主 |
| 个人成长 | craft-handmade(craft) | 暖色(warm) | scene→narrative / timeline→progression / list→progression | 叙事为主，柔和质感 |
| 博物馆/展览 | craft-handmade(craft) | 暖色(warm) | scene→narrative / timeline→progression / infographic→dense-info | 场景感+时间线 |
| 城市/旅行 | craft-handmade(craft) | 暖色(warm) | scene→narrative / list→progression / timeline→progression | 场景+清单 |
| 读书/知识 | hand-drawn-edu(hand-drawn) | 马卡龙(macaron) | infographic→dense-info / list→progression / comparison | 知识图解为主 |
