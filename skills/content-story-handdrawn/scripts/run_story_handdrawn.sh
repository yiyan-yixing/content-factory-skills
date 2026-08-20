#!/bin/bash
# run_story_handdrawn.sh — 中文故事 → 手绘日记漫画视频（一次性封装）
#
# 用法:
#   bash run_story_handdrawn.sh <故事.txt> [标题] [额外参数...]
#
# 示例:
#   bash run_story_handdrawn.sh my-story.txt "枣树的秋天" --style diary --transition cut
#
# 产出: eng/story-handdrawn-renderer/out/picture_silent.mp4
set -euo pipefail

# 定位 renderer 项目（本脚本在 skill 内，回退到相对约定路径）
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RENDERER_DIR="${STORY_HANDDRAWN_DIR:-/Users/zhanglei/yycc/eng/story-handdrawn-renderer}"
IMAGE_STUDIO_DIR="${SEEDREAM_STUDIO_DIR:-/Users/zhanglei/yycc/eng/image-studio}"

INPUT="${1:?用法: run_story_handdrawn.sh <故事.txt> [标题] [额外参数...]}"
TITLE="${2:-手绘日记}"
shift 2 || true

if [ ! -f "$INPUT" ]; then
  echo "❌ 找不到故事文件: $INPUT" >&2
  exit 1
fi
if [ ! -d "$RENDERER_DIR" ]; then
  echo "❌ 找不到 renderer 项目: $RENDERER_DIR（用 STORY_HANDDRAW_DIR 指定）" >&2
  exit 1
fi

cd "$RENDERER_DIR"

# 首次使用自动装依赖
[ -d node_modules ] || npm install --silent

echo "🎨 故事 → 手绘日记漫画：$(basename "$INPUT")"
CODEX_HOME="$RENDERER_DIR/.shim" \
SEEDREAM_STUDIO_DIR="$IMAGE_STUDIO_DIR" \
OPENAI_API_KEY=dummy \
python3 scripts/run_story_video.py \
  --input "$INPUT" \
  --title "$TITLE" \
  --mode full \
  --generator api \
  --text-mode font \
  --transition cut \
  "$@"

echo ""
echo "✅ 成片: $RENDERER_DIR/out/picture_silent.mp4"
