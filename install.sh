#!/bin/bash
# 内容工厂 Agent 体系一键安装脚本
# 用法: bash install.sh /path/to/project
# 或者: bash install.sh /path/to/project --skip-init
#
# 本地仓库安装（已 clone content-factory-skills 到本地）:
#   bash install.sh /path/to/project
# 远程安装（发布到 Git 后）:
#   curl -fsSL https://raw.githubusercontent.com/yiyan-yixing/content-factory-skills/main/install.sh | bash

set -e

# 仓库地址（发布后替换为真实地址；本地安装时自动检测使用本地文件）
REPO_URL="https://github.com/yiyan-yixing/content-factory-skills.git"
CLONE_DIR=$(mktemp -d)
TARGET_DIR="."
SKIP_INIT=""

# ─── 解析参数 ───
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-init) SKIP_INIT="1"; shift ;;
    --init) SKIP_INIT=""; shift ;;
    -*) echo "未知参数: $1"; shift ;;
    *) TARGET_DIR="$1"; shift ;;
  esac
done

echo "📖 内容工厂 Agent 体系安装"
echo "============================"
echo ""

# ─── Step 1: 定位源仓库 ───
echo "📦 [1/5] 定位源仓库..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/README.md" ] && [ -d "$SCRIPT_DIR/agents" ]; then
  CLONE_DIR="$SCRIPT_DIR"
  echo "   使用本地仓库: $CLONE_DIR"
else
  echo "   本地未找到完整仓库，尝试克隆远程..."
  git clone --depth 1 "$REPO_URL" "$CLONE_DIR" --quiet
  echo "   克隆完成"
fi

# ─── Step 2: 安装 Skills ───
echo "🎯 [2/5] 安装 Skills 到 .claude/skills/..."
cd "$TARGET_DIR"
mkdir -p .claude/skills
if [ -d "$CLONE_DIR/skills" ]; then
  cp -r "$CLONE_DIR"/skills/* .claude/skills/ 2>/dev/null || true
  echo "   ✅ 35 个 Skills"
fi

# ─── Step 3: 安装 Agents ───
echo "👥 [3/5] 安装 Agents 到 .claude/agents/..."
mkdir -p .claude/agents
for agent_file in "$CLONE_DIR"/agents/*.md; do
  if [ -f "$agent_file" ]; then
    cp "$agent_file" .claude/agents/
  fi
done
echo "   ✅ 9 个 Agent + WORKFLOW + 质疑协议"

# ─── Step 4: 安装记忆系统 + 白板 + 评估 + CLAUDE.md ───
echo "🧠 [4/5] 安装记忆系统 + 白板 + 评估体系..."

# 询问 Profile（如果有多个）
SELECTED_PROFILE=""
if [ -d "$CLONE_DIR/profiles" ]; then
  AVAILABLE_PROFILES=($(ls -d "$CLONE_DIR"/profiles/*/ 2>/dev/null | xargs -I{} basename {}))
  if [ ${#AVAILABLE_PROFILES[@]} -gt 0 ]; then
    echo ""
    echo "📋 可用的垂直 Profile："
    echo "   0) 通用（默认，不选 Profile）"
    PROFILE_IDX=1
    for p in "${AVAILABLE_PROFILES[@]}"; do
      echo "   $PROFILE_IDX) $p"
      PROFILE_IDX=$((PROFILE_IDX + 1))
    done
    echo ""
    read -p "请选择 Profile [0-$((PROFILE_IDX-1))]（默认 0）: " profile_choice
    profile_choice=${profile_choice:-0}
    if [ "$profile_choice" != "0" ] && [ "$profile_choice" -le "$((PROFILE_IDX-1))" ] 2>/dev/null; then
      SELECTED_PROFILE="${AVAILABLE_PROFILES[$((profile_choice-1))]}"
      echo "   ✅ 已选择 Profile: $SELECTED_PROFILE"
    else
      echo "   ✅ 使用通用配置"
    fi
  fi
fi

# 记忆系统
mkdir -p .claude/memory/core .claude/memory/archival/decisions .claude/memory/archival/lessons .claude/memory/archival/user-research .claude/memory/recall

# 如果选择了 Profile，优先使用 Profile 的记忆模板
if [ -n "$SELECTED_PROFILE" ] && [ -d "$CLONE_DIR/profiles/$SELECTED_PROFILE/memory/core" ]; then
  cp "$CLONE_DIR"/profiles/$SELECTED_PROFILE/memory/core/* .claude/memory/core/ 2>/dev/null || true
  echo "   ✅ 记忆系统 (core from profile: $SELECTED_PROFILE + archival + recall)"
else
  if [ -d "$CLONE_DIR/memory/core" ]; then
    cp "$CLONE_DIR"/memory/core/* .claude/memory/core/ 2>/dev/null || true
    echo "   ✅ 记忆系统 (core + archival + recall)"
  fi
fi

# archival（始终使用通用版）
if [ -d "$CLONE_DIR/memory/archival" ]; then
  cp "$CLONE_DIR"/memory/archival/decisions/* .claude/memory/archival/decisions/ 2>/dev/null || true
  cp "$CLONE_DIR"/memory/archival/lessons/* .claude/memory/archival/lessons/ 2>/dev/null || true
  cp "$CLONE_DIR"/memory/archival/user-research/* .claude/memory/archival/user-research/ 2>/dev/null || true
fi

# 共享白板
mkdir -p .claude/blackboard
if [ -d "$CLONE_DIR/blackboard" ]; then
  cp "$CLONE_DIR"/blackboard/* .claude/blackboard/ 2>/dev/null || true
  echo "   ✅ 共享白板 (4 个文件)"
fi

# 评估体系
mkdir -p .claude/evals
if [ -d "$CLONE_DIR/evals" ]; then
  cp "$CLONE_DIR"/evals/* .claude/evals/ 2>/dev/null || true
  echo "   ✅ 评估体系"
fi

# 垂直落地配置（参考）
if [ -d "$CLONE_DIR/profiles" ]; then
  mkdir -p .claude/profiles
  cp -r "$CLONE_DIR"/profiles/* .claude/profiles/ 2>/dev/null || true
  echo "   ✅ 垂直 profile（参考配置）"
fi

# CLAUDE.md（优先使用 Profile 的模板）
if [ -n "$SELECTED_PROFILE" ] && [ -f "$CLONE_DIR/profiles/$SELECTED_PROFILE/CLAUDE.md.template" ]; then
  cp "$CLONE_DIR"/profiles/$SELECTED_PROFILE/CLAUDE.md.template .claude/CLAUDE.md
  echo "   ✅ CLAUDE.md (from profile: $SELECTED_PROFILE)"
elif [ -f "$CLONE_DIR/CLAUDE.md.template" ]; then
  cp "$CLONE_DIR"/CLAUDE.md.template .claude/CLAUDE.md
  echo "   ✅ CLAUDE.md (记忆入口)"
fi

# ─── Step 5: 安装 init.sh + examples ───
echo "🚀 [5/5] 安装初始化脚本..."
if [ -f "$CLONE_DIR/init.sh" ]; then
  cp "$CLONE_DIR"/init.sh .claude/init.sh
  chmod +x .claude/init.sh
  echo "   ✅ init.sh (交互式初始化)"
fi

# 使用示例 + 文档
if [ -d "$CLONE_DIR/examples" ]; then
  mkdir -p .claude/examples
  cp -r "$CLONE_DIR"/examples/* .claude/examples/ 2>/dev/null || true
  echo "   ✅ 使用示例"
fi
if [ -d "$CLONE_DIR/docs" ]; then
  mkdir -p .claude/docs
  cp -r "$CLONE_DIR"/docs/* .claude/docs/ 2>/dev/null || true
  echo "   ✅ 操作文档"
fi

# 快速启动脚本（按 Profile 选择）
if [ -n "$SELECTED_PROFILE" ] && [ -f "$CLONE_DIR/quickstart-$SELECTED_PROFILE.sh" ]; then
  cp "$CLONE_DIR"/quickstart-$SELECTED_PROFILE.sh .claude/quickstart.sh
  chmod +x .claude/quickstart.sh
  echo "   ✅ 快速启动脚本 (profile: $SELECTED_PROFILE)"
elif [ -f "$CLONE_DIR/quickstart-passive-income.sh" ]; then
  cp "$CLONE_DIR"/quickstart-passive-income.sh .claude/quickstart-passive-income.sh
  chmod +x .claude/quickstart-passive-income.sh
  echo "   ✅ 被动收入快速启动脚本"
fi

# 清理临时目录（本地仓库不删）
if [ "$CLONE_DIR" != "$SCRIPT_DIR" ] && [ -d "$CLONE_DIR" ]; then
  rm -rf "$CLONE_DIR"
fi

echo ""
echo "🎉 安装完成！"
echo ""
echo "已安装内容："
echo "  .claude/skills/        — 35 个 Skills"
echo "  .claude/agents/        — 9 个 Agent + WORKFLOW + 质疑协议"
echo "  .claude/memory/        — 三层记忆系统 (core + archival + recall)"
echo "  .claude/blackboard/    — 共享白板 (4 个文件)"
echo "  .claude/evals/         — 效果评估体系"
echo "  .claude/profiles/      — 垂直 profile（参考配置）"
echo "  .claude/examples/      — 使用示例"
echo "  .claude/docs/          — 操作文档"
echo "  .claude/CLAUDE.md      — 记忆入口 (@import core)"
echo "  .claude/init.sh        — 交互式初始化脚本"
if [ -n "$SELECTED_PROFILE" ]; then
  echo "  .claude/quickstart.sh  — 快速启动 ($SELECTED_PROFILE)"
fi
echo ""

# ─── Step 6: 自动初始化（非 --skip-init 时） ───
if [ -z "$SKIP_INIT" ] && [ -f ".claude/init.sh" ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⚡ 现在运行初始化，设置你的内容工厂信息"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  bash .claude/init.sh
fi

# ─── 被动收入 Profile 提示 ───
if [ "$SELECTED_PROFILE" = "passive-income-factory" ]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "💰 被动收入工厂已就绪！"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "快速启动（3 分钟配置）："
  echo "  bash .claude/quickstart.sh"
  echo ""
  echo "或直接在 Claude Code 中："
  echo "  @主编 帮我验证一个长青文选题"
  echo ""
  echo "📖 完整手册: .claude/docs/passive-income-blueprint.md"
  echo "📖 示例流程: .claude/examples/passive-income-flow.md"
else
  if [ -z "$SKIP_INIT" ]; then
    :
  else
    echo ""
    echo "下一步："
    echo "  1. 运行 bash .claude/init.sh 初始化你的内容工厂信息"
    echo "  2. 启动 Claude Code，输入 @主编 定义第一个内容选题"
  fi
fi
