# 爆款学习 Batch1 技能增量回灌记录（2026-08-10）

> 状态：✅ 6 个 gap 已全部落源头 + 同步安装侧
> 级联：cascade-viral-20260810
> 主理：@head-of-skills（工程实施）→ @head-of-content（复核）
> 来源：viral-deconstruct-20260810 / viral-deconstruct-20260810-batch1

## 回灌路径

- 源头：`skills/content-factory-skills/skills/`（改动主）
- 安装：`content/.claude/skills/`（已同步，见下表）
- 全部为「追加式」补丁，不改写既有内容；每条补丁标注来源。

## 6 个 gap 落点清单

| # | 优先级 | Gap | 落点文件（源头） | 章节 | 安装侧同步 |
|---|--------|-----|----------------|------|-----------|
| 1 | 核心 | 类比域缺「金融/博弈」域 + 角色升格类 | `skills/L3-production/content-analogy-craft/SKILL.md` | 类比域 → 新增 `### 6. 金融博弈` | ✅ |
| 2 | 核心 | 缺「反共识/泼冷水」钩子模式 | `skills/L3-production/content-hook-design/SKILL.md` | 开头公式 → 新增 `### 4. 反共识/泼冷水型` | ✅ |
| 3 | 核心 | 缺「数字可信感堆叠」证据链规则 | `skills/content-quality-rules/SKILL.md` | 正文铁律 → 新增 `**4. 数字证据链**` | ✅（name 字段保留） |
| 4 | 次要 | 缺「身份实录型信任状」标题模板 | `skills/L3-production/content-title-engine/SKILL.md` | 标题公式 → 新增 `### 垂类扩展：身份实录型` | ✅ |
| 5 | 次要 | 缺「时间货币化」钩子 + 收藏驱动设计 | `skills/L3-production/content-hook-design/SKILL.md` + `skills/L3-production/content-platform-adapt/SKILL.md` | 开头公式 → 新增 `### 5. 时间货币化型`；收藏/分享驱动力设计 → 新增 `### 收藏驱动设计` | ✅ |
| 6 | 次要 | 垂类「专业 vs 通俗」二选一路线 | `skills/content-quality-rules/SKILL.md` + `skills/L3-production/content-analogy-craft/SKILL.md` | 文风铁律 → 新增 `### 垂类路线铁律`；密度规则 → 补垂类路线注记 | ✅ |

## 各 gap 新增内容摘要

### Gap 1 → content-analogy-craft（SKILL-359）
- 类比域新增第 6 域「金融博弈」（AI 自动化/一人公司/量化垂类专用），6 条模板：工具定位（秘书 vs 对冲基金）、卖铲子逻辑、角色升格（合伙人）、成本锚点（低于雇实习生）、职位类比（市场部）、押注博弈。
- 附加「角色升格类比模板（工具→角色）」一句规则。
- 示例：新智元 Clawdbot / 古都闲云泼冷水 / 三木一人公司 / Chris 北大状元。

### Gap 2 → content-hook-design（SKILL-360）
- 开头公式从 3 种 → 5 种，新增「反共识/泼冷水型」：公式=承认叙事→看穿动机→硬逻辑拆解→降维收尾，含 4 条规则 + 古都闲云 619 赞示例。

### Gap 3 → content-quality-rules（SKILL-357）
- 正文铁律新增第 4 条「数字证据链」：操作数字堆叠 + 结果数字堆叠 + 真实账本对比三模式，含 3 条规则，示例用 Insist / 新智元 / 三木 的真实数字。

### Gap 4 → content-title-engine（SKILL-358）
- 标题公式追加「垂类扩展：身份实录型」：公式 `[身份标签]+[数字/决定]+[系列感]`，示例拒 60w 北大状元实录 + 双非二本软文，含焦虑三重标签规则。

### Gap 5 → content-hook-design + content-platform-adapt（SKILL-360/362）
- hook-design：新增「时间货币化型」开头公式（3 小时→15 分钟 + 把时间还给自己），含 3 条规则 + 小红书 2217 赞示例。
- platform-adapt：收藏/分享驱动力设计下新增「收藏驱动设计（每条独立可收藏）」：金句清单（X thread）/ 框架清单（小红书）/ 实录系列（小红书），附 8991 藏 vs 8985 赞、2052 书签 vs 911 赞 实证。

### Gap 6 → content-quality-rules + content-analogy-craft（SKILL-359/357）
- quality-rules：文风铁律下新增「垂类路线铁律：专业 vs 通俗二选一」——硬核线（结构+数字，类比可降）/ 通俗线（故事+类比+身份），中间态最危险。
- analogy-craft：密度规则补一条垂类路线注记，交叉引用 quality-rules 垂类路线铁律。

## 安装侧同步说明

- content-analogy-craft / content-hook-design / content-title-engine / content-platform-adapt：源头与安装侧原本字节一致，已直接覆盖同步，`cmp` 验证一致。
- content-quality-rules：安装侧 `name` frontmatter 为「Content Quality Rules / 内容质量铁律」，源头为「content-quality-rules」，为既有差异。同步时保留安装侧 name，仅追加两份补丁，验证通过。
- 未重跑 install.sh（全量 cp 会覆盖安装侧既有定制 name 字段）；按需可后续 reinstall 统一。

## 约束遵守

- 只落 gap 清单内 6 项，未顺手改其它内容、未加风格偏好、未重排既有结构。
- 时间盒内完成（追加式补丁，每处 1 个 batch1 真实案例）。

## 下一步

- @head-of-content 复核补丁可用性。
- CEO 收尾验收（cascade-viral-20260810）。

---
*回灌记录。@head-of-skills 落，待 @head-of-content 复核。*
