# content-xhs-cards · 触发评估（skill-creator eval 试点）

> 试点日期：2026-07-30 ｜ 工具：`reference/anthropic-skills/skills/skill-creator`（依赖 `claude -p`，本地 v2.1.220 可用）

## 试点结论

**eval 的价值兑现：用 `failed_queries` 逼出并修复了本 skill 的三个真实元数据缺陷**（这些缺陷在真实安装/多 skill 共存时都会出问题）：

| # | 缺陷 | 修复 |
|---|---|---|
| 1 | `name: "Content XHS Cards / 小红书图文卡片组"` —— 含 `/` 空格中文，**违反 kebab-case 规范**；run_eval 用 name 拼 command 文件名，`/` 被当目录 → 文件创建失败 → 全 query `failed` | → `name: "content-xhs-cards"` |
| 2 | `disable-model-invocation: true` —— description 写了触发词却禁止自动触发，**自相矛盾** | → 已移除 |
| 3 | 触发条件误放进 `when_to_use`（自定义字段），系统只认 `description` | → 并入 `description`，改 pushy 版 |

**触发率测量**（name 修复后 `failed_queries=0`，工具链跑通）：应触发 5/5 触发率仍 0%。
- 根因判断：run_eval 用 `.claude/commands/` 模拟 skill availability，而 Claude 对 **command** 不会像对真 skill 那样主动 consult（skill-creator 文档预告：Claude 只在"自己做不好"时 consult skill）。
- **更可靠验证**（留后续）：`run_loop.py` 自动优化（train/test + 迭代 5 轮），或真实安装到 `.claude/skills/` 后观察。

## 怎么跑

### 测当前 description 触发率（快）
```bash
cd reference/anthropic-skills/skills/skill-creator
python3 -m scripts.run_eval \
  --eval-set   workshop/content-factory-skills/skills/content-xhs-cards/evals/trigger-eval.json \
  --skill-path workshop/content-factory-skills/skills/content-xhs-cards \
  --runs-per-query 3 --num-workers 5 --verbose
```

### 自动优化 description（重，跑前先测 baseline）
```bash
python3 -m scripts.run_loop \
  --eval-set   workshop/content-factory-skills/skills/content-xhs-cards/evals/trigger-eval.json \
  --skill-path workshop/content-factory-skills/skills/content-xhs-cards \
  --model <session-model-id> \
  --max-iterations 5 --verbose
```
> 输出 HTML 报告 + `best_description`（按 held-out test score 选，防过拟合）。

## 扩展到其余 skill

每个 skill 复制本目录结构，改 `trigger-eval.json` 的 query。**跑前先体检三件事**：
1. `name` 是 kebab-case 小写（无 `/` 空格中文）
2. 触发条件在 `description` 里（不在 `when_to_use`），且 pushy
3. 没有 `disable-model-invocation: true`（除非刻意要手动触发）
