---
name: "content-story-handdrawn"
description: "将中文故事渲染为手绘日记漫画风格视频（竖屏 MP4，无音轨）。当用户说'故事手绘漫画''手绘日记''日记漫画视频''把故事画成漫画''handdrawn story video'时触发。"
when_to_use: "需要把一段故事/随笔/短篇转成手绘日记漫画风竖屏视频时（小红书/抖音/B站故事类内容、个人叙事、回忆录片段）。频次：on-demand，时间盒：10min（不含生图等待）"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-VIDEO-04"
layer: "L3-生产层-视频线"
---

# SKILL-VIDEO-04：中文故事 → 手绘日记漫画视频

把一段中文故事渲染成 **手绘日记漫画风格** 的竖屏视频（1080×1440，无音轨，供后续配乐/旁白/字幕），像「手绘日记/生活手账」的动画。

**落地来源**：Apple Notes 收藏吸收（2026-08-17）。上游开源：`gnipbao/story-to-handdrawn-video`（MIT，Remotion 渲染器，20 种手绘风格）。生图桥接本司 火山方舟 Seedream 5.0 Pro（无需 Codex）。

## 一、产出定义

| 项 | 值 |
|---|---|
| 视频 | 1080×1440 竖屏 · 30fps · h264 · 无音轨 |
| 时长 | 每句故事约 5s（长句自动切分） |
| 风格 | 20 种手绘风格可选（默认 `diary`），含黑白线稿/彩铅/蜡笔等 |
| 字幕 | 由故事文本生成，已烘进画面 |
| 流程 | 故事 → 分镜（每句一场景）→ 逐场景生图（Seedream）→ Remotion 渲染 |

## 二、环境

- **Renderer 项目**：`eng/story-handdrawn-renderer/`（本司仓库，含 Seedream shim）
- **生图后端**：火山方舟 Seedream（`eng/image-studio/seedream_client.py`），需 `ARK_API_KEY` 环境变量
- **运行时依赖**：Node ≥20（Remotion）、Python3（seedream_client 同依赖）

**首次使用前**（一次性）：
```bash
cd eng/story-handdrawn-renderer && npm install
```

## 三、用法

```bash
cd eng/story-handdrawn-renderer

# 完整流程：plan → generate(Seedream) → render，一步到位
CODEX_HOME="$PWD/.shim" \
SEEDREAM_STUDIO_DIR=/Users/zhanglei/yycc/eng/image-studio \
OPENAI_API_KEY=dummy \
python3 scripts/run_story_video.py \
  --input 故事.txt \
  --title "故事标题" \
  --mode full \
  --generator api \
  --text-mode font \
  --transition cut \
  --force
```

产出：`eng/story-handdrawn-renderer/out/picture_silent.mp4`（约 20s，1.7MB）。

### 参数速查

| 参数 | 说明 | 默认 |
|---|---|---|
| `--input` | 故事文本文件（UTF-8，每句一行或多行均可） | 必填 |
| `--title` | 视频标题（也会成为分镜语境） | — |
| `--mode` | `plan`（只出分镜）/ `generate`（plan+生图）/ `full`（全部+渲染）/ `import` / `render` | `full` |
| `--generator` | `api`（本司 Seedream shim，推荐）/ `codex`（上游原生，需 Codex） | `codex` |
| `--text-mode` | `font`（中文需用 font，否则可能乱码） | `font` |
| `--transition` | 转场：`cut` / `fade` 等 | `cut` |
| `--style` | 手绘风格名（`python3 scripts/list-handdrawn-styles.mjs` 列出全部 20 种） | `diary` |
| `--force` | 覆盖已存在的生成结果 | — |

### 分步调试

```bash
# 1) 只出分镜计划（不烧钱）
... --mode plan --force

# 2) 只渲染（图已生成过，跳过生图）
... --mode render

# 3) 快速预览（低分辨率，先看构图）
cd eng/story-handdrawn-renderer && npm run render:preview
```

## 四、Seedream shim 说明

上游渲染器用固定路径调用 Codex 的 `image_gen.py` CLI（`$CODEX_HOME/skills/.system/imagegen/scripts/image_gen.py`）。本司无 Codex，改用一个 **shim**（`eng/story-handdrawn-renderer/.shim/`）满足同一 CLI 契约，但转调火山方舟 Seedream 5.0 Pro：

- `CODEX_HOME="$PWD/.shim"` → 让渲染器找到 shim
- `OPENAI_API_KEY=dummy` → 渲染器只在 `--generator api` 时检查此键，shim 真正使用的是 `ARK_API_KEY`
- `SEEDREAM_STUDIO_DIR` → seedream_client 所在目录（默认已是 `/Users/zhanglei/yycc/eng/image-studio`，缺省可不传）

**已知限制**：
- `--image` 参考图（风格参考/角色连续参考）被忽略：Seedream 参考图只收 URL 不收本地路径。提示词文本本身足够详细时无需参考图。
- 分辨率固定 1K（¥0.30/张）——够用最省，不需要提 `--quality`。

## 五、工作流提示

1. **故事入参**：从闪念/选题/随笔取故事。建议 60-120 字、情感有起伏、场景可分 4-6 句（对应 4-6 场景 ≈ 20-30s 成片）。句子太长会被自动切分，注意断句。
2. **风格选择**：先 `list-handdrawn-styles.mjs` 看 20 种风格，封面/标题页用 `bw`（黑白线稿）或 `color`（彩铅），正文用 `diary` 保连续。
3. **角色连续**：同一故事想保持主角形象一致 → 提示词里给足主角外貌描述（`--character-lock` 传一段描述），shim 下参考图失效但仍可靠文本锁定。
4. **视频线衔接**：产出是静音成片，交 `@video-editor` 配 BGM/旁白/字幕条再分发。
5. **成片归档**：成品视频按 content 视频线惯例归档到 `content/video/`，本项目 `out/` 仅作工作区（gitignore）。
