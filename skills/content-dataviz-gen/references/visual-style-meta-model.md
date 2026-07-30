# 视觉风格元模型：Structure × Render × Palette

> 从 baoyu-skills 的三维/四维/五维体系蒸馏合并为统一框架。
> 6×5×4 = 120种组合，10个preset覆盖95%场景。

## 三维定义

### Structure（信息结构，6种）
来源：baoyu-article-illustrator Type + baoyu-infographic Layout 蒸馏

| Structure | 信息特征 | 典型布局 | 对应脚本 | ← D2 Type |
|-----------|---------|---------|---------|-----------|
| data-impact | 单点冲击数据 | 大数字居中+对比 | cover_composer number-impact | number-impact / screenshot-enhanced |
| comparison | 多维度对比 | 左右/表格/矩阵 | comparison_matrix / vs-compare | comparison |
| progression | 线性递进/流程 | 从左到右/从上到下 | dataviz line / flowchart | line-chart / list / flowchart / timeline |
| hierarchy | 层级/包含 | 树形/冰山/分层 | dataviz bar / funnel | heatmap |
| narrative | 叙事/时间线 | 封面→铺垫→核心→收获→CTA | xhs_card story | scene |
| dense-info | 高密度信息 | bento-grid/模块化 | infographic (AI生成) | infographic |

### Render（视觉渲染，5种）
来源：baoyu 22种Style蒸馏为5种

| Render | 视觉特征 | 字体 | 线条 | ← D2 Style |
|--------|---------|------|------|-----------|
| bold | 高对比+粗线+强色块 | 黑体粗 | 粗直 | bold-graphic |
| technical | 网格+等宽+数据标注 | Mono | 细直 | technical-schematic |
| hand-drawn | 手绘+粉笔+暖色 | 手写体 | 曲线 | hand-drawn-edu |
| craft | 柔和+莫兰迪+纸质 | 衬线 | 柔和 | craft-handmade |
| minimal | 极简+留白+功能 | 无衬线细 | 极少 | minimal |

### Palette（配色，4种）

| Palette | 主色 | 辅色 | 强调色 | 背景 | ← D2 Palette |
|---------|------|------|--------|------|-------------|
| brand-dark | #e9c46a | #ffffff | #e76f51 | #1a1a2e | 品牌深蓝 |
| macaron | #A8D8EA | #B5E5CF | #E8655A | #F5F0E8 | 马卡龙 |
| warm | #ED8936 | #F6AD55 | #A0522D | #FFECD2 | 暖色 |
| neon | #00F5FF | #FF00FF | #FFFF00 | #1A1025 | 霓虹 |

## 10个Preset（覆盖95%场景）

| Preset | S×R×P | 适用场景 | 信号关键词 | ← D2 信号行 |
|--------|-------|---------|-----------|------------|
| 数据冲击 | data-impact × bold × brand-dark | 量化失败/No-Go记录 | 失败,否决,全挂 | 失败/全No-Go/被否 |
| 技术横评 | comparison × technical × brand-dark | AI工具对比 | 横评,对比,VS | 对比/横评/VS |
| 教程清单 | progression × hand-drawn × macaron | how-to/步骤/入门 | 教程,步骤,入门 | 教程/步骤/how-to |
| 叙事卡片 | narrative × craft × warm | 个人成长故事 | 故事,历程,成长 | 故事/成长/历程 |
| 数据报告 | hierarchy × technical × brand-dark | 量化周报/归因 | 报告,归因,因子 | 数据/趋势/曲线 |
| 知识图解 | dense-info × hand-drawn × warm | 概念解释/科普 | 解释,为什么,概念 | 概念/解释/为什么 |
| 流程架构 | progression × technical × brand-dark | 系统架构/API流程 | 架构,流程,系统 | 流程/架构/系统 |
| 时间线 | progression × minimal × brand-dark | 演变/发展历程 | 时间线,演变,历史 | 时间线/演变 |
| 截图标注 | data-impact × technical × brand-dark | IDE实测/工具截图 | 截图,实测,IDE | 截图/实测/IDE |
| 因子热力 | hierarchy × technical × brand-dark | 因子暴露/热力图 | 热力,因子,暴露 | 热力/因子/暴露 |

## 兼容性规则

| 组合 | 兼容? | 说明 |
|------|-------|------|
| narrative × technical | ⚠️ | 叙事型用手绘或craft更佳 |
| dense-info × bold | ⚠️ | 高密度信息用technical更清晰 |
| comparison × craft | ✅ | 柔和对比表适合生活类横评 |
| data-impact × hand-drawn | ❌ | 冲击数据不适合手绘风 |
| hierarchy × hand-drawn | ✅ | 层级图解用手绘增加亲和力 |
| narrative × minimal | ✅ | 极简叙事适合时间线卡片 |
| dense-info × neon | ⚠️ | 高密度+霓虹易视觉过载，仅限前沿科技 |
| comparison × bold | ✅ | 强对比配合粗体有力 |
| progression × craft | ✅ | 柔和流程适合生活类教程 |
| data-impact × neon | ✅ | 冲击数据+霓虹适合赛博/前沿主题 |
| hand-drawn × brand-dark | ✅ | 手绘+深蓝底适合数据驱动的教程 |
| data-impact × craft | ⚠️ | 冲击数据用bold或technical更有效 |

## 使用流程

1. 识别内容信号关键词（参考 content-signal-style-map.md）
2. 通过 D2 的 Type→Structure / Style→Render / Palette代码 桥接列，将信号映射到本模型的三维代码
3. 匹配最接近的 Preset
4. 如 Preset 不完全匹配，从三维中自由组合
5. 检查兼容性规则表，确认组合合理
6. 输出选型结果：`{Preset名称} = {Structure} × {Render} × {Palette}`
7. 写入 prompt 文件（遵循 Prompt-File-First 约定，prompt中使用本模型的英文代码）

## 与其他参考的关系

> 修改本文件时通知 content-signal-style-map.md / SKILL-352 / content-illustrator agent 同步更新。

| 参考 | 关系 |
|------|------|
| content-signal-style-map.md | 信号→Type/Style/Palette 映射表（本模型的上游输入，通过桥接列连接） |
| SKILL-352 SKILL.md | 数据可视化技能，使用本模型确定 Structure/Render/Palette 参数 |
| content-illustrator agent | 配图师，使用本模型确定整体视觉方案 |
