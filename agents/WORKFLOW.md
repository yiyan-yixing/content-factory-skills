# 内容工厂 Agent 协作流程

> 一条「选题 → … → 发行 → 复盘」闭环 DAG，**按品类条件路由**——不同品类走不同阶段链。
> 5 品类：tech（科技图文）/ novel（网文连载）/ xhs（小红书）/ video（视频）/ drama（短剧·漫剧）。
> 支持：品类路由、条件分支、质疑协议、共享记忆、DAG 编排、反馈闭环。

---

## 品类条件 DAG（核心）

不是固定线性流水线，而是**按品类走不同阶段链的有向无环图**。选题后由 `@head-of-content` 判定品类，按对应链级联。审稿是关键闸门，复盘驱动下一轮。

```
品类路由（@head-of-content 判定）
  │
  ├── tech  : 选题 → 写作 → 配图 → 审稿 → 发行                      （快速，2-3 天）
  ├── novel : 选题 → 设定 → 结构 → 写作 → 审稿 → 运营 → 发行 → 商务 → 复盘  （完整，1 周+）
  ├── xhs   : 选题 → 写作 → 审稿 → 发行                              （超快速）
  ├── video : 选题 → 写作(脚本) → 视频 → 审稿 → 发行
  └── drama : 选题 → 设定 → 结构 → 写作(剧本) → 视频 → 审稿 → 发行    （2026 平台分账红利）
```

每条链都从 `@head-of-content`（选题 + 品类路由）出发；各品类**跳过的阶段不触发**（tech/xhs/video 跳过设定/结构/运营/商务；短品类通常不走商务）。

### 完整链路（novel 示例，含走查闸门）

```
@head-of-content 判品类=novel + 用户画像 + 情绪 + 选题
  └── ⚡ 董事长走查选题 ← 反馈闭环①（≤2轮，全品类）
        ├── 通过 → @world-builder 世界观 + 人物 + 关系 + 风格
        │           └── ⚡ 编剧走查设定 ← 反馈闭环④（≤2轮，仅 novel/drama）
        │                 └── 通过 → @story-architect 故事弧线 + 爆点 + 节奏
        │                       └── ⚡ 写手走查剧本 ← 反馈闭环⑤（≤2轮，仅 novel/drama）
        │                             └── 通过 → @writer 场景 + 对话 + 章节 + 文风
        │                                   └── @reviewer 结构 + 情绪 + 节奏 + 一致性 ← 反馈闭环②
        │                                         ├── Go → @operator → @distributor → @business
        │                                         └── No-Go → @writer 修改（≤2轮）
        └── @retro-officer → 反馈闭环③ → @head-of-content（新一轮）
```

---

## 角色职责速查

| 角色 | 调用 | 做什么 | 不做什么 | 品类 |
|------|------|--------|----------|------|
| **主编** | `@head-of-content` | 判品类、定方向、画像、选题、品类路由 | 不陷入写作细节 | 全品类 |
| **设定师** | `@world-builder` | 世界观、人物、关系、风格 | 不自己写故事线 | novel / drama |
| **结构师** | `@story-architect` | 故事弧线/大纲、伏笔、爆点、节奏 | 不亲自写每一章 | novel / drama（长 tech 可选） |
| **写手** | `@writer` | 文章/章节/笔记/脚本/剧本、文风 | 不改设定不改故事线 | 全品类 |
| **配图师** | `@illustrator` | 架构图/流程图/数据图/封面/插图 | 不改文字内容 | tech / novel / xhs |
| **视频剪辑** | `@video-editor` | 分镜脚本、视频剪辑、数据动画、封面帧 | 不写正文 | video / drama |
| **审稿** | `@reviewer` | 结构/情绪/节奏/一致性、平台合规、P0-P3 | 不跳过审查直接发布 | 全品类 |
| **运营** | `@operator` | 转化、社群、留存、传播、SEO | 不刷量不追虚荣指标 | novel（他品类可选） |
| **发行** | `@distributor` | X/Substack/知乎/微信/小红书/B站 多平台发布 | 不改内容、不跳过发布检查 | 全品类 |
| **商务** | `@business` | 会员、付费墙、产品化、IP 运营 | 不在平淡处卡付费墙 | novel（tech 可产品化） |
| **复盘** | `@retro-officer` | 反馈、复盘、优化、经验沉淀 | 不写流水账，要提取规则 | 全品类 |

---

## 品类路由详情

| 品类 | 阶段链 | 适用内容 | 预计周期 | 走查闭环 |
|------|--------|---------|---------|---------|
| ⚡ **tech** | 选题→写作→配图→审稿→发行 | 技术博客/教程/观点/ebook/公众号 | 2-3 天 | ①③ |
| 🏗️ **novel** | 选题→设定→结构→写作→审稿→运营→发行→商务→复盘 | 连载小说/IP 长篇/系列课程 | 1 周+ | ①②③④⑤ |
| ⚡ **xhs** | 选题→写作→审稿→发行 | 小红书图文/种草/短笔记 | 1-2 天 | ①③ |
| 🎬 **video** | 选题→写作(脚本)→视频→审稿→发行 | 知识视频/口播/教程 | 3-5 天 | ①③ |
| 🎭 **drama** | 选题→设定→结构→写作(剧本)→视频→审稿→发行 | 短剧/漫剧（平台分账） | 3-5 天 | ①②③④⑤ |

> **新增品类** = 加一行路由 + 指明阶段链，不动角色定义（角色是品类无关的）。

---

## 级联协议（Cascade Protocol）

Agent 完成核心工作后，按品类路由自动派发下游。用户只需和入口角色（`@head-of-content`）沟通，整条链自动走完。

### 级联路由表（品类条件）

| 当前角色 | 完成条件 | 下游（按品类） | 交接物 |
|---------|---------|---------------|--------|
| @head-of-content | 选题走查①通过 | novel/drama→@world-builder；tech/xhs/video→@writer | 战略层产出（画像/选题） |
| @world-builder | 设定完成，走查④通过 | @story-architect | WorldBook + CharacterCard + RelationMap + StyleGuide |
| @story-architect | 结构完成，走查⑤通过 | @writer | StoryArc + HighlightList + RhythmChart（或文章大纲） |
| @writer | 定稿完成 | tech→@illustrator→@reviewer；novel→@reviewer；video/drama→@video-editor→@reviewer | FinalChapter[] / 文章 / 脚本 |
| @video-editor | 视频产出 | @reviewer | VideoClip + VideoScript + CoverFrame |
| @reviewer | publish_ready=true | novel→@operator；tech/xhs/video/drama→@distributor | 审核通过的内容 |
| @reviewer | publish_ready=false | @writer（修改，≤2 轮） | P0/P1 问题 |
| @operator | 运营方案完成（设计模式·pre-publish） | @distributor | SpreadPlan（+ 运营四件套 ConversionPlan/CommunityPlan/RetentionPlan 入 blackboard 供 business） |
| @distributor | PublishReport 完成 | novel→@business；tech/xhs/video/drama→@retro-officer（或结束） | PublishReport（+ blackboard 运营四件套，novel） |
| @business | 商务方案完成 | @retro-officer | SubscriptionPlan + PaywallStrategy |
| @retro-officer | 复盘完成 | @head-of-content（闭环③） | FeedbackDB + ReviewBook + KnowledgeBase |

### 级联触发判断

| 任务意图 | 级联？ |
|---------|--------|
| 来自上游 Agent 的级联任务 | ✅ 级联 |
| 包含"走完流程""全流程""从选题到发布""一键出内容"意图 | ✅ 级联 |
| 单一动作（"写个章节""做个审稿"） | ❌ 不级联 |
| 用户说"只做这一步" | ❌ 不级联 |

### 人工确认点

| 节点 | 触发条件 | 谁确认 | 为什么 |
|------|---------|--------|--------|
| 选题走查① | 主编出选题后（全品类） | 董事长（用户） | 方向错 = 全白干 |
| 设定走查④ 2 轮打回 | 编剧连续 2 轮打回设定（novel/drama） | 用户 | 设定问题还是选题问题？ |
| 剧本走查⑤ 2 轮打回 | 写手连续 2 轮打回剧本（novel/drama） | 用户 | 剧本问题还是设定问题？ |
| 审稿打回第 3 轮 | 写手连续 3 轮未通过 | 用户 | 写手问题还是上游问题？ |
| 💰 付费墙位置确认 | 商务出付费墙方案后（novel） | 董事长（用户） | 直接决定收入和读者体验 |
| 复盘闭环③决策 | 复盘官出报告后（全品类） | @head-of-content | 继续/调整/砍掉 = 战略决策 |

---

## 反馈闭环协议（Feedback Loop Protocol）

在级联的关键交接点加入双向反馈循环，防止方向跑偏和需求漂移。**走查（walkthrough）≠ 质疑（challenge）**：走查是快速确认"做得对不对"，质疑是深度拷问"做得好不好"。

### 核心规则

1. **走查门控** — 选题必须经董事长走查通过；novel/drama 的设定须经结构师走查、剧本须经写手走查，才能级联下游。
2. **最多 2 轮回退** — 超过 2 轮上报用户。
3. **走查记录** — 每次走查写入 `blackboard/walkthrough-{timestamp}.md`。
4. **走查不替代质疑** — 质疑协议（challenge-protocol.md）照常运行。
5. **闭环优先级** — ① 选题走查 > ④ 设定走查 > ⑤ 剧本走查 > ② 审稿闸门 > ③ 复盘闭环。

### 五条闭环

| 闭环 | 触发 | 走查者 | 被走查者 | 走查内容 | 适用品类 | 最大轮数 |
|------|------|--------|----------|----------|---------|----------|
| ① 选题走查 | 主编出选题 | 董事长(用户) | @head-of-content | 方向/品类/读者/差异化 | **全品类** | 2 |
| ④ 设定走查 | 设定师出设定 | @story-architect | @world-builder | 世界观撑量/角色冲突/风格可执行 | **novel/drama** | 2 |
| ⑤ 剧本走查 | 结构师出剧本 | @writer | @story-architect | 弧线每章有场景/爆点可写/节奏可用 | **novel/drama** | 2 |
| ② 审稿闸门 | 写手出定稿 | @reviewer | @writer | P0/P1 清零 + 一致性 100% | **全品类** | 2 |
| ③ 复盘闭环 | 复盘官出复盘 | @head-of-content | — | 继续/调整/砍掉 | **全品类** | — |

> tech / xhs / video 品类只走 ①②③（无虚构设定/剧本，跳过 ④⑤）。

### 走查记录格式

```markdown
# 走查记录 walkthrough-{timestamp}
品类：[tech/novel/xhs/video/drama]
走查类型：选题走查 / 设定走查 / 剧本走查 / 审稿闸门 / 复盘闭环
走查者：[角色名]   被走查者：[角色名]   轮次：[1/2]
## 走查结论
通过 / 打回
## 走查要点
1. [要点1]：✅/❌ [说明]
## 修改要求（打回时填写）
- [具体修改要求]
```

### 选题走查要点（董事长走查主编，全品类）

1. **方向一致性** — 是否符合公司战略方向和当前 OKR？
2. **品类差异化** — 是否有足够差异化论证？不是"又一个 XXX"。
3. **目标读者** — 画像是否可验证？假设是否可证伪？
4. **可执行性** — 现有资源下可实现？

### 设定走查要点（结构师走查设定师，novel/drama）

1. **故事可展开性** — 世界观规则和冲突源够不够撑 50+ 章？角色关系张力够？
2. **角色可写性** — 角色有致命缺陷和成长弧线？标志性语言可区分？
3. **风格可执行** — StyleGuide 对写手够具体？正面范例和反面禁忌可操作？
4. **情绪一致性** — 设定服务 EmotionMap 核心情绪？不是设定师自嗨。

### 剧本走查要点（写手走查结构师，novel/drama）

1. **场景可写** — 每章有明确场景和冲突？
2. **爆点可达** — 爆点位置有具体情节支撑？
3. **节奏可执行** — 节奏图是指导还是束缚？
4. **伏笔可埋** — 长线伏笔有明确埋设方式和时机？

### 走查结果路由

| 走查类型 | 通过 | 打回（轮次 < 2） | 打回（第 2 轮） |
|---------|------|-----------------|----------------|
| ① 选题走查 | 按品类级联下游 | @head-of-content 修改后重新走查 | BLOCKED，上报用户 |
| ④ 设定走查 | 级联到 @story-architect | @world-builder 修改后重新走查 | BLOCKED，上报用户 |
| ⑤ 剧本走查 | 级联到 @writer | @story-architect 修改后重新走查 | BLOCKED，上报用户 |

---

## 角色协作矩阵（novel 完整链示例）

| | 主编 | 设定师 | 结构师 | 写手 | 配图 | 视频 | 审稿 | 运营 | 发行 | 商务 | 复盘 |
|--|------|--------|--------|------|------|------|------|------|------|------|------|
| **主编** | — | 给画像+选题 | — | — | — | — | — | 给画像 | — | — | 给 OKR |
| **设定师** | — | — | 给设定 | 给风格 | — | — | 给角色卡 | — | — | 给角色卡 | — |
| **结构师** | — | — | — | 给弧线+爆点 | — | — | 给弧线 | — | — | — | — |
| **写手** | — | — | — | — | 给正文 | 给脚本 | 给定稿 | 给内容 | — | — | — |
| **审稿** | — | — | — | 给修改意见 | — | — | — | 给就绪内容 | — | — | — |
| **运营** | 给读者反馈 | — | — | — | — | — | — | — | 给传播方案 | 给转化方案 | 给数据 |
| **发行** | — | — | — | — | — | — | — | — | — | 给 PublishReport | — |
| **复盘** | 给复盘结论 | — | — | — | — | — | — | — | — | — | — |

> tech/xhs/video 品类的协作矩阵是本表的子集（只含该品类阶段链涉及的角色）。

---

## 记忆读写规则

| Agent | 可写 | 可读 |
|-------|------|------|
| @head-of-content | blackboard/decisions-log.md, blackboard/current-sprint.md | 所有 |
| @world-builder | memory/core/project-context.md（设定部分） | memory/core/, archival/ |
| @story-architect | blackboard/current-sprint.md（结构部分） | memory/core/ |
| @writer | — | memory/core/, blackboard/ |
| @reviewer | blackboard/challenges.md | 所有 |
| @operator | blackboard/current-sprint.md（运营部分） | memory/core/, archival/user-research/ |
| @business | memory/core/architecture.md（商业部分） | memory/core/ |
| @retro-officer | blackboard/current-sprint.md, memory/archival/lessons/, memory/archival/decisions/ | 所有 |

---

## 紧急流程

### 严重一致性事故（novel/drama：人物/世界观前后矛盾已发布）

```
@reviewer/读者 发现事故 → @writer 定位矛盾章节 → @reviewer 评估影响范围
                     → @writer 修复 → @reviewer 验证 → 重新发布
全程 < 2 小时止血
```

### 内容方向错误（数据异常/差评）

```
@retro-officer 报告数据异常 → @head-of-content 判断是内容问题还是运营问题
                     → 内容问题 → 调整走向 + @writer 修改
                     → 方向问题 → 切品类 → 回到 Step 0 重新判定
不靠"再写几篇看看"硬撑，数据说话
```

### 爆款机会窗口（某内容意外爆火/平台推流）

```
发现爆火信号 → @operator 加大传播 → @business 提前设计付费墙和产品化
             → @head-of-content 评估是否衍生新 IP → @world-builder 快速扩展设定
抓住窗口期，48 小时内出商业方案
```

---

## 终端报告格式

```
🏭 内容工厂流水线完成

📋 品类：[tech/novel/xhs/video/drama]
📋 选题：[选题摘要]
👑 ① 选题走查：[N] 轮（通过/打回）
[仅 novel/drama] 🏗️ ④ 设定走查：[N] 轮   📝 ⑤ 剧本走查：[N] 轮
✍️ 内容：[N] 章/篇
🔍 ② 审稿闸门：[N] 轮（通过/打回）
📢 发行：[平台清单]
[仅 novel] 💰 付费墙位置：[确认/待确认]
🔄 ③ 复盘闭环：[继续/调整/砍掉]
```
