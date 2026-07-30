#!/usr/bin/env python3
"""
cover_composer.py -- 小红书/公众号封面图合成

将数据图/AI图 + 品牌文字 + 模板布局 合成为最终封面图PNG。

用法:
  python3 cover_composer.py \
    --template number-impact \
    --title "17" \
    --highlight "0个Go" \
    --highlight-color "#e76f51" \
    --subtitle "量化策略Go/No-Go完整记录" \
    --background /path/to/chart.png \
    --platform xiaohongshu \
    --output /path/to/cover.png
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 公共模块 — 确保从任意目录运行时可找到本模块
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_common import (
    BRAND_RGB, find_font, create_gradient_bg,
)

# 品牌色板（RGB，Pillow用）
BRAND = BRAND_RGB

# 尺寸规范
SIZES = {
    'xiaohongshu': (1080, 1440),
    'wechat': (1200, 675),
    'zhihu': (1920, 1080),
}

# 线索颜色映射
THREAD_COLOR_MAP = {
    'red': BRAND_RGB['red'],
    'blue': BRAND_RGB.get('positive', (42, 157, 143)),
    'yellow': BRAND_RGB['yellow'],
}


def draw_series_overlay(draw: ImageDraw.Draw, w: int, h: int,
                         series: str, episode: str,
                         thread_color: str, total_episodes: int,
                         current_episode: int) -> None:
    """在封面图上绘制系列标识覆盖层。

    元素:
      - 左上角: 系列名（白色14pt）+ 半透明背景条
      - 右上角: 集数（白色12pt）
      - 左下线索色标: 圆点
      - 底部: 进度条
    """
    if not series:
        return

    # --- 左上角: 系列名 ---
    series_font = find_font(14)
    bar_h = 28
    draw.rectangle([(0, 0), (w, bar_h)], fill=BRAND['navy'])
    draw.text((30, 5), series, fill=BRAND['white'], font=series_font)

    # --- 右上角: 集数 ---
    if episode:
        ep_font = find_font(12)
        ep_bbox = draw.textbbox((0, 0), episode, font=ep_font)
        ep_w = ep_bbox[2] - ep_bbox[0]
        draw.text((w - ep_w - 30, 7), episode,
                  fill=BRAND['white'], font=ep_font)

    # --- 线索色标 ---
    if thread_color and thread_color in THREAD_COLOR_MAP:
        dot_color = THREAD_COLOR_MAP[thread_color]
        dot_r = 10
        dot_x = 30
        dot_y = h - 100
        draw.ellipse([(dot_x, dot_y), (dot_x + dot_r * 2, dot_y + dot_r * 2)],
                     fill=dot_color)

    # --- 进度条 ---
    if total_episodes > 0 and current_episode > 0:
        bar_y = h - 50
        bar_h = 8
        n_slots = min(total_episodes, 10)
        slot_w = 40
        gap = 6
        total_bar_w = n_slots * slot_w + (n_slots - 1) * gap
        bar_x = (w - total_bar_w) // 2

        for i in range(n_slots):
            sx = bar_x + i * (slot_w + gap)
            color = BRAND['yellow'] if i < current_episode else BRAND['navy']
            draw.rectangle([(sx, bar_y), (sx + slot_w, bar_y + bar_h)],
                          fill=color, outline=BRAND['navy'])


def hex_to_rgb(hex_color: str) -> tuple:
    """#rrggbb -> (r, g, b)"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def compose_number_impact(img: Image.Image, title: str, highlight: str,
                           highlight_color: tuple, subtitle: str,
                           background: str = None,
                           series: str = '', episode: str = '',
                           thread_color: str = '',
                           total_episodes: int = 0,
                           current_episode: int = 0) -> Image.Image:
    """数字冲击型：大数字居中 + 副标题下方 + 底图嵌入"""
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # 线索色装饰
    accent = THREAD_COLOR_MAP.get(thread_color, BRAND['yellow'])
    dark_accent = tuple(max(0, c - 80) for c in accent)
    bright_accent = tuple(min(255, c + 30) for c in accent)

    # 左上角装饰色块
    tri_size = int(w * 0.3)
    draw.polygon([(0, 0), (tri_size, 0), (0, tri_size)], fill=dark_accent)
    tri_small = int(tri_size * 0.6)
    draw.polygon([(0, 0), (tri_small, 0), (0, tri_small)], fill=bright_accent)

    # 系列标识覆盖层
    draw_series_overlay(draw, w, h, series, episode, thread_color,
                        total_episodes, current_episode)

    # 底图嵌入（如有）
    if background and Path(background).exists():
        try:
            bg_img = Image.open(background)
            # 适配封面宽度，留边距
            max_w = w - 60
            max_h = int(h * 0.40)
            bg_img.thumbnail((max_w, max_h), Image.LANCZOS)
            # 半透明遮罩（RGBA混合）
            overlay = Image.new('RGBA', (w, h), (0, 0, 0, 128))
            # 在底图区域放置数据图
            fx = (w - bg_img.width) // 2
            fy = h - bg_img.height - 60
            img.paste(bg_img, (fx, fy))
        except Exception as e:
            print(f"Warning: background image failed: {e}")

    # 重新创建draw（paste后需要）
    draw = ImageDraw.Draw(img)

    # 大数字/主标题 居中偏上
    title_font = find_font(96 if h > 1000 else 64)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = int(h * 0.18)
    draw.text((x, y), title, fill=BRAND['yellow'], font=title_font)

    # 高亮文字
    if highlight:
        hl_font = find_font(52 if h > 1000 else 36)
        hbbox = draw.textbbox((0, 0), highlight, font=hl_font)
        hw = hbbox[2] - hbbox[0]
        hx = (w - hw) // 2
        hy = y + th + 20
        draw.text((hx, hy), highlight, fill=highlight_color, font=hl_font)

    # 副标题 底部
    if subtitle:
        sub_font = find_font(24 if h > 1000 else 18)
        sbbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = sbbox[2] - sbbox[0]
        sx = (w - sw) // 2
        sy = int(h * 0.78)
        draw.text((sx, sy), subtitle, fill=BRAND['white'], font=sub_font)

    return img


def compose_vs_compare(img: Image.Image, title_left: str, title_right: str,
                        subtitle: str,
                        series: str = '', episode: str = '',
                        thread_color: str = '',
                        total_episodes: int = 0,
                        current_episode: int = 0) -> Image.Image:
    """VS对比型：左右分栏 + 中间VS"""
    draw = ImageDraw.Draw(img)
    w, h = img.size
    mid = w // 2

    # 系列标识覆盖层
    draw_series_overlay(draw, w, h, series, episode, thread_color,
                        total_episodes, current_episode)

    # VS大字居中
    vs_font = find_font(64)
    vs_bbox = draw.textbbox((0, 0), "VS", font=vs_font)
    vs_w = vs_bbox[2] - vs_bbox[0]
    draw.text((mid - vs_w // 2, int(h * 0.12)), "VS",
              fill=BRAND['yellow'], font=vs_font)

    # 左侧标题
    side_font = find_font(40)
    draw.text((50, int(h * 0.32)), title_left,
              fill=BRAND['white'], font=side_font)

    # 右侧标题
    draw.text((mid + 50, int(h * 0.32)), title_right,
              fill=BRAND['white'], font=side_font)

    # 底部结论
    if subtitle:
        sub_font = find_font(28)
        sbbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = sbbox[2] - sbbox[0]
        draw.text(((w - sw) // 2, h - 90), subtitle,
                  fill=BRAND['red'], font=sub_font)

    return img


def compose_list(img: Image.Image, items: list, summary: str,
                  series: str = '', episode: str = '',
                  thread_color: str = '',
                  total_episodes: int = 0,
                  current_episode: int = 0) -> Image.Image:
    """清单型：竖排编号 + 一句话 + 底部总结"""
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # 系列标识覆盖层
    draw_series_overlay(draw, w, h, series, episode, thread_color,
                        total_episodes, current_episode)

    num_font = find_font(52)
    text_font = find_font(26)

    start_y = int(h * 0.10)
    spacing = min(110, (h * 0.60) // max(len(items), 1))

    for i, item in enumerate(items):
        y = start_y + i * spacing
        # 编号
        draw.text((50, y), str(i + 1), fill=BRAND['yellow'], font=num_font)
        # 内容
        draw.text((130, y + 10), item, fill=BRAND['white'], font=text_font)

    # 底部总结
    if summary:
        sub_font = find_font(30)
        sbbox = draw.textbbox((0, 0), summary, font=sub_font)
        sw = sbbox[2] - sbbox[0]
        draw.text(((w - sw) // 2, h - 90), summary,
                  fill=BRAND['red'], font=sub_font)

    return img


def compose_screenshot_enhanced(img: Image.Image, title: str, subtitle: str,
                                 screenshot: str = None,
                                 series: str = '', episode: str = '',
                                 thread_color: str = '',
                                 total_episodes: int = 0,
                                 current_episode: int = 0) -> Image.Image:
    """截图增强型：大截图占2/3 + 顶部标题 + 底部结论"""
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # 系列标识覆盖层
    draw_series_overlay(draw, w, h, series, episode, thread_color,
                        total_episodes, current_episode)

    # 顶部标题
    title_font = find_font(44)
    tbbox = draw.textbbox((0, 0), title, font=title_font)
    tw = tbbox[2] - tbbox[0]
    draw.text(((w - tw) // 2, 40), title, fill=BRAND['yellow'], font=title_font)

    # 截图占2/3
    if screenshot and Path(screenshot).exists():
        try:
            ss_img = Image.open(screenshot)
            max_w = w - 60
            max_h = int(h * 0.60)
            ss_img.thumbnail((max_w, max_h), Image.LANCZOS)
            sx = (w - ss_img.width) // 2
            sy = 100
            img.paste(ss_img, (sx, sy))
        except Exception as e:
            print(f"Warning: screenshot image failed: {e}")

    draw = ImageDraw.Draw(img)

    # 底部结论
    if subtitle:
        sub_font = find_font(28)
        sbbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = sbbox[2] - sbbox[0]
        draw.text(((w - sw) // 2, h - 80), subtitle,
                  fill=BRAND['red'], font=sub_font)

    return img


def main():
    parser = argparse.ArgumentParser(description='Cover Composer')
    parser.add_argument('--template', required=True,
                        choices=['number-impact', 'vs-compare', 'list', 'screenshot-enhanced'])
    parser.add_argument('--background', default=None, help='背景/数据图路径')
    parser.add_argument('--title', required=True, help='主标题')
    parser.add_argument('--highlight', default='', help='高亮文字')
    parser.add_argument('--highlight-color', default='#e76f51', help='高亮颜色')
    parser.add_argument('--subtitle', default='', help='副标题')
    parser.add_argument('--title-left', default='', help='VS左侧标题')
    parser.add_argument('--title-right', default='', help='VS右侧标题')
    parser.add_argument('--items', nargs='*', default=[], help='清单项')
    parser.add_argument('--summary', default='', help='清单总结')
    parser.add_argument('--screenshot', default=None, help='截图路径')
    parser.add_argument('--platform', default='xiaohongshu',
                        choices=['xiaohongshu', 'wechat', 'zhihu'])
    # 系列标识参数
    parser.add_argument('--series', default='', help='Series name, e.g. "一人AI实战记"')
    parser.add_argument('--episode', default='', help='Episode label, e.g. "D1/10"')
    parser.add_argument('--thread-color', default='', choices=['red', 'blue', 'yellow', ''],
                        help='Thread color indicator: red(quant), blue(AI infra), yellow(tools)')
    parser.add_argument('--total-episodes', type=int, default=0, help='Total episodes in series (for progress bar)')
    parser.add_argument('--current-episode', type=int, default=0, help='Current episode number (for progress bar)')
    parser.add_argument('--output', required=True, help='输出PNG路径')
    args = parser.parse_args()

    width, height = SIZES.get(args.platform, SIZES['xiaohongshu'])

    # 创建底图 — XHS 平台用线索色渐变，其他平台用默认
    if args.platform == 'xiaohongshu' and not (args.background and Path(args.background).exists()):
        from composer_common import create_xhs_gradient_bg
        bg = create_xhs_gradient_bg(width, height, thread_color=args.thread_color)
    elif args.background and Path(args.background).exists():
        try:
            bg = Image.open(args.background).resize((width, height), Image.LANCZOS)
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 140))
            bg = bg.convert('RGBA')
            bg = Image.alpha_composite(bg, overlay).convert('RGB')
        except Exception:
            bg = create_gradient_bg(width, height)
    else:
        bg = create_gradient_bg(width, height)

    # 高亮颜色
    hl_color = hex_to_rgb(args.highlight_color) if args.highlight_color.startswith('#') \
               else BRAND['red']

    # 按模板合成（传入系列参数）
    series_kw = dict(
        series=args.series,
        episode=args.episode,
        thread_color=args.thread_color,
        total_episodes=args.total_episodes,
        current_episode=args.current_episode,
    )
    if args.template == 'number-impact':
        result = compose_number_impact(bg, args.title, args.highlight,
                                        hl_color, args.subtitle, args.background,
                                        **series_kw)
    elif args.template == 'vs-compare':
        result = compose_vs_compare(bg, args.title_left, args.title_right, args.subtitle,
                                    **series_kw)
    elif args.template == 'list':
        result = compose_list(bg, args.items if args.items else [args.title], args.summary,
                              **series_kw)
    elif args.template == 'screenshot-enhanced':
        result = compose_screenshot_enhanced(bg, args.title, args.subtitle, args.screenshot,
                                             **series_kw)

    # 保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(str(output_path), 'PNG', optimize=True)
    print(f"Cover saved: {output_path} ({width}x{height})")


if __name__ == '__main__':
    main()
