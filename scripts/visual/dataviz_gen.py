#!/usr/bin/env python3
"""
dataviz_gen.py -- 品牌统一数据可视化生成

读取JSON数据，用品牌色板生成matplotlib图表PNG。

支持图表类型:
  bar      - 水平柱状图
  pie      - 饼图
  line     - 折线图/净值曲线
  drawdown - 回撤水位图
  funnel   - 漏斗图
  heatmap  - 热力图

用法:
  python3 dataviz_gen.py \
    --type bar \
    --data '[["H001",-2.17],["H002",-2.45],["H004",0.1]]' \
    --columns '策略,OOS Sharpe' \
    --title '17个策略OOS Sharpe对比' \
    --output biz/content/assets/figures/T1-004/sharpe-comparison.png \
    --size 1080x1440 \
    --brand-colors
"""

import argparse
import json
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


def _save_fig(fig, output, dpi=120):
    """通用保存逻辑"""
    plt.tight_layout()
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=dpi, facecolor=fig.get_facecolor(),
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)


# ---------- bar ----------

def gen_bar(data, columns, title, output, size, brand):
    """水平柱状图"""
    if brand:
        setup_brand_style()

    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    w, h = size
    dpi = 120

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])
    ax.set_facecolor(BRAND['deep_blue'])

    # 按值着色：负值红色，正值黄色
    colors = [BRAND['red'] if v < 0 else BRAND['yellow'] for v in values]
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=colors, height=0.6, edgecolor='none')

    # 数值标注
    for bar, val in zip(bars, values):
        x_pos = bar.get_width()
        offset = 0.08 if val >= 0 else -0.08
        ha = 'left' if val >= 0 else 'right'
        ax.text(x_pos + offset, bar.get_y() + bar.get_height() / 2,
                f'{val:.2f}', va='center', ha=ha,
                color=BRAND['white'], fontsize=9, fontweight='bold')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_title(title, fontsize=16, fontweight='bold',
                 color=BRAND['yellow'], pad=20)
    ax.axvline(x=1.0, color=BRAND['positive'], linestyle='--',
               alpha=0.6, linewidth=1.5, label='Go threshold')
    ax.axvline(x=0.0, color=BRAND['gray'], linestyle='-', alpha=0.4, linewidth=0.8)
    ax.legend(facecolor=BRAND['deep_blue'], edgecolor=BRAND['neutral'],
              labelcolor=BRAND['white'], fontsize=10)
    ax.grid(axis='x', alpha=0.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    _save_fig(fig, output, dpi)
    print(f"Bar chart saved: {output} ({w}x{h})")


# ---------- pie ----------

def gen_pie(data, columns, title, output, size, brand):
    """饼图"""
    if brand:
        setup_brand_style()

    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    w, h = size
    dpi = 120

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])

    base_colors = [BRAND['yellow'], BRAND['red'], BRAND['positive'],
                  BRAND['neutral'], '#457b9d', '#a8dadc']
    pie_colors = (base_colors * ((len(labels) // len(base_colors)) + 1))[:len(labels)]
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=pie_colors,
        autopct='%1.1f%%', startangle=90,
        textprops={'color': BRAND['white'], 'fontsize': 12}
    )
    for autotext in autotexts:
        autotext.set_color(BRAND['white'])
        autotext.set_fontsize(10)

    ax.set_title(title, fontsize=16, fontweight='bold',
                 color=BRAND['yellow'], pad=20)

    _save_fig(fig, output, dpi)
    print(f"Pie chart saved: {output} ({w}x{h})")


# ---------- line ----------

def gen_line(data, columns, title, output, size, brand,
             shade=False, threshold=1.0):
    """折线图/净值曲线

    data: [[label, val1, val2, ...], ...]
    columns[0] = x轴标签列名, columns[1:] = 各条线名
    shade: 在前两条线之间填充差值阴影
    threshold: Go阈值虚线y值
    """
    if brand:
        setup_brand_style()

    labels = [row[0] for row in data]
    w, h = size
    dpi = 120

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])
    ax.set_facecolor(BRAND['deep_blue'])

    x = np.arange(len(labels))
    line_names = columns[1:] if len(columns) > 1 else ['value']
    line_colors = []
    for i in range(len(line_names)):
        if i == 0:
            line_colors.append(BRAND['yellow'])
        elif i == 1:
            line_colors.append(BRAND['red'])
        else:
            line_colors.append(BRAND['positive'])

    # 绘制每条线
    lines = []
    for i, name in enumerate(line_names):
        col_idx = i + 1
        values = [row[col_idx] if col_idx < len(row) else 0 for row in data]
        ln, = ax.plot(x, values, color=line_colors[i], linewidth=2.2,
                      marker='o', markersize=5, label=name)
        lines.append((ln, values))

    # 差值阴影
    if shade and len(line_names) >= 2:
        vals_a = [row[1] for row in data]
        vals_b = [row[2] for row in data]
        diff = [a - b for a, b in zip(vals_a, vals_b)]
        ax.fill_between(x, 0, diff, alpha=0.18, color=BRAND['yellow'],
                        label='差值')

    # Go阈值线
    ax.axhline(y=threshold, color=BRAND['positive'], linestyle='--',
               linewidth=1.5, alpha=0.7, label=f'Go={threshold}')

    ax.axhline(y=0, color=BRAND['gray'], linestyle='-', linewidth=0.8,
               alpha=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, rotation=30, ha='right')
    ax.set_title(title, fontsize=16, fontweight='bold',
                 color=BRAND['yellow'], pad=20)
    ax.legend(loc='upper right', facecolor=BRAND['deep_blue'],
              edgecolor=BRAND['neutral'], labelcolor=BRAND['white'],
              fontsize=10)
    ax.grid(axis='y', alpha=0.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    _save_fig(fig, output, dpi)
    print(f"Line chart saved: {output} ({w}x{h})")


# ---------- drawdown ----------

def gen_drawdown(data, columns, title, output, size, brand):
    """回撤水位图

    data: [[label, drawdown_value], ...]  drawdown_value 通常为负数
    """
    if brand:
        setup_brand_style()

    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    w, h = size
    dpi = 120

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])
    ax.set_facecolor(BRAND['deep_blue'])

    x = np.arange(len(labels))
    ax.plot(x, values, color=BRAND['red'], linewidth=2.0)
    ax.fill_between(x, values, 0, color=BRAND['red'], alpha=0.3)

    # 危险线：回撤超15%
    ax.axhline(y=-0.15, color='#ff4444', linestyle='--',
               linewidth=1.5, alpha=0.7, label='危险线 -15%')

    # 标注最大回撤
    min_val = min(values)
    min_idx = values.index(min_val)
    ax.annotate(f'最大回撤\n{min_val:.2%}',
                xy=(min_idx, min_val),
                xytext=(min_idx + 0.5, min_val * 0.6),
                fontsize=10, fontweight='bold', color=BRAND['yellow'],
                arrowprops=dict(arrowstyle='->', color=BRAND['yellow'],
                                lw=1.5),
                bbox=dict(boxstyle='round,pad=0.3', facecolor=BRAND['navy'],
                          edgecolor=BRAND['yellow'], alpha=0.9))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, rotation=30, ha='right')
    ax.set_title(title, fontsize=16, fontweight='bold',
                 color=BRAND['yellow'], pad=20)
    ax.legend(loc='lower right', facecolor=BRAND['deep_blue'],
              edgecolor=BRAND['neutral'], labelcolor=BRAND['white'],
              fontsize=10)
    ax.grid(axis='y', alpha=0.15)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    _save_fig(fig, output, dpi)
    print(f"Drawdown chart saved: {output} ({w}x{h})")


# ---------- funnel ----------

def gen_funnel(data, columns, title, output, size, brand):
    """漏斗图

    data: [[label, value], ...]
    柱宽按数值递减，最大值=全宽；每层间加箭头；品牌色渐变
    """
    if brand:
        setup_brand_style()

    labels = [row[0] for row in data]
    values = [row[1] for row in data]
    w, h = size
    dpi = 120

    max_val = max(abs(v) for v in values) if values else 1
    max_val = max(max_val, 1)  # 避免除0

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])
    ax.set_facecolor(BRAND['deep_blue'])

    n = len(values)
    # 渐变色：黄色 -> 红色 -> 灰色
    gradient_colors = []
    for i in range(n):
        ratio = i / max(n - 1, 1)
        if ratio < 0.5:
            # 黄 -> 红
            t = ratio / 0.5
            r = int(0xe9 + (0xe7 - 0xe9) * t)
            g = int(0xc4 + (0x6f - 0xc4) * t)
            b = int(0x6a + (0x51 - 0x6a) * t)
        else:
            # 红 -> 灰
            t = (ratio - 0.5) / 0.5
            r = int(0xe7 + (0x8d - 0xe7) * t)
            g = int(0x6f + (0x99 - 0x6f) * t)
            b = int(0x51 + (0xae - 0x51) * t)
        gradient_colors.append(f'#{r:02x}{g:02x}{b:02x}')

    # 零值的特殊颜色
    for i, v in enumerate(values):
        if v == 0:
            gradient_colors[i] = BRAND['gray']

    bar_height = 0.55
    y_positions = np.arange(n)[::-1]  # 从上到下

    for i, (label, val) in enumerate(zip(labels, values)):
        width = abs(val) / max_val
        bar_y = y_positions[i]
        # 居中绘制
        ax.barh(bar_y, width, left=(1 - width) / 2, height=bar_height,
                color=gradient_colors[i], edgecolor='none')
        # 标签居中
        ax.text(0.5, bar_y, label, ha='center', va='center',
                fontsize=11, fontweight='bold', color=BRAND['white'])
        # 右侧数字
        ax.text(1.02, bar_y, str(val), ha='left', va='center',
                fontsize=11, fontweight='bold',
                color=gradient_colors[i])

    # 层间箭头
    for i in range(n - 1):
        y_top = y_positions[i] - bar_height / 2
        y_bottom = y_positions[i + 1] + bar_height / 2
        ax.annotate('', xy=(0.5, y_bottom), xytext=(0.5, y_top),
                    arrowprops=dict(arrowstyle='->', color=BRAND['white'],
                                    lw=1.5, alpha=0.6))

    ax.set_xlim(0, 1.15)
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=16, fontweight='bold',
                 color=BRAND['yellow'], pad=20)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)

    _save_fig(fig, output, dpi)
    print(f"Funnel chart saved: {output} ({w}x{h})")


# ---------- heatmap ----------

def gen_heatmap(data, columns, rows, title, output, size, brand):
    """热力图

    data: [[val, val, ...], ...]  纯数值矩阵
    columns: 列标签
    rows: 行标签
    """
    if brand:
        setup_brand_style()

    matrix = np.array(data, dtype=float)
    w, h = size
    dpi = 120

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])
    ax.set_facecolor(BRAND['deep_blue'])

    # 品牌色板colormap: 深蓝 -> 黄 -> 红
    cmap_colors = [BRAND['navy'], BRAND['yellow'], BRAND['red']]
    cmap = mcolors.LinearSegmentedColormap.from_list('brand', cmap_colors)

    im = ax.imshow(matrix, cmap=cmap, aspect='auto')

    # 格子标注数值
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            # 用归一化值判断文字颜色，深色背景白色、浅色背景深蓝
            norm_val = (val - matrix.min()) / (matrix.max() - matrix.min()) if matrix.max() != matrix.min() else 0.5
            text_color = BRAND['white'] if norm_val < 0.35 or norm_val > 0.65 else BRAND['deep_blue']
            ax.text(j, i, f'{val:.2f}', ha='center', va='center',
                    fontsize=11, fontweight='bold', color=text_color)

    # 列标签和行标签
    ax.set_xticks(np.arange(len(columns)))
    ax.set_yticks(np.arange(len(rows)))
    ax.set_xticklabels(columns, fontsize=10, rotation=30, ha='right')
    ax.set_yticklabels(rows, fontsize=10)

    ax.set_title(title, fontsize=16, fontweight='bold',
                 color=BRAND['yellow'], pad=20)

    # colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color=BRAND['white'])
    cbar.outline.set_edgecolor(BRAND['gray'])
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'),
             color=BRAND['white'], fontsize=9)

    _save_fig(fig, output, dpi)
    print(f"Heatmap saved: {output} ({w}x{h})")


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description='DataViz Generator')
    parser.add_argument('--type', required=True,
                        choices=['bar', 'pie', 'line', 'drawdown',
                                 'funnel', 'heatmap'])
    parser.add_argument('--data', required=True, help='JSON数据数组')
    parser.add_argument('--columns', required=True, help='列名，逗号分隔')
    parser.add_argument('--rows', default=None,
                        help='行标签(热力图用)，逗号分隔')
    parser.add_argument('--title', default='Chart', help='图表标题')
    parser.add_argument('--output', required=True, help='输出PNG路径')
    parser.add_argument('--size', default='1080x1440', help='宽x高')
    parser.add_argument('--brand-colors', action='store_true',
                        help='使用品牌色板')
    parser.add_argument('--shade', action='store_true',
                        help='(line) 显示前两条线的差值阴影')
    parser.add_argument('--threshold', type=float, default=1.0,
                        help='(line) Go阈值虚线y值，默认1.0')
    args = parser.parse_args()

    data = json.loads(args.data)
    # 数据校验
    if not isinstance(data, list) or len(data) == 0:
        parser.error('--data must be a non-empty JSON array')
    for row in data:
        if not isinstance(row, list) or len(row) < 2:
            parser.error(f'each data row must be a list with >= 2 elements, got: {row}')

    # 支持 "x" 和 "," 两种分隔符
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

    columns = args.columns.split(',')
    rows = args.rows.split(',') if args.rows else None

    if args.type == 'bar':
        gen_bar(data, columns, args.title, args.output, size,
                args.brand_colors)
    elif args.type == 'pie':
        gen_pie(data, columns, args.title, args.output, size,
                args.brand_colors)
    elif args.type == 'line':
        gen_line(data, columns, args.title, args.output, size,
                 args.brand_colors, shade=args.shade,
                 threshold=args.threshold)
    elif args.type == 'drawdown':
        gen_drawdown(data, columns, args.title, args.output, size,
                     args.brand_colors)
    elif args.type == 'funnel':
        gen_funnel(data, columns, args.title, args.output, size,
                   args.brand_colors)
    elif args.type == 'heatmap':
        if rows is None:
            print("Error: heatmap requires --rows", file=sys.stderr)
            sys.exit(1)
        gen_heatmap(data, columns, rows, args.title, args.output, size,
                    args.brand_colors)


if __name__ == '__main__':
    main()
