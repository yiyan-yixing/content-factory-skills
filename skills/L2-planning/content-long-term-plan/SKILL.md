---
name: "Content Long Term Plan / 长线规划"
description: "将故事骨架拆解为章节结构，安排主线、支线、节奏。连载小说的核心规划工具。"
when_to_use: "需要规划章节结构时；用户说'章节规划''长线规划''ChapterPlan''连载规划''节奏安排'时触发。频次：on-demand，时间盒：45min"
allowed-tools:
  - Read
  - Write
  - Edit
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-202"
layer: "L2-内容规划层"
---

# SKILL-202：长线规划

你是内容公司的连载规划师。你的目标：把故事骨架拆成可执行的章节计划。

## 技能定义

| 维度 | 说明 |
|------|------|
| **输入** | StoryMap、目标字数/章节数 |
| **输出** | ChapterPlan（章节计划） |
| **依赖** | SKILL-201 故事设计 |
| **自动化** | 人工★★★☆☆ Agent★★★★☆ |
| **训练价值** | 高（剧情→章节） |

## 输入字段

```json
{
  "story_map_id": "故事地图 ID",
  "total_chapters": 100,
  "words_per_chapter": 3000,
  "update_frequency": "日更/周更"
}
```

## 输出字段

```json
{
  "arcs": [
    {"chapters": "1-10", "phase": "铺垫", "main_event": "日常+隐患", "emotion": "好奇"}
  ],
  "chapter_list": [
    {"chapter": 1, "goal": "建立角色日常", "key_scene": "林晚加班", "word_count": 3000}
  ],
  "beat_sheet": "节拍表"
}
```

## 执行步骤

### Step 1：弧线切分（15min）

按 StoryMap 的三幕切分章节：
- 铺垫期：建立日常、埋伏笔
- 升级期：冲突叠加、关系推进
- 高潮期：集中爆发、收束

### Step 2：章节分配（15min）

每章定义：
- 目标：这章要完成什么
- 关键场景：最重要的一个场景
- 章末钩子：让读者想看下一章的东西
- 字数目标

### Step 3：节奏校准（15min）

检查节奏是否合理：
- 是否有连续 3 章以上没有转折？
- 高潮章节是否有足够铺垫？
- 钩子密度是否均匀？

## 产出

1. ChapterPlan（章节规划表）
2. 弧线分配图
3. 节拍表（Beat Sheet）

## 关键指标

- 完读率预估：每章的章末钩子强度
- 追更力：读者看完一章想看下一章的比例

## 反模式（避免）

- ❌ 每章信息量均等（要有轻重缓急）
- ❌ 铺垫太长（前 10 章还没有第一个钩子）
- ❌ 支线和主线比例失衡
- ❌ 没有章末钩子（读者随时可以放下）

## 资产沉淀

- ChapterPlan → 下游技能（场景设计）的直接输入
- 章节模板可复用（铺垫章/转折章/高潮章模板）
