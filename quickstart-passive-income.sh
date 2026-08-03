#!/bin/bash
# 被动收入工厂 — 快速启动指南
# 安装后运行此脚本，3 分钟配置完成，立即开始第一篇长青文
#
# 用法: bash .claude/quickstart-passive-income.sh

set -e

echo "💰 被动收入工厂 — 快速启动"
echo "==========================="
echo ""

# ─── 检查安装 ───
if [ ! -d ".claude/skills" ] || [ ! -d ".claude/agents" ]; then
  echo "❌ 未检测到内容工厂安装，请先运行: bash install.sh"
  exit 1
fi

echo "✅ 内容工厂已安装"
echo ""

# ─── Step 1: 个人信息 ───
echo "📝 [1/4] 基本信息配置"
echo "━━━━━━━━━━━━━━━━━━━━━━"

# 读取或询问笔名
AUTHOR_NAME=""
if [ -f ".claude/memory/core/project-context.md" ]; then
  AUTHOR_NAME=$(grep -oP '(?<=作者：).*' .claude/memory/core/project-context.md 2>/dev/null || true)
fi
if [ -z "$AUTHOR_NAME" ]; then
  read -p "你的笔名/作者名: " AUTHOR_NAME
fi
echo "   笔名: $AUTHOR_NAME"

# 读取或询问领域
DOMAIN=""
echo ""
echo "选择你的内容领域（输入数字）:"
echo "  1) AI/科技 — AI工具、效率提升、科技趋势"
echo "  2) 副业/赚钱 — 副业方法、被动收入、自由职业"
echo "  3) 职场/成长 — 职场技能、个人成长、时间管理"
echo "  4) 教育/学习 — 学习方法、考试技巧、知识管理"
echo "  5) 其他（自定义）"
read -p "选择 [1-5]: " domain_choice
case "$domain_choice" in
  1) DOMAIN="AI/科技"; KEYWORDS="AI写作工具,AI办公,效率工具,ChatGPT技巧" ;;
  2) DOMAIN="副业/赚钱"; KEYWORDS="被动收入,副业推荐,自由职业,网赚方法" ;;
  3) DOMAIN="职场/成长"; KEYWORDS="职场技能,时间管理,个人成长,沟通技巧" ;;
  4) DOMAIN="教育/学习"; KEYWORDS="学习方法,考试技巧,知识管理,笔记方法" ;;
  *) read -p "输入你的领域: " DOMAIN; read -p "输入3-5个核心关键词(逗号分隔): " KEYWORDS ;;
esac
echo "   领域: $DOMAIN"
echo "   核心关键词: $KEYWORDS"

# ─── Step 2: 平台账号 ───
echo ""
echo "📱 [2/4] 平台账号状态"
echo "━━━━━━━━━━━━━━━━━━━━━━"

PLATFORMS=()
echo "你已经注册了哪些平台？（可多选，空格分隔数字）"
echo "  1) 微信公众号"
echo "  2) 今日头条"
echo "  3) 知乎"
echo "  4) 小红书"
echo "  5) 抖音"
read -p "已注册平台 [如: 1 3 4]: " platform_choices

for choice in $platform_choices; do
  case "$choice" in
    1) PLATFORMS+=("公众号") ;;
    2) PLATFORMS+=("头条") ;;
    3) PLATFORMS+=("知乎") ;;
    4) PLATFORMS+=("小红书") ;;
    5) PLATFORMS+=("抖音") ;;
  esac
done

if [ ${#PLATFORMS[@]} -eq 0 ]; then
  echo "   ⚠️  尚未注册任何平台，建议先注册公众号（私域底盘）"
  echo "   📖 参考: docs/passive-income-blueprint.md → SOP-01 平台注册"
else
  echo "   已有平台: ${PLATFORMS[*]}"
fi

# 检查公众号粉丝数
FANS_COUNT=0
read -p "公众号当前粉丝数（没有填0）: " FANS_COUNT
if [ "$FANS_COUNT" -ge 500 ] 2>/dev/null; then
  echo "   ✅ 粉丝 ≥ 500，可开通流量主！"
else
  REMAIN=$((500 - FANS_COUNT))
  echo "   📈 还差 $REMAIN 粉丝开通流量主（500粉门槛）"
fi

# ─── Step 3: 变现管道选择 ───
echo ""
echo "💰 [3/4] 变现管道优先级"
echo "━━━━━━━━━━━━━━━━━━━━━━"

echo "选择你先启动的变现管道（推荐按顺序启动）:"
echo "  1) 流量分成 — 最简单，有粉就有收益（推荐首选）"
echo "  2) 付费专栏 — 知识星球/小报童（中期核心）"
echo "  3) 带货佣金 — 精选联盟/蒲公英（需要内容量支撑）"
echo "  4) 数字产品 — 模板/电子书/Prompt包（零边际成本）"
read -p "首选管道 [1-4]（默认1）: " pipeline_choice
pipeline_choice=${pipeline_choice:-1}
case "$pipeline_choice" in
  1) PIPELINE="流量分成"; NEXT_STEP="先专注涨粉到500→开通流量主" ;;
  2) PIPELINE="付费专栏"; NEXT_STEP="准备10篇干货文→开知识星球" ;;
  3) PIPELINE="带货佣金"; NEXTSTORE="先产出20+篇种草内容→开精选联盟" ;;
  4) PIPELINE="数字产品"; NEXT_STEP="整理你的模板/经验→打包上传面包多" ;;
esac
echo "   首选管道: $PIPELINE"

# ─── Step 4: 写入配置 ───
echo ""
echo "💾 [4/4] 写入配置到记忆系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 更新 project-context.md
if [ -f ".claude/memory/core/project-context.md" ]; then
  # 追加个人配置区
  cat >> .claude/memory/core/project-context.md <<EOF

## 个人配置（quickstart 生成）

- **笔名**：$AUTHOR_NAME
- **领域**：$DOMAIN
- **核心关键词**：$KEYWORDS
- **已有平台**：${PLATFORMS[*]}
- **公众号粉丝**：$FANS_COUNT
- **首选变现管道**：$PIPELINE
- **配置日期**：$(date +%Y-%m-%d)
EOF
  echo "   ✅ project-context.md 已更新"
fi

# 写入启动计划到黑板
mkdir -p .claude/blackboard
cat > .claude/blackboard/startup-plan.md <<EOF
# 被动收入启动计划

> 由 quickstart-passive-income.sh 于 $(date +%Y-%m-%d) 生成

## 基本信息

- 笔名: $AUTHOR_NAME
- 领域: $DOMAIN
- 核心关键词: $KEYWORDS
- 已有平台: ${PLATFORMS[*]}
- 公众号粉丝: $FANS_COUNT
- 首选管道: $PIPELINE

## 第 1 周：基础设施

- [ ] 注册/完善 5 大平台账号
- [ ] 安装 5118（SEO 验证）+ 壹伴（公众号排版）
- [ ] 用 @head-of-content 做第一个 SEO 选题验证
- [ ] 跑通 L0→L4 全流程，产出第一篇长青文

## 第 2-4 周：内容积累

- [ ] 日更 1-2 篇长青文（15 分钟人工/篇）
- [ ] 每篇做一鱼多吃分发（5 平台版本）
- [ ] 积累 20+ 篇长青内容
- [ ] 公众号粉丝冲刺 500（开通流量主）

## 第 5-8 周：变现启动

- [ ] 开通流量主（500 粉后）
- [ ] 启动 $PIPELINE 管道
- [ ] 开设知识星球/小报童
- [ ] 每周复盘搜索排名+收益数据

## 第 9-12 周：管道扩展

- [ ] 启动第 2-3 条变现管道
- [ ] 数字产品打包（面包多）
- [ ] 带货选品测试
- [ ] 月被动收入目标: ¥1000+

## 每日 30 分钟流程

\`\`\`
08:00  @head-of-content SEO 验证选题（5分钟确认）
08:05  L0-L4 全自动级联（AI 15 分钟）
08:20  人工终审+发布（5 分钟）
08:25  一鱼多吃分发确认（5 分钟）
\`\`\`
EOF
echo "   ✅ startup-plan.md 已写入黑板"

# ─── 完成 ───
echo ""
echo "🎉 快速启动配置完成！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 现在开始你的第一篇长青文："
echo ""
echo "  在 Claude Code 中输入："
echo "  @head-of-content 帮我验证一个选题：「$KEYWORDS」领域中最适合做长青文的关键词"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 完整操作手册: .claude/docs/passive-income-blueprint.md"
echo "📖 示例流程:     .claude/examples/passive-income-flow.md"
echo "📋 启动计划:     .claude/blackboard/startup-plan.md"
echo ""
echo "💡 关键提醒："
echo "  • 选题必须 SEO 验证，不写无人搜索的内容"
echo "  • 每篇内容必须做一鱼多吃（5 平台版本）"
echo "  • 先涨粉到 500 → 开通流量主 → 再扩展其他管道"
echo "  • 每天 30 分钟，坚持 12 周见效"
