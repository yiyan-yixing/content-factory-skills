#!/usr/bin/env python3
"""
article_illustrator.py — 文章正文配图生成 CLI

从文章内容识别配图点，或根据参数生成单张配图。
支持双模式：image-studio API（优先）+ Pillow fallback。

用法:
  # 自动模式：从文章识别配图点并生成
  python3 article_illustrator.py \
    --article-id T1-004 \
    --article pipeline/writing/T1-004/draft-v1.md \
    --platform wechat \
    --output-dir assets/figures/T1-004/ \
    --auto

  # 单张架构图
  python3 article_illustrator.py \
    --article-id T1-004 \
    --type architecture \
    --title "Agent Harness 四层约束体系" \
    --items '原则层:安全第一,人类否决权;宪法层:Challenge Protocol,Go/No-Go;规则层:Harness约束,权限隔离;判例层:历史案例,红线清单' \
    --output assets/figures/T1-004/T1-004-fig-01-arch.png

  # 单张流程图
  python3 article_illustrator.py \
    --article-id T1-004 \
    --type flow \
    --title "Go/No-Go 判定流程" \
    --items 'OOS回测;风险检查;一致性检查;Go/No-Go判定' \
    --output assets/figures/T1-004/T1-004-fig-02-flow.png

  # 单张概念图（FLUX底图+Pillow文字）
  python3 article_illustrator.py \
    --article-id T1-004 \
    --type concept \
    --title "Harness=缰绳" \
    --concept-left "Agent:Harness:无约束" \
    --concept-right "马:缰绳:野马跑偏" \
    --flux-prompt "powerful horse with reins, dark background, golden" \
    --output assets/figures/T1-004/T1-004-fig-03-concept.png
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 公共模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_common import BRAND_RGB, find_font, create_gradient_bg

# ── 品牌色板 ──────────────────────────────────────
BRAND = BRAND_RGB

# 文章配图尺寸
SIZE_WECHAT = (1080, 720)
SIZE_XHS = (1080, 1080)
SIZE_ZHIHU = (1080, 720)

# diagram 主题（从 image-studio DIAGRAM_THEMES 对齐）
DIAGRAM_THEMES = {
    "dark": {
        "bg": "#1a1a2e",
        "card_bg": "#16213e",
        "card_border": "#2a2a4a",
        "text_primary": "#e9c46a",
        "text_secondary": "#cccccc",
        "accent": "#2a9d8f",
        "arrow": "#e9c46a",
        "line": "#2a2a4a",
    },
    "blue": {
        "bg": "#0d1117",
        "card_bg": "#161b22",
        "card_border": "#30363d",
        "text_primary": "#58a6ff",
        "text_secondary": "#c9d1d9",
        "accent": "#1f6feb",
        "arrow": "#58a6ff",
        "line": "#30363d",
    },
}

# ── 配图识别信号 ──────────────────────────────────
ILLUSTRATION_SIGNALS = {
    "architecture": ["架构", "系统", "层次", "模块", "分层", "组件", "约束体系", "技术栈", "pipeline"],
    "flow": ["流程", "步骤", "链路", "触发", "工作流", "时序", "环节", "第一步"],
    "data_comparison": ["对比", "VS", "vs", "横评", "差异", "优劣", "高于", "低于"],
    "data_trend": ["趋势", "曲线", "回撤", "因子", "热力", "分布", "Sharpe", "波动"],
    "concept": ["像", "好比", "可以理解为", "就像", "类似于", "相当于"],
    "screenshot": ["截图", "实测", "IDE", "终端", "报错"],
    "infographic": ["清单", "要点", "框架", "关键", "核心"],
}


# ══════════════════════════════════════════════════
# 辅助绘图函数
# ══════════════════════════════════════════════════

def _hex_to_rgb(hex_color):
    """#rrggbb -> (r, g, b)"""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_arrow_down(draw, x, y1, y2, color, width=2, head_size=10):
    draw.line([(x, y1), (x, y2 - head_size)], fill=color, width=width)
    draw.polygon([
        (x, y2),
        (x - head_size, y2 - head_size * 1.5),
        (x + head_size, y2 - head_size * 1.5),
    ], fill=color)


def _draw_arrow_right(draw, x1, y, x2, color, width=2, head_size=8):
    draw.line([(x1, y), (x2 - head_size, y)], fill=color, width=width)
    draw.polygon([
        (x2, y),
        (x2 - head_size, y - head_size * 1.2),
        (x2 - head_size, y + head_size * 1.2),
    ], fill=color)


# ══════════════════════════════════════════════════
# 架构图（分层方框 + 箭头）
# ══════════════════════════════════════════════════

def draw_architecture(title, layers, theme_name="dark", size=SIZE_WECHAT):
    """
    绘制分层架构图。
    layers: [{"label": "原则层", "components": ["安全第一", "人类否决权"]}, ...]
    """
    theme = DIAGRAM_THEMES.get(theme_name, DIAGRAM_THEMES["dark"])
    w, h = size

    img = Image.new('RGB', (w, h), _hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)

    # 标题
    title_font = find_font(36)
    draw.text((40, 25), title, fill=_hex_to_rgb(theme["text_primary"]), font=title_font)

    # 计算每层高度
    n_layers = len(layers)
    top_margin = 80
    bottom_margin = 30
    gap = 20
    available_h = h - top_margin - bottom_margin - (n_layers - 1) * gap
    layer_h = min(available_h // n_layers, 120)

    # 层起始Y
    start_y = top_margin + (available_h - n_layers * layer_h - (n_layers - 1) * gap) // 2

    for i, layer in enumerate(layers):
        y = start_y + i * (layer_h + gap)

        # 层卡片
        _draw_rounded_rect(draw, [60, y, w - 60, y + layer_h], radius=12,
                          fill=_hex_to_rgb(theme["card_bg"]),
                          outline=_hex_to_rgb(theme["card_border"]), width=2)

        # 左侧色条
        _draw_rounded_rect(draw, [60, y, 72, y + layer_h], radius=4,
                          fill=_hex_to_rgb(theme["accent"]))

        # 层名
        label_font = find_font(28)
        draw.text((90, y + 12), layer["label"], fill=_hex_to_rgb(theme["text_primary"]),
                 font=label_font)

        # 组件标签
        comp_font = find_font(22)
        components = layer.get("components", [])
        comp_x = 90
        comp_y = y + 55
        for j, comp in enumerate(components):
            comp_w = len(comp) * 22 + 20
            if comp_x + comp_w > w - 80:
                comp_x = 90
                comp_y += 32

            _draw_rounded_rect(draw, [comp_x, comp_y, comp_x + comp_w, comp_y + 26],
                              radius=6, fill=_hex_to_rgb(theme["line"]),
                              outline=_hex_to_rgb(theme["card_border"]), width=1)
            draw.text((comp_x + 10, comp_y + 2), comp, fill=_hex_to_rgb(theme["text_secondary"]),
                     font=comp_font)
            comp_x += comp_w + 10

        # 层间箭头
        if i < n_layers - 1:
            arrow_y1 = y + layer_h
            arrow_y2 = y + layer_h + gap
            _draw_arrow_down(draw, w // 2, arrow_y1, arrow_y2,
                           _hex_to_rgb(theme["arrow"]), width=2, head_size=8)

    # 品牌水印
    watermark_font = find_font(16)
    draw.text((w - 120, h - 25), "一言一行", fill=_hex_to_rgb(theme["line"]),
             font=watermark_font)

    return img


# ══════════════════════════════════════════════════
# 流程图（纵向方框 + 箭头）
# ══════════════════════════════════════════════════

def draw_flow(title, steps, theme_name="dark", size=SIZE_WECHAT):
    """
    绘制流程图。
    steps: ["OOS回测", "风险检查", "一致性检查", "Go/No-Go判定"]
    """
    theme = DIAGRAM_THEMES.get(theme_name, DIAGRAM_THEMES["dark"])
    w, h = size

    img = Image.new('RGB', (w, h), _hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)

    # 标题
    title_font = find_font(36)
    draw.text((40, 25), title, fill=_hex_to_rgb(theme["text_primary"]), font=title_font)

    # 计算每步高度
    n_steps = len(steps)
    top_margin = 80
    bottom_margin = 30
    gap = 30
    available_h = h - top_margin - bottom_margin - (n_steps - 1) * gap
    step_h = min(available_h // n_steps, 80)

    start_y = top_margin + (available_h - n_steps * step_h - (n_steps - 1) * gap) // 2

    center_x = w // 2
    box_w = 360

    for i, step in enumerate(steps):
        y = start_y + i * (step_h + gap)
        box_left = center_x - box_w // 2
        box_right = center_x + box_w // 2

        # 步骤编号圆
        circle_r = 18
        circle_x = box_left - 40
        circle_y = y + step_h // 2
        draw.ellipse([circle_x - circle_r, circle_y - circle_r,
                     circle_x + circle_r, circle_y + circle_r],
                    fill=_hex_to_rgb(theme["accent"]))
        num_font = find_font(20)
        draw.text((circle_x - 6, circle_y - 10), str(i + 1),
                 fill=_hex_to_rgb(theme["bg"]), font=num_font)

        # 步骤方框
        is_last = (i == n_steps - 1)
        fill_color = _hex_to_rgb(theme["accent"]) if is_last else _hex_to_rgb(theme["card_bg"])
        text_color = _hex_to_rgb(theme["bg"]) if is_last else _hex_to_rgb(theme["text_primary"])

        _draw_rounded_rect(draw, [box_left, y, box_right, y + step_h], radius=12,
                          fill=fill_color,
                          outline=_hex_to_rgb(theme["card_border"]), width=2)

        # 步骤文字
        step_font = find_font(26)
        text_w = draw.textlength(step, font=step_font)
        draw.text((center_x - text_w // 2, y + (step_h - 26) // 2), step,
                 fill=text_color, font=step_font)

        # 步骤间箭头
        if i < n_steps - 1:
            _draw_arrow_down(draw, center_x, y + step_h, y + step_h + gap,
                           _hex_to_rgb(theme["arrow"]), width=2, head_size=8)

    # 品牌水印
    watermark_font = find_font(16)
    draw.text((w - 120, h - 25), "一言一行", fill=_hex_to_rgb(theme["line"]),
             font=watermark_font)

    return img


# ══════════════════════════════════════════════════
# 概念图解（左右类比映射）
# ══════════════════════════════════════════════════

def draw_concept(title, left_items, right_items, theme_name="dark", size=SIZE_WECHAT):
    """
    绘制概念图解（左右类比映射）。
    left_items: ["Agent", "Harness", "无约束"]  (技术概念)
    right_items: ["马", "缰绳", "野马跑偏"]     (日常类比)
    """
    theme = DIAGRAM_THEMES.get(theme_name, DIAGRAM_THEMES["dark"])
    w, h = size

    img = Image.new('RGB', (w, h), _hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)

    # 标题
    title_font = find_font(32)
    draw.text((40, 20), title, fill=_hex_to_rgb(theme["text_primary"]), font=title_font)

    # 分割线
    mid_x = w // 2
    draw.line([(mid_x, 70), (mid_x, h - 30)], fill=_hex_to_rgb(theme["line"]), width=1)

    # 列标题
    col_font = find_font(22)
    draw.text((mid_x // 2 - 40, 55), "技术概念", fill=_hex_to_rgb(theme["accent"]), font=col_font)
    draw.text((mid_x + mid_x // 2 - 40, 55), "日常类比", fill=_hex_to_rgb(theme["text_primary"]),
             font=col_font)

    # 映射项
    n_items = min(len(left_items), len(right_items))
    item_font = find_font(26)
    label_font = find_font(18)

    top_y = 100
    gap = 20
    available = h - top_y - 60
    item_h = min((available - (n_items - 1) * gap) // n_items, 140)

    for i in range(n_items):
        y = top_y + i * (item_h + gap)

        # 左侧卡片（技术概念）
        _draw_rounded_rect(draw, [40, y, mid_x - 30, y + item_h], radius=10,
                          fill=_hex_to_rgb(theme["card_bg"]),
                          outline=_hex_to_rgb(theme["accent"]), width=2)
        draw.text((60, y + 12), left_items[i], fill=_hex_to_rgb(theme["text_primary"]),
                 font=item_font)

        # 右侧卡片（日常类比）
        _draw_rounded_rect(draw, [mid_x + 30, y, w - 40, y + item_h], radius=10,
                          fill=_hex_to_rgb(theme["card_bg"]),
                          outline=_hex_to_rgb(theme["card_border"]), width=2)
        draw.text((mid_x + 50, y + 12), right_items[i], fill=_hex_to_rgb(theme["text_secondary"]),
                 font=item_font)

        # 映射箭头
        arrow_y = y + item_h // 2
        _draw_arrow_right(draw, mid_x - 25, arrow_y, mid_x + 25,
                         _hex_to_rgb(theme["arrow"]), width=2, head_size=6)

        # 映射标签
        draw.text((mid_x - 8, arrow_y - 20), "=", fill=_hex_to_rgb(theme["arrow"]),
                 font=label_font)

    # 品牌水印
    watermark_font = find_font(16)
    draw.text((w - 120, h - 25), "一言一行", fill=_hex_to_rgb(theme["line"]),
             font=watermark_font)

    return img


# ══════════════════════════════════════════════════
# 信息图（清单/要点）
# ══════════════════════════════════════════════════

def draw_infographic(title, items, theme_name="dark", size=SIZE_WECHAT):
    """
    绘制信息图/清单图。
    items: [{"icon": "✅", "text": "OOS Sharpe >= 1.0"}, ...]
           或简单字符串列表
    """
    theme = DIAGRAM_THEMES.get(theme_name, DIAGRAM_THEMES["dark"])
    w, h = size

    img = Image.new('RGB', (w, h), _hex_to_rgb(theme["bg"]))
    draw = ImageDraw.Draw(img)

    # 标题
    title_font = find_font(36)
    draw.text((40, 20), title, fill=_hex_to_rgb(theme["text_primary"]), font=title_font)

    # 信息项
    n_items = len(items)
    top_y = 75
    gap = 10
    available = h - top_y - 40
    item_h = min((available - (n_items - 1) * gap) // n_items, 80)

    item_font = find_font(24)
    num_font = find_font(20)

    for i, item in enumerate(items):
        y = top_y + i * (item_h + gap)

        # 交替背景
        bg = _hex_to_rgb(theme["card_bg"]) if i % 2 == 0 else _hex_to_rgb(theme["bg"])
        _draw_rounded_rect(draw, [40, y, w - 40, y + item_h], radius=8,
                          fill=bg, outline=_hex_to_rgb(theme["card_border"]), width=1)

        # 编号
        circle_r = 14
        cx, cy = 75, y + item_h // 2
        draw.ellipse([cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r],
                    fill=_hex_to_rgb(theme["accent"]))
        draw.text((cx - 5, cy - 9), str(i + 1), fill=_hex_to_rgb(theme["bg"]), font=num_font)

        # 文字
        text = item if isinstance(item, str) else item.get("text", "")
        draw.text((100, y + (item_h - 24) // 2), text,
                 fill=_hex_to_rgb(theme["text_secondary"]), font=item_font)

    # 品牌水印
    watermark_font = find_font(16)
    draw.text((w - 120, h - 25), "一言一行", fill=_hex_to_rgb(theme["line"]),
             font=watermark_font)

    return img


# ══════════════════════════════════════════════════
# 配图识别
# ══════════════════════════════════════════════════

def detect_illustration_points(article_path, platform="wechat"):
    """从文章Markdown识别配图点，返回IllustrationPlan列表"""
    with open(article_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 优先取父目录名（pipeline/writing/T1-004/draft-v1.md → T1-004），否则取文件名
    parent_name = Path(article_path).parent.name
    article_id = parent_name if re.match(r'^[A-Z]+-\d+', parent_name) else Path(article_path).stem.replace("draft-", "")
    illustrations = []
    paragraphs = re.split(r'\n{2,}', content)

    # 密度控制
    density_map = {"wechat": 600, "zhihu": 800, "xiaohongshu": 400}
    chars_per_fig = density_map.get(platform, 600)

    char_count = 0
    fig_count = 0

    for i, para in enumerate(paragraphs):
        char_count += len(para)

        # 检查各类信号
        detected_type = None
        for sig_type, keywords in ILLUSTRATION_SIGNALS.items():
            if any(kw in para for kw in keywords):
                detected_type = sig_type
                break

        # 密度触发
        need_fig = char_count >= chars_per_fig * (fig_count + 1)

        if detected_type or (need_fig and len(para) > 200):
            fig_count_val = fig_count + 1
            fig_id = f"{article_id}-fig-{fig_count_val:02d}"

            fig_type = detected_type or "infographic"

            # 从段落提取标题：优先H2/H3标题，否则取首句
            h2_match = re.match(r'^#+\s+(.+)', para)
            if h2_match:
                title = h2_match.group(1).strip()
            else:
                # 取首句（到句号/问号/感叹号），中文30字/英文60字符
                first_sentence = re.split(r'[。？！\.\?\!]', para.strip())[0]
                has_cjk = any('一' <= c <= '鿿' for c in first_sentence)
                title = first_sentence[:60 if not has_cjk else 30].strip()
            # 清理 Markdown 标记
            title = re.sub(r'\*\*|__|`', '', title)

            illustrations.append({
                "fig_id": fig_id,
                "position": f"after:para-{i}",
                "fig_type": fig_type,
                "title": title,
                "char_position": char_count,
            })

            fig_count = fig_count_val

    return {
        "article_id": article_id,
        "platform": platform,
        "illustrations": illustrations,
    }


# ══════════════════════════════════════════════════
# 解析 --items 参数
# ══════════════════════════════════════════════════

def parse_items(items_str):
    """
    解析 --items 参数。
    格式1（架构图）: "原则层:安全第一,人类否决权;宪法层:Challenge Protocol,Go/No-Go"
    格式2（流程图/信息图）: "OOS回测;风险检查;一致性检查;Go/No-Go判定"
    """
    if ':' in items_str and ';' in items_str:
        # 架构图格式
        layers = []
        for layer_str in items_str.split(';'):
            parts = layer_str.split(':')
            label = parts[0].strip()
            components = [c.strip() for c in parts[1].split(',')] if len(parts) > 1 else []
            layers.append({"label": label, "components": components})
        return {"type": "architecture", "data": layers}
    elif ';' in items_str:
        # 流程图/信息图格式
        items = [s.strip() for s in items_str.split(';')]
        return {"type": "flow_or_info", "data": items}
    else:
        # 单项
        return {"type": "single", "data": [items_str.strip()]}


# ══════════════════════════════════════════════════
# 主入口
# ══════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='文章正文配图生成')
    parser.add_argument('--article-id', required=True, help='文章ID，如 T1-004')
    parser.add_argument('--article', help='文章Markdown路径（auto模式必填）')
    parser.add_argument('--platform', default='wechat', choices=['wechat', 'zhihu', 'xiaohongshu'])
    parser.add_argument('--output-dir', help='输出目录（auto模式）')
    parser.add_argument('--auto', action='store_true', help='自动识别配图点并生成')
    parser.add_argument('--type', choices=['architecture', 'flow', 'concept', 'infographic', 'auto'],
                       help='配图类型')
    parser.add_argument('--title', help='配图标题')
    parser.add_argument('--items', help='配图数据（架构: 层:组件,组件;层:组件 / 流程: 步骤;步骤）')
    parser.add_argument('--concept-left', help='概念图左侧（技术概念，冒号分隔）')
    parser.add_argument('--concept-right', help='概念图右侧（日常类比，冒号分隔）')
    parser.add_argument('--flux-prompt', help='FLUX英文prompt（概念图底图）')
    parser.add_argument('--theme', default='dark', choices=['dark', 'blue'], help='视觉主题')
    parser.add_argument('--output', help='输出文件路径')
    parser.add_argument('--size', default='wechat', choices=['wechat', 'xhs', 'zhihu'], help='图片尺寸')

    args = parser.parse_args()

    # 尺寸映射
    size_map = {"wechat": SIZE_WECHAT, "xhs": SIZE_XHS, "zhihu": SIZE_ZHIHU}
    img_size = size_map.get(args.size, SIZE_WECHAT)

    if args.auto:
        # 自动模式：识别 + 生成
        if not args.article:
            parser.error("--auto 模式需要 --article 参数")
        if not args.output_dir:
            args.output_dir = f"assets/figures/{args.article_id}"
        os.makedirs(args.output_dir, exist_ok=True)

        plan = detect_illustration_points(args.article, args.platform)
        # CLI 传入的 --article-id 优先于自动推断
        plan["article_id"] = args.article_id
        for ill in plan["illustrations"]:
            ill["fig_id"] = ill["fig_id"].replace(ill["fig_id"].split("-fig-")[0], args.article_id)
        print(json.dumps(plan, ensure_ascii=False, indent=2))

        # 生成配图
        for ill in plan["illustrations"]:
            out_path = os.path.join(args.output_dir, f"{ill['fig_id']}-{ill['fig_type'][:4]}.png")
            # 根据类型调用不同生成器
            if ill["fig_type"] in ("architecture", "data_comparison"):
                img = draw_architecture(ill["title"], [{"label": ill["title"], "components": []}],
                                       theme_name=args.theme, size=img_size)
                img.save(out_path, 'PNG')
                print(f"Generated: {out_path}")
            elif ill["fig_type"] == "flow":
                img = draw_flow(ill["title"], [ill["title"]],
                              theme_name=args.theme, size=img_size)
                img.save(out_path, 'PNG')
                print(f"Generated: {out_path}")
            elif ill["fig_type"] == "concept":
                img = draw_concept(ill["title"], [ill["title"]], ["类比"],
                                 theme_name=args.theme, size=img_size)
                img.save(out_path, 'PNG')
                print(f"Generated: {out_path}")
            else:
                img = draw_infographic(ill["title"], [ill["title"]],
                                      theme_name=args.theme, size=img_size)
                img.save(out_path, 'PNG')
                print(f"Generated: {out_path}")

        return

    # 单张生成模式
    if not args.type or not args.title:
        parser.error("单张模式需要 --type 和 --title 参数")

    if args.type == "architecture":
        if not args.items:
            parser.error("架构图需要 --items 参数")
        parsed = parse_items(args.items)
        if parsed["type"] == "architecture":
            layers = parsed["data"]
        else:
            layers = [{"label": args.title, "components": parsed["data"]}]
        img = draw_architecture(args.title, layers, theme_name=args.theme, size=img_size)

    elif args.type == "flow":
        if not args.items:
            parser.error("流程图需要 --items 参数")
        parsed = parse_items(args.items)
        steps = parsed["data"] if parsed["type"] in ("flow_or_info", "single") else [args.title]
        img = draw_flow(args.title, steps, theme_name=args.theme, size=img_size)

    elif args.type == "concept":
        left = args.concept_left.split(':') if args.concept_left else [args.title]
        right = args.concept_right.split(':') if args.concept_right else ["类比"]
        img = draw_concept(args.title, left, right, theme_name=args.theme, size=img_size)

    elif args.type == "infographic":
        if not args.items:
            parser.error("信息图需要 --items 参数")
        parsed = parse_items(args.items)
        items = parsed["data"] if parsed["type"] in ("flow_or_info", "single") else [args.title]
        img = draw_infographic(args.title, items, theme_name=args.theme, size=img_size)

    else:
        parser.error(f"未知类型: {args.type}")

    # 保存
    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        img.save(args.output, 'PNG')
        print(f"Saved: {args.output} ({img.size[0]}x{img.size[1]})")
    else:
        print("Warning: no --output specified, image not saved")


if __name__ == '__main__':
    main()
