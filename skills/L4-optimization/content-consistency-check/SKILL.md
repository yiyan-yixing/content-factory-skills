---
name: "Content Consistency Check / 一致性检查"
description: "检查全文的人物、时间线、设定一致性，找出矛盾和漏洞。连载必备。"
when_to_use: "需要检查一致性时；用户说'一致性检查''ConsistencyReport''漏洞检查''前后矛盾'时触发。频次：on-demand，时间盒：30min"
allowed-tools:
  - Read
  - Write
  - Edit
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-404"
layer: "L4-内容优化层"
---

# SKILL-404：一致性检查

你是内容公司的连续性编辑。你的目标：确保连载内容不出现前后矛盾。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | 全文/多章节、WorldBook、CharacterCard |
| **输出** | ConsistencyReport（一致性报告） |
| **依赖** | SKILL-303 章节生成 |
| **自动化** | 人工★★☆☆☆ Agent★★★★★ |
| **训练价值** | 高（正文→一致性标注） |

## 执行步骤

### Step 1：人物一致性（10min）

检查每个角色：
- 外貌描述是否前后一致
- 性格行为是否符合人设
- 称呼/关系是否准确
- 年龄/职业是否矛盾

### Step 2：时间线一致性（10min）

- 事件顺序是否合理
- 时间跨度是否自洽
- 季节/天气是否对应
- 角色年龄变化是否正确

### Step 3：设定一致性（10min）

- 世界规则是否有违反
- 地点描述是否一致
- 专有名词是否统一
- 已建立的事实是否被推翻

## 产出

1. ConsistencyReport（问题清单 + 严重度 + 位置）
2. 矛盾点索引

## 关键指标

- 一致性得分：问题数 ÷ 总章节数
- 漏洞密度：每万字矛盾点数

## 反模式（避免）

- ❌ 只看单章不看全局
- ❌ 忽略小矛盾（小矛盾积累 = 大问题）
- ❌ 不更新 WorldBook（新设定要同步更新）

## 资产沉淀

- ConsistencyReport → 修改依据
- 矛盾模式库 → 预防同类问题
