# 内容生产工厂

**[English](./README_EN.md)** | 中文

> Claude Code 技能集合 — 内容工厂 8 层角色 Agent + 31 个核心技能 + 三层记忆 + 协作白板 + 质疑协议。
> 专为「用最少人数跑通 **战略 → 设定 → 生产 → 复盘** 闭环」的内容团队打造。标准 `.claude/` 格式。

## 30 秒上手

```bash
# 1. 创建新项目
mkdir my-novel-project && cd my-novel-project

# 2. 一键安装 + 自动初始化（回答几个问题，工厂就是你的了）
curl -fsSL https://raw.githubusercontent.com/yiyan-yixing/content-factory-skills/main/install.sh | bash

# 3. 启动 Claude Code，你的内容工厂已就绪
claude
@主编 帮我定第一部作品的选题和目标读者
@设定师 构建世界观和人物
```

> 🎯 安装完成后，你将拥有：8 层 Agent 角色、31 个技能、三层记忆系统、共享白板、质疑协议 — 一家完整的内容生产工厂框架。

## 架构

```
L0 战略层（3 技能）   用户画像 → 情绪洞察 → 市场选题
       ↓
L1 设定层（4 技能）   世界观 → 人物 → 关系 → 风格
       ↓
L2 剧本层（4 技能）   故事 → 长线 → 爆点 → 连载节奏
       ↓
L3 生产层（4 技能）   场景 → 对话 → 章节 → 文风统一
       ↓
L4 审稿层（4 技能）   结构审查 → 情绪强化 → 节奏优化 → 一致性检查
       ↓
L5 运营层（4 技能）   读者转化 → 社群 → 留存 → 传播
       ↓
L6 商务层（4 技能）   会员 → 付费墙 → 产品化 → IP运营
       ↓
L7 复盘层（4 技能）   反馈收集 → 复盘 → 技能优化 → 经验沉淀
       ↓
                  反馈闭环 → 回到 L0
```

---

## 目录结构

```
content-factory-skills/          # 仓库根目录
├── skills/                      #   31 个技能（标准 SKILL.md 格式）
│   ├── L0-strategic/            #     战略层（3 技能）
│   ├── L1-ip/                   #     设定层（4 技能）
│   ├── L2-planning/             #     剧本层（4 技能）
│   ├── L3-production/           #     生产层（4 技能）
│   ├── L4-optimization/         #     审稿层（4 技能）
│   ├── L5-growth/               #     运营层（4 技能）
│   ├── L6-business/             #     商务层（4 技能）
│   └── L7-learning/             #     复盘层（4 技能）
│
├── agents/                      #   8 层角色子代理（通过 @角色名 调用）
│   ├── L0-chief-editor.md       #     主编
│   ├── L1-world-builder.md      #     设定师
│   ├── L2-screenwriter.md       #     编剧
│   ├── L3-writer.md             #     写手
│   ├── L4-reviewer.md           #     审稿
│   ├── L5-operator.md           #     运营
│   ├── L6-business.md           #     商务
│   ├── L7-review-officer.md     #     复盘官
│   ├── WORKFLOW.md              #     内容闭环 DAG 流程
│   └── challenge-protocol.md   #     质疑协议
│
├── memory/                      #   三层记忆系统
│   ├── core/                    #     常驻记忆（每 session 加载）
│   │   ├── tech-stack.md        #       技术栈
│   │   ├── architecture.md      #       架构决策
│   │   └── project-context.md   #       项目上下文
│   ├── archival/                #     长期记忆（按需读取）
│   │   ├── decisions/           #       决策归档
│   │   ├── lessons/             #       经验教训
│   │   └── user-research/       #       读者调研
│   └── recall/                  #     历史会话（按需检索）
│
├── blackboard/                  #   Agent 共享白板
│   ├── current-sprint.md        #     当前迭代状态
│   ├── open-questions.md        #     待解决问题
│   ├── challenges.md            #     质疑记录
│   └── decisions-log.md         #     决策日志
│
├── evals/                       #   效果评估体系
├── profiles/                    #   垂直落地配置包
│   └── web-novel-factory/       #     网文工厂
├── examples/                    #   使用示例
│   └── novel-writing-flow.md    #     小说创作全流程
│
├── CLAUDE.md.template           #   记忆入口模板
├── install.sh                   #   一键安装脚本
└── init.sh                      #   交互式初始化脚本
```

### 安装后的用户项目结构

```
your-project/
└── .claude/                    # Claude Code 自动发现
    ├── skills/                 #   31 个 Skills
    ├── agents/                 #   8 个 Agent + WORKFLOW + 质疑协议
    ├── memory/                 #   三层记忆系统
    │   ├── core/               #     （init.sh 写入你的工厂信息）
    │   ├── archival/           #     决策归档、经验教训
    │   └── recall/             #     历史会话
    ├── blackboard/             #   共享白板
    ├── evals/                  #   效果评估体系
    ├── examples/               #   使用示例
    ├── profiles/               #   垂直落地配置
    ├── CLAUDE.md               #   记忆入口 (@import core)
    └── init.sh                 #   初始化脚本
```

---

## 安装

### 一键安装（推荐）

```bash
curl -fsSL https://raw.githubusercontent.com/yiyan-yixing/content-factory-skills/main/install.sh | bash
```

或克隆后本地安装：

```bash
git clone https://github.com/yiyan-yixing/content-factory-skills.git
cd content-factory-skills && bash install.sh /path/to/your/project
```

#### 安装参数

| 参数 | 说明 |
|------|------|
| `--init` | 安装后自动运行初始化（回答几个问题，一键把框架变成你的工厂） |
| `--skip-init` | 只安装框架，跳过初始化（稍后手动运行 `bash .claude/init.sh`） |
| 无参数 | **默认行为**：安装后自动初始化（同 `--init`） |

```bash
# 只装框架，稍后手动初始化
bash install.sh /path/to/project --skip-init

# 非交互模式初始化（适合 CI/自动化）
COMPANY_NAME="我的工作室" CONTENT_DIRECTION="都市成长小说" TARGET_READER="20-28岁女性" \
  HYPOTHESIS="读者需要逆袭+闺蜜情的故事" ADVANTAGE="AI辅助高产出" \
  PRODUCT_POSITIONING="日更3000字都市连载" PLATFORM="番茄小说" \
  bash .claude/init.sh
```

---

## 角色子代理（8 层）

通过 `@角色名` 调用，每个角色拥有完整的职责、上下游、产出和可用技能。

```
┌─────────────────────────────────────────────────────────┐
│                      主编 · L0                           │
│    方向 · 画像 · 选题 · 情绪策略                         │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ 设定师    │ 编剧     │ 写手     │ 审稿     │ 运营        │
│ · L1     │ · L2     │ · L3    │ · L4     │ · L5        │
│ 世界观    │ 故事弧线  │ 章节生产 │ 结构审查  │ 读者转化    │
│ 人物关系  │ 伏笔爆点  │ 文风统一 │ 情绪强化  │ 社群传播    │
├──────────┼──────────┤          │          ├─────────────┤
│ 商务      │ 复盘官   │          │          │             │
│ · L6     │ · L7     │          │          │             │
│ 付费会员  │ 反馈收集  │          │          │             │
│ IP运营    │ 经验沉淀  │          │          │             │
└──────────┴──────────┘          └──────────┴─────────────┘
```

| 角色 | 调用 | 核心使命 | 负责技能 |
|------|------|----------|----------|
| **主编** | `@主编` | 决定写给谁、写什么、打什么情绪 | 用户画像、情绪洞察、市场选题 |
| **设定师** | `@设定师` | 构建世界观、人物、关系、风格 | 世界观构建、人物设计、角色关系、风格指南 |
| **编剧** | `@编剧` | 设计故事、埋伏笔、设爆点、控节奏 | 故事设计、长线规划、爆点设计、连载节奏 |
| **写手** | `@写手` | 场景、对话、章节、文风落地 | 场景设计、对话写作、章节生成、文风统一 |
| **审稿** | `@审稿` | 结构审查、情绪强化、节奏、一致性 | 结构审查、情绪强化、节奏优化、一致性检查 |
| **运营** | `@运营` | 读者转化、社群、留存、传播 | 读者转化、社群设计、留存设计、传播设计 |
| **商务** | `@商务` | 会员、付费墙、产品化、IP运营 | 会员设计、付费墙设计、产品化、IP运营 |
| **复盘官** | `@复盘官` | 反馈收集、复盘、技能优化、经验沉淀 | 反馈收集、内容复盘、技能优化、经验沉淀 |

### 内容闭环流程

```
@主编 定义画像+选题 → @设定师 构建设定 → @编剧 设计故事 → @写手 生产章节
  → @审稿 审查优化 → @运营 推向读者 → @商务 商业变现 → @复盘官 闭环反馈
                                                                    ↓
                           @主编 战略校准 ← @复盘官 复盘报告 ←─────┘
```

详见 `agents/WORKFLOW.md`。

---

## 技能一览（31 个）

| 层级 | 智能体 | 技能 | SKILL ID |
|------|--------|------|----------|
| L0 战略 | 主编 | 用户画像 | SKILL-001 |
| | | 情绪洞察 | SKILL-002 |
| | | 市场选题 | SKILL-003 |
| L1 设定 | 设定师 | 世界观构建 | SKILL-101 |
| | | 人物设计 | SKILL-102 |
| | | 角色关系 | SKILL-103 |
| | | 风格指南 | SKILL-104 |
| L2 剧本 | 编剧 | 故事设计 | SKILL-201 |
| | | 长线规划 | SKILL-202 |
| | | 爆点设计 | SKILL-203 |
| | | 连载节奏 | SKILL-204 |
| L3 生产 | 写手 | 场景设计 | SKILL-301 |
| | | 对话写作 | SKILL-302 |
| | | 章节生成 | SKILL-303 |
| | | 文风统一 | SKILL-304 |
| L4 审稿 | 审稿 | 结构审查 | SKILL-401 |
| | | 情绪强化 | SKILL-402 |
| | | 节奏优化 | SKILL-403 |
| | | 一致性检查 | SKILL-404 |
| L5 运营 | 运营 | 读者转化 | SKILL-501 |
| | | 社群设计 | SKILL-502 |
| | | 留存设计 | SKILL-503 |
| | | 传播设计 | SKILL-504 |
| L6 商务 | 商务 | 会员设计 | SKILL-601 |
| | | 付费墙设计 | SKILL-602 |
| | | 产品化 | SKILL-603 |
| | | IP 运营 | SKILL-604 |
| L7 复盘 | 复盘官 | 反馈收集 | SKILL-701 |
| | | 内容复盘 | SKILL-702 |
| | | 技能优化 | SKILL-703 |
| | | 经验沉淀 | SKILL-704 |

---

## 快速出作品流程（1 周）

> 内容工厂铁律：没有可发布的章节，就没有读者。

```
Day 1:   @主编 定画像+选题 + @设定师 出世界观+人物
Day 2:   @设定师 出关系+风格 + @编剧 出故事弧线+爆点
Day 3-4: @写手 批量产章节（5-10 章）
Day 5:   @审稿 全链路审查 + @运营 出转化+传播方案
Day 6-7: @商务 出付费墙+会员 + 发布上线 + 开始收集反馈
```

详见 `agents/WORKFLOW.md` 的快速出作品流程。

---

## 依赖关系（DAG）

```
SKILL-001 ──→ SKILL-002 ──→ SKILL-003
                                  │
    ┌─────────────────────────────┘
    ↓
SKILL-101 ──→ SKILL-102 ──→ SKILL-103 ──→ SKILL-104
                                              │
    ┌─────────────────────────────────────────┘
    ↓
SKILL-201 ──→ SKILL-202 ──→ SKILL-203 ──→ SKILL-204
                                              │
    ┌─────────────────────────────────────────┘
    ↓
SKILL-301 ──→ SKILL-302 ──→ SKILL-303 ──→ SKILL-304
                                              │
    ┌─────────────────────────────────────────┘
    ↓
SKILL-401 ──→ SKILL-402 ──→ SKILL-403 ──→ SKILL-404
                                              │
    ┌─────────────────────────────────────────┘
    ↓
SKILL-501 ──→ SKILL-502 ──→ SKILL-503 ──→ SKILL-504
                                              │
    ┌─────────────────────────────────────────┘
    ↓
SKILL-601 ──→ SKILL-602 ──→ SKILL-603 ──→ SKILL-604
                                              │
    ┌─────────────────────────────────────────┘
    ↓
SKILL-701 ──→ SKILL-702 ──→ SKILL-703 ──→ SKILL-704
    ↑                                       │
    └───────────── 反馈闭环 ────────────────┘
```

---

## Agent 优先级

| 优先级 | 技能 | 说明 |
|--------|------|------|
| ★★★★★ 先 Agent 化 | 场景、对话、章节、一致性 | 规则明确、输入输出清晰 |
| ★★★★ 第二批 | 角色、关系、增长、审查 | 需要一定人工校验 |
| ★★★ 长期人工 | 用户洞察、世界观、战略 | 需要人类判断力和创造力 |

---

## 三层记忆系统

| 层级 | 路径 | 加载方式 | 内容 |
|------|------|----------|------|
| **Core（常驻）** | `.claude/memory/core/` | CLAUDE.md @import，每 session 自动加载 | 技术栈、架构决策、项目上下文 |
| **Archival（长期）** | `.claude/memory/archival/` | Agent 需要时用 Read 读取 | 决策归档、经验教训、读者调研 |
| **Recall（历史）** | `.claude/memory/recall/` | 会话摘要 | 历史对话、自动学习 |

## 共享白板

| 文件 | 用途 | 维护者 |
|------|------|--------|
| `.claude/blackboard/current-sprint.md` | 当前迭代目标、任务分配、进度 | @主编 |
| `.claude/blackboard/open-questions.md` | 待解决问题 | 任何 Agent |
| `.claude/blackboard/challenges.md` | 质疑记录 | 协调者 |
| `.claude/blackboard/decisions-log.md` | 决策日志索引 | @主编 |

## 质疑协议

@主编 出选题 → @设定师 质疑设定可行性 + @编剧 质疑故事可展开性
@写手 出章节 → @审稿 质疑一致性和情绪强度
@商务 出付费墙 → @运营 质疑读者体验

详见 `agents/challenge-protocol.md`。

---

## 垂直落地 Profile

通用框架 + 垂直落地配置包。`profiles/` 下提供针对特定内容场景的具体化参考：

- `profiles/web-novel-factory/` — **网文工厂**：起点/番茄/晋江连载，日更模式，付费墙+IP孵化

做自媒体短文/剧本/漫画脚本可仿照此结构做自己的 profile。

---

## 与 skills 通用框架的关系

| 维度 | `skills`（通用框架） | `content-factory-skills`（领域特化） |
|------|---------------------|--------------------------------------|
| 角色 | 跨领域通用（CEO/PM/Dev/QA...） | 内容领域专属（主编/设定师/编剧/写手...） |
| 技能 | 跨领域通用（PRD/代码审查/记账...） | 内容领域专属（31 个 content-* 技能） |
| 基础设施 | memory/blackboard/evals（出处的） | 同构复用 |
| WORKFLOW | 通用产品闭环 | 内容闭环（战略→设定→生产→复盘） |
| profiles | — | ✅ 垂直配置包（网文/自媒体/剧本...） |

**边界规则**：任何内容团队都需要的放 `content-factory-skills`，任何软件公司都需要的放 `skills`。

---

## License

CC BY-SA 4.0 — 欢迎借鉴，请注明出处

## 版本

- V0.4 — 2026-06-18 — 补齐基础设施：memory/blackboard/evals/profiles/install.sh/init.sh/WORKFLOW.md/质疑协议
- V0.3 — 2026-06-18 — 角色重命名：主编/设定师/编剧/写手/审稿/运营/商务/复盘官
- V0.2 — 2026-06-17 — 31 技能 × 8 层 × 完整闭环
