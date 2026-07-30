#!/usr/bin/env python3
"""
composer_common.py -- 视觉生产层公共模块

提供品牌色板、字体查找、渐变背景、base64编码、Markdown转换、
图片交错插入、HTML转义等共享功能。

被以下脚本引用：
  - cover_composer.py
  - page_composer.py
  - xhs_card_composer.py
  - landing_page_composer.py
"""

import base64
import html
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# 品牌色板 — RGB元组（Pillow用）+ Hex字符串（HTML/CSS用）
# ============================================================

BRAND_RGB = {
    'deep_blue': (26, 26, 46),
    'navy': (22, 33, 62),
    'navy_mid': (30, 42, 80),
    'yellow': (233, 196, 106),
    'yellow_light': (255, 220, 140),
    'white': (255, 255, 255),
    'off_white': (245, 240, 230),
    'red': (231, 111, 81),
    'red_light': (255, 140, 110),
    'positive': (42, 157, 143),
    'positive_light': (80, 200, 180),
    'dark_overlay': (0, 0, 0, 140),
}

BRAND_HEX = {
    'deep_blue': '#1a1a2e',
    'navy': '#16213e',
    'yellow': '#e9c46a',
    'white': '#ffffff',
    'red': '#e76f51',
    'positive': '#2a9d8f',
}

# ============================================================
# 字体查找
# ============================================================

FONT_CANDIDATES = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/Library/Fonts/Arial Unicode.ttf',
]

_font_cache = {}  # 简单缓存，避免重复磁盘查找


def find_font(size: int) -> ImageFont.FreeTypeFont:
    """查找系统中可用的中文字体，带缓存"""
    if size in _font_cache:
        return _font_cache[size]
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                font = ImageFont.truetype(path, size)
                _font_cache[size] = font
                return font
            except Exception:
                continue
    font = ImageFont.load_default()
    _font_cache[size] = font
    return font


# ============================================================
# 系统字体栈（HTML/CSS用）
# ============================================================

FONT_STACK = "PingFang SC, Heiti SC, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

# ============================================================
# 渐变背景生成
# ============================================================


def create_gradient_bg(width: int, height: int, top_color=None, bottom_color=None) -> Image.Image:
    """创建渐变背景，支持自定义顶底颜色"""
    tc = top_color or BRAND_RGB['deep_blue']
    bc = bottom_color or BRAND_RGB['navy']
    try:
        import numpy as np
        r = np.linspace(tc[0], bc[0], height, dtype=np.uint8)
        g = np.linspace(tc[1], bc[1], height, dtype=np.uint8)
        b = np.linspace(tc[2], bc[2], height, dtype=np.uint8)
        arr = np.stack([np.tile(r, (width, 1)).T,
                        np.tile(g, (width, 1)).T,
                        np.tile(b, (width, 1)).T], axis=2)
        return Image.fromarray(arr, 'RGB')
    except ImportError:
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        for y in range(height):
            ratio = y / height
            r = int(tc[0] * (1 - ratio) + bc[0] * ratio)
            g = int(tc[1] * (1 - ratio) + bc[1] * ratio)
            b = int(tc[2] * (1 - ratio) + bc[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        return img


# ============================================================
# XHS 专用：线索色渐变背景 + 几何装饰
# ============================================================

# 线索 → 渐变色对
THREAD_GRADIENT_MAP = {
    'red':    ((50, 20, 25), (22, 33, 62)),      # 暗红→深蓝
    'blue':   ((15, 35, 55), (22, 33, 62)),      # 深青蓝→深蓝
    'yellow': ((45, 38, 20), (22, 33, 62)),      # 暗金→深蓝
}

# 线索 → 装饰色（色块/圆/线条的亮色）
THREAD_ACCENT_MAP = {
    'red':    BRAND_RGB['red'],
    'blue':   BRAND_RGB['positive'],
    'yellow': BRAND_RGB['yellow'],
}


def create_xhs_gradient_bg(width: int, height: int,
                            thread_color: str = '') -> Image.Image:
    """为XHS卡片创建线索色渐变背景 + 角落几何装饰。

    与纯深蓝渐变不同，线索色背景顶部带有暖色调（红/青/金），
    底部回归深蓝。加角落色块和半透明圆形作为视觉锚点。
    """
    colors = THREAD_GRADIENT_MAP.get(thread_color, ((26, 26, 46), (22, 33, 62)))
    img = create_gradient_bg(width, height, top_color=colors[0], bottom_color=colors[1])
    draw = ImageDraw.Draw(img)

    accent = THREAD_ACCENT_MAP.get(thread_color, BRAND_RGB['yellow'])

    # 左上角：线索色三角色块（对角切角装饰）
    tri_size = int(width * 0.35)
    draw.polygon([(0, 0), (tri_size, 0), (0, tri_size)],
                  fill=(*accent, ))  # Pillow RGB 不支持 alpha，用混合色
    # 用稍暗版本避免过亮
    dark_accent = tuple(max(0, c - 80) for c in accent)
    draw.polygon([(0, 0), (tri_size, 0), (0, tri_size)],
                  fill=dark_accent)
    # 再叠一层更亮更小的三角
    bright_accent = tuple(min(255, c + 30) for c in accent)
    tri_small = int(tri_size * 0.6)
    draw.polygon([(0, 0), (tri_small, 0), (0, tri_small)],
                  fill=bright_accent)

    # 右下角：半透明感圆形（用暗色圆模拟）
    circle_r = int(width * 0.25)
    cx = width - int(circle_r * 0.3)
    cy = height - int(circle_r * 0.3)
    very_dark = tuple(max(0, c - 30) for c in colors[1])
    draw.ellipse([(cx - circle_r, cy - circle_r),
                   (cx + circle_r, cy + circle_r)],
                  fill=very_dark)

    # 顶部细线：线索色横线（视觉分割）
    draw.line([(0, 4), (width, 4)], fill=accent, width=4)

    return img


# ============================================================
# 图片base64编码
# ============================================================

MAX_BASE64_SIZE = 500 * 1024  # 超过此大小使用相对路径而非base64内联


def image_to_base64_src(path: str) -> str:
    """将图片文件转为base64 data URI，或超过阈值返回文件名"""
    p = Path(path)
    if not p.exists():
        return ''
    size = p.stat().st_size
    if size > MAX_BASE64_SIZE:
        return p.name
    with open(p, 'rb') as f:
        data = base64.b64encode(f.read()).decode('utf-8')
    ext = p.suffix.lower().lstrip('.')
    mime_map = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                'gif': 'image/gif', 'webp': 'image/webp'}
    mime = mime_map.get(ext, 'image/png')
    return f'data:{mime};base64,{data}'


# ============================================================
# Markdown转HTML
# ============================================================

try:
    import markdown as _md_lib
    HAS_MARKDOWN = True
except ImportError:
    _md_lib = None
    HAS_MARKDOWN = False


def markdown_to_html(text: str) -> str:
    """将Markdown文本转为HTML。有markdown库用完整转换，否则正则兜底。"""
    if HAS_MARKDOWN:
        return _md_lib.markdown(text, extensions=['fenced_code', 'tables', 'codehilite'])
    # 基础正则兜底转换
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code>\2</code></pre>', text, flags=re.DOTALL)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
    lines = text.split('\n')
    result = []
    in_tag = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
            continue
        if stripped.startswith('<h') or stripped.startswith('<pre') or stripped.startswith('<blockquote'):
            result.append(stripped)
            in_tag = True
        elif in_tag and (stripped.startswith('</') or stripped == ''):
            result.append(stripped)
            in_tag = False
        elif not in_tag and stripped and not stripped.startswith('<'):
            result.append(f'<p>{stripped}</p>')
        else:
            result.append(stripped)
    return '\n'.join(result)


# ============================================================
# 图片交错插入正文
# ============================================================


def interleave_figures(body_html: str, figures: list, figure_class: str = 'figure-wrap') -> str:
    """在正文HTML中的自然分段点（h2标题后）插入配图。

    策略：按<h2>标签分段，在每个有内容的段落后插入一张配图。
    配图多于段落时，剩余配图追加到末尾。配图不足时均匀分布。
    """
    if not figures:
        return body_html

    sections = re.split(r'(<h2>.*?</h2>)', body_html, flags=re.DOTALL)

    fig_idx = 0
    result_parts = []
    for section in sections:
        result_parts.append(section)
        if fig_idx < len(figures) and section.strip() and not section.startswith('<h2>'):
            fig_path = figures[fig_idx]
            src = image_to_base64_src(fig_path)
            if src:
                fig_name = Path(fig_path).stem.replace('-', ' ').replace('_', ' ')
                result_parts.append(
                    f'\n<div class="{figure_class}">\n'
                    f'  <img src="{src}" alt="{html.escape(fig_name)}">\n'
                    f'  <div class="fig-caption">{html.escape(fig_name)}</div>\n'
                    f'</div>\n'
                )
                fig_idx += 1

    while fig_idx < len(figures):
        fig_path = figures[fig_idx]
        src = image_to_base64_src(fig_path)
        if src:
            fig_name = Path(fig_path).stem.replace('-', ' ').replace('_', ' ')
            result_parts.append(
                f'\n<div class="{figure_class}">\n'
                f'  <img src="{src}" alt="{html.escape(fig_name)}">\n'
                f'  <div class="fig-caption">{html.escape(fig_name)}</div>\n'
                f'</div>\n'
            )
        fig_idx += 1

    return ''.join(result_parts)


# ============================================================
# HTML安全转义
# ============================================================


def html_escape(text: str) -> str:
    """HTML实体转义，防止XSS注入。转义 <, >, &, ", ' """
    return html.escape(text, quote=True)


def html_escape_attr(text: str) -> str:
    """HTML属性值转义（用于meta标签等属性上下文）"""
    return html.escape(text, quote=True)
