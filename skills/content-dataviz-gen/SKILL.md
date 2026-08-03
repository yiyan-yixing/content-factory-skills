---
name: "content-dataviz-gen"
description: "用matplotlib脚本化生成数据可视化图，品牌色板统一。当用户说'数据图''图表''数据可视化''dataviz''matplotlib出图'时触发。"
when_to_use: "需要生成数据可视化图时；用户说'做数据图''画图表''数据可视化''matplotlib'时触发。频次：on-demand，时间盒：15min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.1.0"
skill_id: "SKILL-352"
layer: "L3.5-视觉生产层"
---

# SKILL-352：数据可视化生成

你是内容公司的数据可视化工程师。你的目标：用 matplotlib 生成品牌统一的数据图表。

## 图表类型

| 数据结构 | 推荐图表 | matplotlib方法 |
|---------|---------|---------------|
| 多个数值对比 | 水平柱状图 | ax.barh() |
| 占比/分配 | 饼图 | ax.pie() |
| 趋势/时间序列 | 折线图 | ax.plot() |
| 漏斗转化 | 漏斗图 | 自定义barh |

## 视觉风格选型

生成数据图前，根据内容信号确定 Structure × Render × Palette 组合：
- 信号→风格映射：`references/content-signal-style-map.md`（含 Type→Structure / Style→Render / Palette→代码 桥接列）
- 视觉风格元模型：`references/visual-style-meta-model.md`（定义 Structure/Render/Palette 含义 + 10个Preset + 兼容性规则）

术语说明：content-signal-style-map 使用中文+复合名（Type/Style/Palette中文名），visual-style-meta-model 使用英文代码（Structure/Render/Palette代码）。信号表中的桥接列提供映射。prompt文件统一使用 meta-model 的英文代码。

快速选型：量化/数据类内容默认 `hierarchy × technical × brand-dark`，教程/入门类默认 `progression × hand-drawn × macaron`。

## 执行步骤

### Step 0: 写prompt文件（Prompt-File-First）

1. 在 `prompts/{article_id}/` 目录下创建 prompt 文件：`NN-{type}-{slug}.md`
2. 文件内容包括：
   - 图表类型（Structure，使用 meta-model 英文代码）
   - 渲染风格（Render，使用 meta-model 英文代码）
   - 配色方案（Palette，使用 meta-model 英文代码）
   - 数据来源/数值
   - 标题/标签/注释文案
   - 尺寸和输出路径
3. prompt文件是事实来源，后续所有生成操作以此为准
4. 修改prompt文件后可用 `--regenerate` 重新生成，无需从零开始

### Step 1: 确定图表类型

- 匹配数据结构到推荐图表
- 参考 content-signal-style-map.md 的信号→Type映射，通过桥接列获得 Structure/Render/Palette 代码
- 参考 visual-style-meta-model.md 选择 Preset，检查兼容性规则

### Step 2: 调用脚本生成

- 调用 dataviz_gen.py 脚本（biz/content/scripts/dataviz_gen.py）
- 传入 prompt 文件中的参数
- 如需封面合成，调用 cover_composer.py（biz/content/scripts/cover_composer.py）

### Step 3: 验证产出

- 尺寸正确（封面 1080x1440/1080x1080，数据图按需）
- 中文字体正常渲染
- 色板符合 Prompt-File-First 中指定的 Palette
- 标签/标题可读

## Prompt 文件格式

```markdown
# {article_id} - {NN}-{type}-{slug}

## 视觉选型
- Structure: {data-impact|comparison|progression|hierarchy|narrative|dense-info}
- Render: {bold|technical|hand-drawn|craft|minimal}
- Palette: {brand-dark|macaron|warm|neon}

## 数据
{数据描述或数值}

## 标注
- 标题: {chart_title}
- 标签: {axis_labels}
- 注释: {annotations}

## 输出
- 尺寸: {width}x{height}
- 路径: {output_path}
- 格式: PNG
```
