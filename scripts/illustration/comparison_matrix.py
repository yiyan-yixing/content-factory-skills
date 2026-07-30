#!/usr/bin/env python3
"""
comparison_matrix.py -- 品牌统一横评对比表可视化

用 matplotlib 绘制结构化横评对比表，单元格按分数着色。

用法:
  python3 comparison_matrix.py \
    --title "5个AI编程工具横评" \
    --rows 'Cursor,Copilot,Cline,Aider,Continue' \
    --columns '代码补全,上下文理解,多文件编辑,终端集成,价格' \
    --scores '5,4,3,3,4;4,5,3,2,3;3,3,4,4,3;4,3,5,5,2;3,3,2,4,4' \
    --output figures/comparison.png \
    --brand-colors
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

# 品牌色板
BRAND = {
    'deep_blue': '#1a1a2e',
    'navy': '#16213e',
    'yellow': '#e9c46a',
    'white': '#ffffff',
    'red': '#e76f51',
    'positive': '#2a9d8f',
    'gray': '#8d99ae',
    'neutral': '#264653',
}

# 分数 -> 颜色映射 (5分制)
SCORE_COLORS = {
    5: '#e9c46a',  # 深黄 - 优秀
    4: '#f4d58d',  # 浅黄 - 良好
    3: '#8d99ae',  # 灰色 - 一般
    2: '#e76f51',  # 红色 - 较差
    1: '#a4243b',  # 深红 - 极差
}


def setup_brand_style():
    plt.rcParams.update({
        'font.sans-serif': ['PingFang SC', 'Heiti SC', 'STHeiti', 'sans-serif'],
        'axes.unicode_minus': False,
        'figure.facecolor': BRAND['deep_blue'],
        'axes.facecolor': BRAND['deep_blue'],
        'axes.edgecolor': BRAND['gray'],
        'axes.labelcolor': BRAND['white'],
        'xtick.color': BRAND['white'],
        'ytick.color': BRAND['white'],
        'text.color': BRAND['white'],
        'grid.color': BRAND['neutral'],
        'grid.alpha': 0.3,
    })


def get_score_color(score):
    """获取分数对应的单元格颜色"""
    return SCORE_COLORS.get(score, BRAND['gray'])


def get_text_color(bg_hex):
    """根据背景色亮度决定文字颜色"""
    try:
        r, g, b = mcolors.to_rgb(bg_hex)
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return BRAND['white'] if luminance < 0.55 else BRAND['deep_blue']
    except ValueError:
        return BRAND['white']


def gen_comparison_matrix(rows, columns, scores, title, output, size, brand):
    """横评对比表

    rows: 行标签列表
    columns: 列标签列表
    scores: 2D列表 [row][col], 整数1-5
    """
    if brand:
        setup_brand_style()

    n_rows = len(rows)
    n_cols = len(columns)
    w, h = size
    dpi = 120

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])
    ax.set_facecolor(BRAND['deep_blue'])
    ax.axis('off')

    # 表格参数
    cell_width = 1.0 / (n_cols + 1)  # +1 for row header
    cell_height = 0.8 / (n_rows + 1)  # +1 for column header

    # 左偏移（给行头留空间）
    x_start = cell_width
    y_bottom = 0.05

    # ---------- 列头 ----------
    header_color = BRAND['neutral']
    for j, col_name in enumerate(columns):
        x = x_start + j * cell_width
        rect = plt.Rectangle((x, y_bottom + n_rows * cell_height),
                              cell_width, cell_height,
                              facecolor=header_color, edgecolor=BRAND['gray'],
                              linewidth=1.2)
        ax.add_patch(rect)
        ax.text(x + cell_width / 2,
                y_bottom + n_rows * cell_height + cell_height / 2,
                col_name, ha='center', va='center',
                fontsize=10, fontweight='bold', color=BRAND['white'])

    # ---------- 行头 ----------
    row_header_color = BRAND['navy']
    for i, row_name in enumerate(rows):
        y = y_bottom + (n_rows - 1 - i) * cell_height
        rect = plt.Rectangle((0, y), cell_width, cell_height,
                              facecolor=row_header_color,
                              edgecolor=BRAND['gray'], linewidth=1.2)
        ax.add_patch(rect)
        ax.text(cell_width / 2, y + cell_height / 2,
                row_name, ha='center', va='center',
                fontsize=10, fontweight='bold', color=BRAND['yellow'])

    # ---------- 数据单元格 ----------
    for i in range(n_rows):
        for j in range(n_cols):
            score = scores[i][j]
            bg = get_score_color(score)
            text_c = get_text_color(bg)

            x = x_start + j * cell_width
            y = y_bottom + (n_rows - 1 - i) * cell_height

            rect = plt.Rectangle((x, y), cell_width, cell_height,
                                  facecolor=bg, edgecolor=BRAND['gray'],
                                  linewidth=1.0, alpha=0.85)
            ax.add_patch(rect)
            ax.text(x + cell_width / 2, y + cell_height / 2,
                    str(score), ha='center', va='center',
                    fontsize=14, fontweight='bold', color=text_c)

    # ---------- 左上角标题单元格 ----------
    title_cell_color = BRAND['deep_blue']
    rect = plt.Rectangle((0, y_bottom + n_rows * cell_height),
                          cell_width, cell_height,
                          facecolor=title_cell_color,
                          edgecolor=BRAND['gray'], linewidth=1.2)
    ax.add_patch(rect)

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, 1)

    # 主标题
    ax.text(0.5, 0.95, title, ha='center', va='bottom',
            fontsize=16, fontweight='bold', color=BRAND['yellow'],
            transform=ax.transAxes)

    # ---------- 图例 ----------
    legend_y = 0.01
    legend_x = 0.0
    legend_cell_w = 0.06
    legend_cell_h = 0.03
    for score_val in [5, 4, 3, 2, 1]:
        bg = get_score_color(score_val)
        text_c = get_text_color(bg)
        rect = plt.Rectangle((legend_x, legend_y),
                              legend_cell_w, legend_cell_h,
                              facecolor=bg, edgecolor=BRAND['gray'],
                              linewidth=0.5, alpha=0.85,
                              transform=ax.transAxes)
        ax.add_patch(rect)
        ax.text(legend_x + legend_cell_w / 2,
                legend_y + legend_cell_h / 2,
                str(score_val), ha='center', va='center',
                fontsize=7, fontweight='bold', color=text_c,
                transform=ax.transAxes)
        legend_x += legend_cell_w + 0.01

    # 图例标签
    labels_map = {5: '优秀', 4: '良好', 3: '一般', 2: '较差', 1: '极差'}
    legend_x = 0.0
    for score_val in [5, 4, 3, 2, 1]:
        ax.text(legend_x + legend_cell_w + 0.01,
                legend_y + legend_cell_h / 2,
                labels_map[score_val], ha='left', va='center',
                fontsize=6, color=BRAND['white'],
                transform=ax.transAxes)
        legend_x += legend_cell_w + 0.01 + len(labels_map[score_val]) * 0.012 + 0.01

    plt.tight_layout()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f"Comparison matrix saved: {output} ({w}x{h})")


def main():
    parser = argparse.ArgumentParser(
        description='Comparison Matrix Generator')
    parser.add_argument('--title', default='Comparison', help='表格标题')
    parser.add_argument('--rows', required=True, help='行标签，逗号分隔')
    parser.add_argument('--columns', required=True, help='列标签，逗号分隔')
    parser.add_argument('--scores', required=True,
                        help='分数矩阵，行间用分号分隔，列间用逗号分隔')
    parser.add_argument('--output', required=True, help='输出PNG路径')
    parser.add_argument('--size', default='1200x800', help='宽x高')
    parser.add_argument('--brand-colors', action='store_true',
                        help='使用品牌色板')
    args = parser.parse_args()

    rows = args.rows.split(',')
    columns = args.columns.split(',')
    try:
        scores = [[int(v) for v in row.split(',')]
                  for row in args.scores.split(';')]
    except ValueError as e:
        parser.error(f'invalid score value (must be integer 1-5): {e}')

    # 分数范围校验
    for i, row in enumerate(scores):
        for j, v in enumerate(row):
            if v < 1 or v > 5:
                parser.error(f'score at [{i}][{j}] = {v}, must be 1-5')

    # size 解析
    size_str = args.size.replace('x', ',')
    parts = size_str.split(',')
    if len(parts) != 2:
        parser.error(f'--size must be WxH or W,H, got: {args.size}')
    try:
        w, h = int(parts[0]), int(parts[1])
    except ValueError:
        parser.error(f'invalid size values: {args.size}')
    if w <= 0 or h <= 0:
        parser.error('size must be positive')
    size = (w, h)

    if len(scores) != len(rows):
        parser.error(f'{len(rows)} row labels but {len(scores)} score rows')
    for i, row in enumerate(scores):
        if len(row) != len(columns):
            parser.error(f'row {i} has {len(row)} scores but '
                         f'{len(columns)} columns')

    gen_comparison_matrix(rows, columns, scores, args.title,
                          args.output, size, args.brand_colors)


if __name__ == '__main__':
    main()
