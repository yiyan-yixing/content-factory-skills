---
name: "Content Illustration Plan / 文章配图规划"
description: "从文章内容自动识别配图点，规划配图类型和生成方式。当用户说'文章配图''正文配图''插图''配图规划''illustration'时触发。"
when_to_use: "需要为公众号/知乎文章正文生成配图时触发。在L3写手完成正文后、平台适配前执行。频次：on-demand，时间盒：10min"
allowed-tools:
  - Read
  - Write
  - Bash
disable-model-invocation: true
version: "1.0.0"
skill_id: "SKILL-365"
layer: "L3.5-视觉生产层"
---

# SKILL-365：文章配图规划

> 核心判断：文章正文配图不是"装饰"，是"信息增量"——一张好配图等于300字解释
> 与 SKILL-359（类比翻译）强联动：类比出现的地方就是概念图解的配图点

## 一、7类配图与生成方式

| 类型 | 识别信号 | 生成方式 | 尺寸 | 视觉选型 |
|------|---------|---------|------|---------|
| 架构图 | "架构/系统/模块/分层/三层/四层" | Pillow diagram(complex/layered) | 1080x720 | hierarchy × technical × brand-dark |
| 流程图 | "流程/步骤/链路→/触发/工作流" | Pillow diagram(flow) | 1080x720 | progression × technical × brand-dark |
| 数据对比图 | "对比/横评/VS/差异/优劣" | comparison_matrix / dataviz bar | 1080x720 | comparison × bold × brand-dark |
| 数据趋势图 | "趋势/曲线/回撤/因子/热力" | dataviz line/heatmap | 1080x720 | hierarchy × technical × brand-dark |
| 概念图解 | 类比出现时（"像/好比/可以理解为"） | FLUX底图 + Pillow类比映射 | 1080x720 | narrative × hand-drawn × warm |
| 截图标注 | "实测/IDE/终端/报错/配置" | Pillow标注(红框+箭头+文字) | 原始尺寸 | data-impact × technical × brand-dark |
| 信息图 | "清单/要点/N个/N条/框架" | Pillow diagram(infographic) | 1080x720 | dense-info × bold × brand-dark |

**尺寸规范**（区别于封面/卡片）：

| 平台 | 文章配图尺寸 | 比例 |
|------|------------|------|
| 公众号 | 1080×720 | 3:2横版 |
| 知乎 | 1080×720 | 3:2横版 |
| 小红书(正文图) | 1080×1080 | 1:1方形 |

## 二、配图识别信号

### 2.1 关键词信号

```python
ILLUSTRATION_SIGNALS = {
    "architecture": {
        "keywords": ["架构", "系统", "层次", "模块", "服务", "组件", "分层",
                     "技术栈", "微服务", "部署", "pipeline", "约束体系"],
        "diagram_type": "complex",
    },
    "flow": {
        "keywords": ["流程", "步骤", "时序", "过程", "工作流", "顺序",
                     "链路", "环节", "第一步", "然后", "接着", "最后", "触发"],
    },
    "data_comparison": {
        "keywords": ["对比", "比较", "VS", "vs", "横评", "差异", "优劣",
                     "高于", "低于", "排名", "占比"],
    },
    "data_trend": {
        "keywords": ["趋势", "曲线", "上升", "下降", "波动", "回撤",
                     "净值", "因子", "热力", "分布", "Sharpe"],
    },
    "concept": {
        "keywords": ["像", "好比", "可以理解为", "简单来说", "本质是",
                     "就像", "类似于", "相当于"],
    },
    "screenshot": {
        "keywords": ["截图", "实测", "IDE", "界面", "操作步骤",
                     "终端", "命令行", "报错", "配置界面"],
    },
    "infographic": {
        "keywords": ["清单", "要点", "框架", "N个", "N条",
                     "核心", "关键", "总结"],
    },
}
```

### 2.2 识别流程（3阶段）

**阶段1：结构扫描**（规则引擎）
1. H2/H3标题匹配信号关键词
2. 连续3段以上无配图且段落>200字，标记需要配图
3. 数据句检测：数字+对比/趋势关键词（"准确率从71%提升到89%"）
4. 类比句检测：SKILL-359的类比模式（"像""好比""可以理解为"）
5. 列表/步骤检测：编号列表或步骤关键词

**阶段2：内容提取**
- 配图类型（7种之一）
- 标题（取H2标题或段落首句核心观点）
- 数据项（数据图：数字和标签）
- 步骤/层次（流程/架构：结构化数据）
- 类比映射（概念图：源域和目标域）

**阶段3：LLM增强**（可选，调image-studio LLM，~2-5s）
- 对架构图/流程图/概念图配图点，用LLM拆解自然语言为结构化JSON
- 复用image-studio的Think Before Drawing引擎

## 三、配图密度规则

| 平台 | 每N字配1图 | 2000字文章约需 | 优先位置 |
|------|----------|--------------|---------|
| 公众号 | 500-800字 | 3-4张 | 每个H2节后 |
| 知乎 | 600-1000字 | 3-4张 | 核心论证处 |
| 小红书 | 300-500字 | 2-3张(正文图) | 类比+数据处 |

**密度规则优先级**：
1. 类比段后必须配概念图（SKILL-359类比锚定，最高优先级）
2. 数据段后必须配数据图
3. 架构/流程描述后必须配结构图
4. 密度不足时，优先在长段落（>300字）后补图

## 四、IllustrationPlan JSON格式

```json
{
  "article_id": "T1-004",
  "platform": "wechat",
  "illustrations": [
    {
      "fig_id": "T1-004-fig-01",
      "position": "after:h2-2",
      "fig_type": "architecture",
      "title": "Agent Harness 四层约束体系",
      "structure": "hierarchy",
      "render": "technical",
      "palette": "brand-dark",
      "diagram_data": {
        "items": [
          {"label": "原则层", "components": ["安全第一", "人类否决权"]},
          {"label": "宪法层", "components": ["Challenge Protocol", "Go/No-Go"]},
          {"label": "规则层", "components": ["Harness约束", "权限隔离"]},
          {"label": "判例层", "components": ["历史案例", "红线清单"]}
        ]
      },
      "size": [1080, 720],
      "output_path": "assets/figures/T1-004/T1-004-fig-01-arch.png"
    },
    {
      "fig_id": "T1-004-fig-02",
      "position": "after:para-5",
      "fig_type": "concept",
      "title": "Harness约束——像给马套上缰绳",
      "structure": "narrative",
      "render": "hand-drawn",
      "palette": "warm",
      "diagram_data": {
        "analogy_source": {"Agent": "强壮的马", "Harness": "缰绳", "无约束": "野马跑偏"},
        "analogy_target": {"约束体系": "方向控制", "Go/No-Go": "安全带"},
        "flux_prompt": "powerful horse with reins and bridle, dark background, golden accents, dramatic, digital art, no text",
        "blank_zone": "right"
      },
      "size": [1080, 720],
      "output_path": "assets/figures/T1-004/T1-004-fig-02-concept.png"
    }
  ]
}
```

## 五、与 SKILL-359（类比翻译）的联动

**类比锚定规则**：当文章中使用SKILL-359的类比构造公式时，自动标记为概念图解配图点。

| SKILL-359类比公式 | 概念图解映射 |
|-----------------|------------|
| `[技术概念]——像[日常场景]` | 左侧技术概念 + 右侧日常场景 + 映射线 |
| `[没有A的B]像[日常场景]——[后果]` | 对比图：有A的B vs 无A的B + 后果标注 |
| `[概念] = [日常场景]` | 等式图：概念 = 场景 + 详解 |

## 六、执行步骤

### Step 0: Prompt-File-First
1. 在 `prompts/{article_id}/` 创建配图规划文件
2. 每张配图一个文件: `NN-{type}-{slug}.md`

### Step 1: 识别配图点
1. 读取文章Markdown
2. 结构扫描：H2标题 + 段落密度 + 信号关键词
3. 类比锚定：SKILL-359类比模式检测
4. 密度控制：确保500-800字/图（公众号）
5. 输出 IllustrationPlan[]

### Step 2: 按类型路由生成
- 架构图/流程图/信息图 → `article_illustrator.py --type diagram`
- 数据对比/趋势图 → `dataviz_gen.py` / `comparison_matrix.py`
- 概念图解 → `article_illustrator.py --type concept`
- 截图标注 → `article_illustrator.py --type screenshot`

### Step 3: 品牌校验
- 色板：BRAND_RGB 一致性
- 字体：PingFang SC 中文渲染
- 尺寸：1080×720 或 1080×1080
- 水印：右下角 "一言一行"

### Step 4: 插入文章
- 按 IllustrationPlan.position 插入 `![标题](路径)` 到 Markdown
- 公众号版：调用 page_composer 嵌入配图

## 七、输出路径规范

| 类型 | 路径模式 |
|------|---------|
| 架构图 | `assets/figures/{article_id}/{fig_id}-arch.png` |
| 流程图 | `assets/figures/{article_id}/{fig_id}-flow.png` |
| 数据图 | `assets/figures/{article_id}/{fig_id}-data.png` |
| 概念图 | `assets/figures/{article_id}/{fig_id}-concept.png` |
| 截图标注 | `assets/figures/{article_id}/{fig_id}-screenshot.png` |
| 信息图 | `assets/figures/{article_id}/{fig_id}-info.png` |

## 自检清单

- [ ] 公众号文章是否有≥3张正文配图？
- [ ] 每个类比段后是否有概念图解？
- [ ] 数据段后是否有数据图？
- [ ] 架构/流程描述后是否有结构图？
- [ ] 配图尺寸是否为1080×720（公众号/知乎）或1080×1080（小红书）？
- [ ] 品牌色板是否统一（BRAND_RGB）？
- [ ] 中文字体是否正常渲染？
