#!/usr/bin/env python3
"""视频封面生成器 — 用 Pillow 生成多尺寸品牌封面图。

用法:
  # 小红书竖版封面 (1080x1440)
  python3 cover_gen.py reels -o cover.png --title "主标题" --subtitle "副标题" --tag "标签"

  # 抖音竖版封面 (1080x1920)
  python3 cover_gen.py vlog -o cover.png --title "主标题" --subtitle "副标题" \\
    --badges "🏔️ 海拔1860m" "🌲 迎客松" --stats "4,天数" "10+,打卡点"
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import argparse
import sys

# ── 品牌色板 ──
BG_DARK = (26, 26, 46)
GOLD = (233, 196, 106)
RED = (231, 111, 81)
WHITE = (255, 255, 255)
DARK_BLUE = (20, 20, 40)
CLOUD = (35, 35, 60)

FONT_CANDIDATES = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Helvetica.ttc',
]


def find_font():
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def draw_gradient(draw, w, h, top_color, bottom_color):
    """绘制垂直渐变背景"""
    for y in range(h):
        ratio = y / h
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def draw_mountains(draw, w, h, peaks, color=(30, 30, 55)):
    """绘制山峰剪影。peaks: [(x, peak_y), ...]"""
    for i in range(len(peaks) - 1):
        x1, y1 = peaks[i]
        x2, y2 = peaks[i + 1]
        mid_x = (x1 + x2) // 2
        draw.polygon([(x1, h), (mid_x, y1), (x2, h)], fill=color)


def draw_clouds(draw, clouds):
    """绘制云朵。clouds: [(cx, cy, rx, ry), ...]"""
    for cx, cy, rx, ry in clouds:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=CLOUD)


def draw_rounded_tag(draw, text, x, y, font, bg_color, text_color=WHITE, radius=8):
    """绘制圆角标签"""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = 12
    draw.rounded_rectangle(
        [x - pad, y - 4, x + tw + pad, y + th + 4],
        radius=radius, fill=bg_color
    )
    draw.text((x, y), text, fill=text_color, font=font)
    return tw + pad * 2, th + 8


def draw_badge(draw, text, cx, y, font, bg_color=(40, 40, 70), text_color=GOLD):
    """居中绘制徽章"""
    bbox = draw.textbbox((0, 0), text, font=font)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    pad = 16
    bx = cx - bw // 2
    draw.rounded_rectangle(
        [bx - pad, y - 4, bx + bw + pad, y + bh + 4],
        radius=10, fill=bg_color
    )
    draw.text((bx, y), text, fill=text_color, font=font)


def create_cover_reels(output_path: str,
                       title: str,
                       subtitle: str,
                       tag: str = "",
                       badges: list = None,
                       cta: str = "关注我 · 解锁完整攻略"):
    """小红书竖版封面 1080x1440"""
    w, h = 1080, 1440
    img = Image.new('RGB', (w, h), BG_DARK)
    draw = ImageDraw.Draw(img)
    font_path = find_font()

    title_font = ImageFont.truetype(font_path, 80) if font_path else ImageFont.load_default()
    subtitle_font = ImageFont.truetype(font_path, 48) if font_path else ImageFont.load_default()
    tag_font = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()

    draw_gradient(draw, w, h, (26, 26, 46), (20, 20, 60))
    draw.rectangle([(0, 0), (w, 6)], fill=GOLD)        # 顶部装饰线

    # 山峰剪影
    draw_mountains(draw, w, h, [(-100, 200), (200, 200), (540, 150), (800, 250), (1040, 180), (1300, h)])
    draw_clouds(draw, [(250, 500, 200, 40), (700, 450, 250, 50), (400, 400, 150, 30), (900, 520, 180, 35)])

    # 标题
    bbox = draw.textbbox((0, 0), title, font=title_font)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, 180), title, fill=GOLD, font=title_font)

    # 标题下装饰线
    line_y = 280
    draw.line([(w // 2 - 120, line_y), (w // 2 + 120, line_y)], fill=GOLD, width=3)

    # 副标题
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, line_y + 20), subtitle, fill=WHITE, font=subtitle_font)

    # 徽章
    if badges:
        badge_y = 500
        badge_spacing = 72
        for i, badge in enumerate(badges):
            draw_badge(draw, badge, w // 2, badge_y + i * badge_spacing, tag_font)

    # 底部 CTA
    bbox = draw.textbbox((0, 0), cta, font=small_font)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, h - 100), cta, fill=WHITE, font=small_font)
    draw.rectangle([(0, h - 6), (w, h)], fill=GOLD)     # 底部装饰线

    # 右上角标签
    if tag:
        draw_rounded_tag(draw, tag, w - 30, 40, small_font, RED)

    img.save(output_path, 'PNG')
    print(f"✅ 封面已保存: {output_path} ({w}x{h})")


def create_cover_vlog(output_path: str,
                      title_line1: str,
                      title_line2: str,
                      subtitle: str,
                      tag: str = "",
                      story: list = None,
                      stats: list = None,
                      cta: str = "关注我 · 带你看更大的世界"):
    """抖音/视频号竖版封面 1080x1920"""
    w, h = 1080, 1920
    img = Image.new('RGB', (w, h), BG_DARK)
    draw = ImageDraw.Draw(img)
    font_path = find_font()

    title_font = ImageFont.truetype(font_path, 90) if font_path else ImageFont.load_default()
    subtitle_font = ImageFont.truetype(font_path, 50) if font_path else ImageFont.load_default()
    body_font = ImageFont.truetype(font_path, 36) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 28) if font_path else ImageFont.load_default()

    draw_gradient(draw, w, h, (26, 26, 46), (18, 15, 50))
    draw.rectangle([(0, 0), (w, 8)], fill=GOLD)

    # 太阳 + 山峰
    draw.ellipse([w // 2 - 60, 180 - 60, w // 2 + 60, 180 + 60], fill=GOLD)
    peaks = [(0, 350), (300, 180), (400, 350), (700, 280), (950, 150), (1200, h)]
    draw_mountains(draw, w, h, peaks)

    # 标题
    bbox = draw.textbbox((0, 0), title_line1, font=title_font)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, 280), title_line1, fill=WHITE, font=title_font)
    bbox = draw.textbbox((0, 0), title_line2, font=title_font)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, 380), title_line2, fill=GOLD, font=title_font)

    line_y = 470
    draw.line([(w // 2 - 100, line_y), (w // 2 + 100, line_y)], fill=GOLD, width=3)

    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, line_y + 20), subtitle, fill=WHITE, font=subtitle_font)

    # 故事线
    if story:
        story_y = 600
        for i, line in enumerate(story):
            bbox = draw.textbbox((0, 0), line, font=body_font)
            draw.text(((w - (bbox[2] - bbox[0])) // 2, story_y + i * 60), line, fill=GOLD, font=body_font)

    # 关键数据
    if stats:
        stat_y = max(900, (story_y + len(story) * 60 + 100) if story else 900)
        stat_spacing = w // (len(stats) + 1)
        for i, (num, label) in enumerate(stats):
            sx = stat_spacing * (i + 1)
            bbox = draw.textbbox((0, 0), num, font=title_font)
            draw.text((sx - (bbox[2] - bbox[0]) // 2, stat_y), num, fill=GOLD, font=title_font)
            bbox = draw.textbbox((0, 0), label, font=small_font)
            draw.text((sx - (bbox[2] - bbox[0]) // 2, stat_y + 100), label, fill=WHITE, font=small_font)

    # 底部 CTA
    draw.rectangle([(0, h - 120), (w, h)], fill=DARK_BLUE)
    bbox = draw.textbbox((0, 0), cta, font=body_font)
    draw.text(((w - (bbox[2] - bbox[0])) // 2, h - 85), cta, fill=GOLD, font=body_font)

    if tag:
        draw_rounded_tag(draw, tag, w - 30, 30, small_font, RED)

    draw.rectangle([(0, h - 8), (w, h)], fill=GOLD)

    img.save(output_path, 'PNG')
    print(f"✅ 封面已保存: {output_path} ({w}x{h})")


def main():
    parser = argparse.ArgumentParser(description="视频封面生成器")
    subparsers = parser.add_subparsers(dest="mode", required=True, help="封面类型")

    # reels 子命令
    rp = subparsers.add_parser("reels", help="小红书竖版封面 1080x1440")
    rp.add_argument("-o", "--output", required=True, help="输出路径")
    rp.add_argument("--title", required=True, help="主标题")
    rp.add_argument("--subtitle", default="", help="副标题")
    rp.add_argument("--tag", default="", help="右上角标签")
    rp.add_argument("--badges", nargs="*", default=[], help="徽章列表")
    rp.add_argument("--cta", default="关注我 · 解锁完整攻略", help="底部CTA")

    # vlog 子命令
    vp = subparsers.add_parser("vlog", help="抖音竖版封面 1080x1920")
    vp.add_argument("-o", "--output", required=True, help="输出路径")
    vp.add_argument("--title-line1", required=True, help="标题第一行")
    vp.add_argument("--title-line2", required=True, help="标题第二行")
    vp.add_argument("--subtitle", default="", help="副标题")
    vp.add_argument("--tag", default="", help="右上角标签")
    vp.add_argument("--story", nargs="*", default=[], help="故事线列表")
    vp.add_argument("--stats", nargs="*", default=[], help="数据统计 (格式: 数字,标签)")
    vp.add_argument("--cta", default="关注我 · 带你看更大的世界", help="底部CTA")

    args = parser.parse_args()

    if args.mode == "reels":
        create_cover_reels(args.output, args.title, args.subtitle,
                           tag=args.tag, badges=args.badges, cta=args.cta)
    elif args.mode == "vlog":
        stats = [s.split(",") for s in args.stats] if args.stats else None
        create_cover_vlog(args.output, args.title_line1, args.title_line2, args.subtitle,
                          tag=args.tag, story=args.story, stats=stats, cta=args.cta)


if __name__ == "__main__":
    main()
