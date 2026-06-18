#!/bin/bash
# 内容工厂初始化脚本
# 安装框架后，一键初始化你的内容工厂信息
# 用法: bash .claude/init.sh
# 非交互模式: COMPANY_NAME="XX" CONTENT_DIRECTION="XX" bash .claude/init.sh

set -e

# ─── 配置项（支持环境变量预填，交互模式可修改） ───

: "${COMPANY_NAME:=}"
: "${CONTENT_DIRECTION:=}"
: "${TARGET_READER:=}"
: "${HYPOTHESIS:=}"
: "${ADVANTAGE:=}"
: "${PRODUCT_POSITIONING:=}"
: "${PLATFORM:=}"
: "${GENRE:=}"
: "${AI_WRITING:=}"
: "${UPDATE_FREQ:=}"

echo ""
echo "📖 内容工厂 · 初始化"
echo "===================="
echo ""
echo "以下信息将写入 Agent 记忆系统，所有角色都会读取。"
echo "按回车跳过则使用默认模板值。"
echo ""

# ─── 交互式收集 ───

if [ -z "$COMPANY_NAME" ]; then
  read -rp "📌 工作室名称: " COMPANY_NAME
fi
if [ -z "$CONTENT_DIRECTION" ]; then
  read -rp "🧭 内容方向 (如: 都市成长小说 / 科幻连载 / 自媒体短文): " CONTENT_DIRECTION
fi
if [ -z "$TARGET_READER" ]; then
  read -rp "👤 目标读者 (如: 20-28 岁都市女性 / 大学生 / 职场新人): " TARGET_READER
fi
if [ -z "$HYPOTHESIS" ]; then
  read -rp "💡 核心假设 (如: 读者需要"逆袭+闺蜜情"的都市成长故事): " HYPOTHESIS
fi
if [ -z "$ADVANTAGE" ]; then
  read -rp "⚔️  差异化壁垒 (如: AI 辅助高产出 + 数据驱动优化): " ADVANTAGE
fi
if [ -z "$PRODUCT_POSITIONING" ]; then
  read -rp "🎯 产品定位 (一句话): " PRODUCT_POSITIONING
fi

echo ""
echo "⚡ 创作偏好 (回车跳过 = 创业期选型原则)"
if [ -z "$PLATFORM" ]; then
  read -rp "   发布平台 (如: 番茄小说 / 起点 / 知乎): " PLATFORM
fi
if [ -z "$GENRE" ]; then
  read -rp "   品类 (如: 都市成长 / 奇幻 / 悬疑): " GENRE
fi
if [ -z "$AI_WRITING" ]; then
  read -rp "   AI 辅助方式 (如: Claude 辅助生成+人工审校): " AI_WRITING
fi
if [ -z "$UPDATE_FREQ" ]; then
  read -rp "   更新频率 (如: 日更 3000 字 / 周更 2 章): " UPDATE_FREQ
fi

# ─── 默认值处理 ───

COMPANY_NAME="${COMPANY_NAME:-我的内容工厂}"
CONTENT_DIRECTION="${CONTENT_DIRECTION:-连载小说}"
TARGET_READER="${TARGET_READER:-待定（需通过 L0 战略层验证）}"
HYPOTHESIS="${HYPOTHESIS:-读者需要 ${CONTENT_DIRECTION} 类型的情绪驱动内容，有人愿意付费追更}"
ADVANTAGE="${ADVANTAGE:-AI 辅助高产出 + 8 层闭环数据驱动优化}"
PRODUCT_POSITIONING="${PRODUCT_POSITIONING:-用 AI 辅助生产高质量 ${CONTENT_DIRECTION} 内容，找到第一批付费读者}"
PLATFORM="${PLATFORM:-待定}"
GENRE="${GENRE:-待定}"
AI_WRITING="${AI_WRITING:-AI 辅助生成 + 人工审校}"
UPDATE_FREQ="${UPDATE_FREQ:-日更 3000 字}"

# ─── 写入记忆系统 ───

CLAUDE_DIR=".claude"

echo ""
echo "📝 [1/4] 写入项目上下文..."

cat > "${CLAUDE_DIR}/memory/core/project-context.md" << EOF
# 项目上下文

> 此文件由所有 Agent 共享。描述公司/产品的基本信息，每个 Agent 都应该知道。

## 公司

- **名称**：${COMPANY_NAME}
- **阶段**：0→1 创立期
- **模式**：内容生产工厂（AI 辅助 + 人创意 + 数据验证）
- **方向**：${CONTENT_DIRECTION}

## 产品

- **定位**：${PRODUCT_POSITIONING}
- **目标读者**：${TARGET_READER}
- **核心假设**：${HYPOTHESIS}
- **差异化**：${ADVANTAGE}

## 季度 OKR

- **O**：跑通战略→设定→生产→复盘闭环，获得第一批付费读者
- **KR1**：完成 L0-L3 层设定，产出首部作品前 10 章（W4）
- **KR2**：首部作品上线，完读率 > 40%（W6）
- **KR3**：L5-L6 运营/商业方案落地，付费率 > 5%（W8）
- **KR4**：L7 复盘闭环运转，至少 3 条技能优化上线（W12）

## 明确不做

- ❌ 全自动写小说（AI 不替代创意，核心由人把控）
- ❌ 追热点洗稿（没有长期 IP 价值）
- ❌ 只做不卖（生产出来必须验证商业闭环）
- ❌ 忽视数据（凭直觉写，不看完读率/跳出点）
- ❌ 一次性 IP（不设计跨作品复用的资产体系）

## 当前瓶颈

- 验证第一个内容品类的 Problem-Solution Fit
- 确定首发平台和品类
- 建立 AI 辅助创作的高效流程

## 团队角色（标准配置 8 层）

| 团队 | 角色 | 调用 | 核心使命 |
|------|------|------|----------|
| L0 战略 | 主编 | @主编 | 决定写给谁、写什么、打什么情绪 |
| L1 设定 | 设定师 | @设定师 | 构建世界观、人物、关系、风格 |
| L2 剧本 | 编剧 | @编剧 | 设计故事、埋伏笔、设爆点、控节奏 |
| L3 生产 | 写手 | @写手 | 场景、对话、章节、文风落地 |
| L4 审稿 | 审稿 | @审稿 | 结构审查、情绪强化、一致性 |
| L5 运营 | 运营 | @运营 | 读者转化、社群、留存、传播 |
| L6 商务 | 商务 | @商务 | 会员、付费墙、产品化、IP运营 |
| L7 复盘 | 复盘官 | @复盘官 | 反馈收集、复盘、技能优化、经验沉淀 |
EOF
echo "   ✅ project-context.md"

# ─── 写入技术栈 ───

echo "⚙️  [2/4] 写入技术栈..."

TECH_ROWS=""
if [ -n "$PLATFORM" ]; then
  TECH_ROWS="${TECH_ROWS}
| 发布平台 | ${PLATFORM} | — | 读者在哪里就去哪 | — |"
fi
if [ -n "$AI_WRITING" ]; then
  TECH_ROWS="${TECH_ROWS}
| AI 辅助 | ${AI_WRITING} | — | 辅助不替代，人做关键决策 | — |"
fi
if [ -n "$UPDATE_FREQ" ]; then
  TECH_ROWS="${TECH_ROWS}
| 更新频率 | ${UPDATE_FREQ} | — | 匹配平台追更习惯 | — |"
fi

if [ -z "$TECH_ROWS" ]; then
  TECH_ROWS="
| 待定 | — | — | 创业初期，尚未选型 | — |"
fi

cat > "${CLAUDE_DIR}/memory/core/tech-stack.md" << EOF
# 技术栈

> 此文件由所有 Agent 共享。每次技术选型变更时更新。

## 当前技术栈

| 层级 | 技术 | 版本 | 选型理由 | 选型日期 |
|------|------|------|----------|----------|${TECH_ROWS}

## 选型原则

- **平台优先**：先在成熟平台验证，不自建站
- **AI 赋能不替代**：AI 辅助创作和审校，核心创意由人把控
- **数据驱动**：用完读率/付费转化数据说话，不靠直觉
- **速度优先**：从选题到首章发布 < 1 周
- **可复用**：世界观/角色/风格资产跨作品复用

## 选型决策记录

| 编号 | 决策 | 理由 | 日期 | 当前状态 |
|------|------|------|------|----------|
| — | — | — | — | — |
EOF
echo "   ✅ tech-stack.md"

# ─── 重置架构 ───

echo "🏗️  [3/4] 重置架构决策..."

cat > "${CLAUDE_DIR}/memory/core/architecture.md" << EOF
# 架构决策记录

> 此文件由所有 Agent 共享。每次重大架构/技术选型决策时更新。

## 当前架构

- **阶段**：0→1 创业期
- **模式**：AI 辅助内容生产（人创意 + AI 执行 + 数据验证）
- **核心约束**：8 层智能体闭环，L3 生产层优先 Agent 化

## 内容工厂八层架构

\`\`\`
L0 战略层    ──→  L1 设定层    ──→  L2 剧本层    ──→  L3 生产层
用户画像/选题      世界观/人物       故事/爆点/节奏     场景/对话/章节
@主编              @设定师           @编剧              @写手

L4 审稿层    ──→  L5 运营层    ──→  L6 商务层    ──→  L7 复盘层
结构/情绪/一致性    转化/社群/传播    会员/付费/IP运营    反馈/复盘/沉淀
@审稿              @运营             @商务              @复盘官

                                                    ↓ 反馈闭环
                                              L0 主编 ← L7 复盘官
\`\`\`

## ADR（Architecture Decision Records）

格式：ADR-<编号> | <标题> | <状态>

### ADR 模板

\`\`\`
## ADR-<N>: <标题>

### 状态
提议 / 已采纳 / 已废弃 / 已替代

### 背景
为什么要做这个决策？

### 决策
我们选择了什么？

### 理由
为什么这么选？考虑了哪些替代方案？

### 后果
这个决策带来的好处和代价？
\`\`\`

### 已记录的 ADR

| 编号 | 标题 | 状态 | 日期 |
|------|------|------|------|
| — | — | — | — |
EOF
echo "   ✅ architecture.md"

# ─── 重置白板 ───

echo "📋 [4/4] 重置共享白板..."

cat > "${CLAUDE_DIR}/blackboard/current-sprint.md" << 'EOF'
# 当前迭代

> 协调者 Agent 维护此文件。所有 Agent 可读取当前迭代状态。

## 迭代信息

| 项目 | 值 |
|------|----|
| 迭代号 | Sprint-0 |
| 起止日期 | — |
| 季度 OKR | O: 跑通战略→设定→生产→复盘闭环，获得第一批付费读者 |

## 本期目标

```
本期目标：[每期开始由 @主编 填写，对齐 OKR]
成功标准：[完读率/付费率/追更率等可量化指标]
内容预算：[本期计划产出章节数]
```

## 任务分配

| 任务 | 负责角色 | 状态 | 交付物 |
|------|----------|------|--------|
| — | — | — | — |

## 进度

| 日期 | 更新内容 | 更新者 |
|------|----------|--------|
| — | 初始化 | @主编 |
EOF

cat > "${CLAUDE_DIR}/blackboard/open-questions.md" << 'EOF'
# 待解决问题

> 任何 Agent 都可以写入新问题，协调者负责分配和推进。

## 问题格式

```
Q<编号> | <提出者> | <日期> | <问题描述> | <严重度：阻断/重要/一般> | <状态：待处理/进行中/已解决>
```

## 问题列表

| 编号 | 提出者 | 日期 | 问题 | 严重度 | 状态 |
|------|--------|------|------|--------|------|

> 新问题追加到表末尾，不要删除已解决问题——它们是决策历史的一部分。
EOF

cat > "${CLAUDE_DIR}/blackboard/challenges.md" << 'EOF'
# 质疑记录

> 按 challenge-protocol.md 执行的质疑记录。协调者维护。

## 格式

```
C<编号> | <质疑者> | <被质疑者> | <日期> | <质疑内容> | <严重度> | <结果：通过/修改/打回>
```

## 记录

| 编号 | 质疑者 | 被质疑者 | 日期 | 质疑内容 | 严重度 | 结果 |
|------|--------|----------|------|----------|--------|------|
EOF

cat > "${CLAUDE_DIR}/blackboard/decisions-log.md" << 'EOF'
# 决策日志

> 记录每个重大决策，便于追溯。

## 格式

```
D<编号> | <决策者> | <日期> | <决策内容> | <依据> | <影响范围>
```

## 决策记录

| 编号 | 决策者 | 日期 | 决策 | 依据 | 影响范围 |
|------|--------|------|------|------|----------|
EOF

echo "   ✅ current-sprint.md / open-questions.md / challenges.md / decisions-log.md"

# ─── 清空归档 ───

echo ""
echo "📦 清空归档记忆（保留模板结构）..."

cat > "${CLAUDE_DIR}/memory/archival/decisions/decisions.md" << 'EOF'
# 决策归档

> 已完成或已废弃的决策存档于此。

## 归档记录

| 编号 | 标题 | 原状态 | 归档原因 | 归档日期 |
|------|------|--------|----------|----------|
EOF

cat > "${CLAUDE_DIR}/memory/archival/lessons/lessons.md" << 'EOF'
# 经验教训

> 每次迭代复盘后的经验教训存档于此。格式：L<编号> | <教训> | <场景> | <如何避免/复用>

## 教训记录

| 编号 | 教训 | 场景 | 如何避免/复用 |
|------|------|------|---------------|
EOF

cat > "${CLAUDE_DIR}/memory/archival/user-research/research.md" << 'EOF'
# 读者调研归档

> 读者访谈、评论分析、阅读统计数据等调研数据存档于此。

## 调研记录

| 编号 | 方法 | 日期 | 样本数 | 关键发现 | 行动 |
|------|------|------|--------|----------|------|
EOF

echo "   ✅ archival/decisions / lessons / user-research"

# ─── 完成 ───

echo ""
echo "🎉 初始化完成！"
echo ""
echo "你的内容工厂信息："
echo "  📌 工作室: ${COMPANY_NAME}"
echo "  🧭 方向: ${CONTENT_DIRECTION}"
echo "  🎯 定位: ${PRODUCT_POSITIONING}"
echo "  👤 读者: ${TARGET_READER}"
echo "  📱 平台: ${PLATFORM}"
echo ""
echo "下一步："
echo "  1. 启动 Claude Code"
echo "  2. 输入 @主编 定义第一个内容选题和目标读者"
echo "  3. 输入 @设定师 构建世界观和人物"
echo "  4. 输入 @编剧 设计故事弧线"
echo ""
echo "随时可以修改 .claude/memory/core/ 下的文件更新工厂信息。"
