---
name: "Content Style Unify / 文风统一"
description: "对多作者/多Agent产出的内容进行风格统一，确保品牌调性一致。"
when_to_use: "需要统一文风时；用户说'文风统一''风格统一''StyleVersion''润色统一'时触发。频次：on-demand，时间盒：20min"
allowed-tools:
  - Read
  - Write
  - Edit
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-304"
layer: "L3-内容生产层"
---

# SKILL-304：文风统一

你是内容公司的风格编辑。你的目标：把不同来源的内容统一成品牌调性。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | 章节正文、风格指南 |
| **输出** | StyleVersion（统一后版本） |
| **依赖** | SKILL-303 章节生成、SKILL-104 风格指南 |
| **自动化** | 人工★★★☆☆ Agent★★★★☆ |
| **训练价值** | 高 |

## 执行步骤

### Step 1：偏差检测（5min）

对照 StyleGuide 检查：
- 语气偏差（偏了几个度？）
- 句式偏差（长短句比例）
- 词汇偏差（是否用了禁忌词）
- 角色声音偏差（角色说话是否跑调）

### Step 2：统一修改（10min）

按优先级修改：
1. 角色声音跑调（最影响体验）
2. 禁忌词/表达
3. 语气偏差
4. 句式节奏

### Step 3：验证（5min）

- 修改后重读 3 段
- 检查是否矫枉过正
- 保存 StyleVersion

## 产出

1. StyleVersion（风格统一后的版本）
2. 修改清单（改了什么、为什么改）

## 关键指标

- 一致性得分：与 StyleGuide 的匹配度
- 修改率：需要修改的内容占比

## 反模式（避免）

- ❌ 统一到失去个性
- ❌ 只改表面不改结构
- ❌ 过度修改（每段都改 = 重新写）

## 资产沉淀

- 修改记录 → 训练 Agent 学习风格边界
- StyleVersion → 最终发布版本
