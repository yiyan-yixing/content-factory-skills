#!/usr/bin/env python3
"""
dataviz_animate.py -- matplotlib FuncAnimation 数据动画

将数据图表转为动画mp4（柱状图逐条生长、折线逐步绘制）。

用法:
  python3 dataviz_animate.py \
    --type bar-grow \
    --data '[["H001",-2.17],["H002",-2.45]]' \
    --columns '策略,OOS Sharpe' \
    --title '17个策略OOS Sharpe' \
    --duration 8 \
    --fps 24 \
    --output biz/content/assets/videos/T1-004/sharpe-animation.mp4 \
    --brand-colors
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
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

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'STHeiti', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False


def animate_bar_grow(data, columns, title, duration, fps, resolution, output):
    """柱状图逐条生长动画"""
    labels = [row[0] for row in data]
    values = np.array([row[1] for row in data])
    w, h = resolution
    dpi = 100
    n_frames = duration * fps

    # 按绝对值排序（大值先出现更有视觉冲击）
    sort_idx = np.argsort(np.abs(values))[::-1]
    labels_sorted = [labels[i] for i in sort_idx]
    values_sorted = values[sort_idx]

    colors = [BRAND['red'] if v < 0 else BRAND['yellow'] for v in values_sorted]
    n_bars = len(labels_sorted)

    fig, ax = plt.subplots(figsize=(w / dpi, h / dpi), dpi=dpi)
    fig.patch.set_facecolor(BRAND['deep_blue'])

    def update(frame):
        ax.clear()
        fig.patch.set_facecolor(BRAND['deep_blue'])
        ax.set_facecolor(BRAND['deep_blue'])

        # 计算当前进度
        progress = min(frame / n_frames, 1.0)
        # 每个柱子按时间依次出现
        bars_to_show = max(1, int(progress * n_bars))
        current_vals = np.zeros(n_bars)
        for i in range(bars_to_show):
            if i < bars_to_show - 1:
                current_vals[i] = values_sorted[i]
            else:
                # 最后一个正在生长的柱子
                bar_progress = (progress * n_bars - i)
                current_vals[i] = values_sorted[i] * min(bar_progress, 1.0)

        y_pos = np.arange(n_bars)
        bars = ax.barh(y_pos, current_vals, color=colors, height=0.55, edgecolor='none')

        # 数值标注
        for bar, val, target in zip(bars, current_vals, values_sorted):
            if abs(val) > 0.01:
                x_pos = bar.get_width()
                offset = 0.06 if val >= 0 else -0.06
                ha = 'left' if val >= 0 else 'right'
                ax.text(x_pos + offset, bar.get_y() + bar.get_height() / 2,
                        f'{val:.2f}', va='center', ha=ha,
                        color=BRAND['white'], fontsize=10, fontweight='bold')

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels_sorted, color=BRAND['white'], fontsize=12)
        ax.set_title(title, color=BRAND['yellow'], fontsize=18,
                     fontweight='bold', pad=20)
        ax.axvline(x=1.0, color=BRAND['positive'], linestyle='--',
                   alpha=0.5, linewidth=1.5)
        ax.axvline(x=0.0, color=BRAND['gray'], linestyle='-', alpha=0.3, linewidth=0.8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(BRAND['gray'])
        ax.spines['left'].set_color(BRAND['gray'])
        ax.tick_params(axis='x', colors=BRAND['white'])
        ax.grid(axis='x', alpha=0.1)

        # 设置固定的x轴范围
        x_min = min(values) - 0.5
        x_max = max(values) + 0.5
        ax.set_xlim(x_min, x_max)

    anim = animation.FuncAnimation(fig, update, frames=n_frames,
                                    interval=1000 // fps, blit=False)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 尝试ffmpeg writer，失败则用pillow转gif
    try:
        writer = animation.FFMpegWriter(fps=fps, bitrate=3000)
        anim.save(str(output_path), writer=writer, dpi=dpi)
        print(f"Animation saved: {output_path}")
    except Exception as e:
        print(f"FFMpeg writer failed ({e}), trying pillow writer...")
        gif_path = str(output_path).replace('.mp4', '.gif')
        anim.save(gif_path, writer='pillow', fps=fps, dpi=dpi)
        print(f"Animation saved as GIF: {gif_path}")
        print("Note: Install ffmpeg for mp4 output")

    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description='DataViz Animator')
    parser.add_argument('--type', required=True,
                        choices=['bar-grow', 'line-draw', 'number-roll'])
    parser.add_argument('--data', required=True, help='JSON数据数组')
    parser.add_argument('--columns', required=True, help='列名')
    parser.add_argument('--title', default='Animation', help='标题')
    parser.add_argument('--duration', type=int, default=8, help='动画秒数')
    parser.add_argument('--fps', type=int, default=24, help='帧率')
    parser.add_argument('--resolution', default='1080x1920', help='宽x高')
    parser.add_argument('--output', required=True, help='输出mp4路径')
    parser.add_argument('--brand-colors', action='store_true', help='品牌色板')
    args = parser.parse_args()

    data = json.loads(args.data)
    resolution = tuple(int(x) for x in args.resolution.split('x'))

    if args.type == 'bar-grow':
        animate_bar_grow(data, args.columns.split(','), args.title,
                         args.duration, args.fps, resolution, args.output)


if __name__ == '__main__':
    main()
