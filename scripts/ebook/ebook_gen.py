#!/usr/bin/env python3
"""
ebook_gen.py — Markdown 目录 → EPUB 电子书生成器

功能:
  - 从 Markdown 文件目录生成标准 EPUB 文件
  - 自动提取 H1/H2 层级生成 TOC (table of contents)
  - Pillow 生成品牌封面图 (使用品牌色板)
  - 完整元数据 (书名、作者、语言、更新日期)
  - 前/后记 + 版权页
  - 输出可在 Apple Books / Calibre 打开的 .epub

用法:
  # 从单个 markdown 文件生成
  python3 ebook_gen.py single input.md -o output.epub --title "我的书"

  # 从目录下的所有 markdown 文件生成 (按文件名排序)
  python3 ebook_gen.py dir /path/to/chapters/ -o output.epub --title "合集" \
    --author "一言一行" --series "系列名" --series-index 1

  # 高级: 指定各章节 Markdown 文件 (控制顺序)
  python3 ebook_gen.py custom -o book.epub \
    --title "AI 量化交易实战" --author "一言一行" \
    --chapters prep.md ch1.md ch2.md ch3.md appendix.md

  # 公共参数
  --lang zh-CN               # 语言, 默认 zh-CN
  --cover-image cover.png    # 使用已有的封面图 (跳过自动生成)
  --no-cover                 # 不生成封面页
  --no-toc                   # 不生成目录页
  --copyright "© 2026 ..."  # 版权声明, 默认使用作者名
  --series "系列名称"        # 系列名 (元数据)
  --series-index 1           # 系列卷号 (元数据)

依赖:
  pip install ebooklib Pillow
"""

import argparse
import html
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ============================================================
# 系统路径 — 引用 composer_common 中的品牌色板
# ============================================================
_SCRIPT_DIR = Path(__file__).parent.resolve()
_SCRIPTS_DIR = _SCRIPT_DIR
_BIZ_CONTENT_DIR = _SCRIPT_DIR.parent.resolve()

# 尝试导入品牌色板
try:
    sys.path.insert(0, str(_SCRIPTS_DIR))
    from composer_common import BRAND_RGB, BRAND_HEX, find_font
    HAS_BRAND = True
except ImportError:
    HAS_BRAND = False
    # 降级到脚本自身定义
    BRAND_RGB = {
        'deep_blue': (26, 26, 46),
        'navy': (22, 33, 62),
        'navy_mid': (30, 42, 80),
        'yellow': (233, 196, 106),
        'yellow_light': (255, 220, 140),
        'white': (255, 255, 255),
        'off_white': (245, 240, 230),
        'red': (231, 111, 81),
        'positive': (42, 157, 143),
    }
    BRAND_HEX = {
        'deep_blue': '#1a1a2e',
        'navy': '#16213e',
        'yellow': '#e9c46a',
        'white': '#ffffff',
        'red': '#e76f51',
        'positive': '#2a9d8f',
    }

    def find_font(size: int) -> ImageFont.FreeTypeFont:
        FONT_CANDIDATES = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/Hiragino Sans GB.ttc',
            '/Library/Fonts/Arial Unicode.ttf',
        ]
        if size in _FONT_CACHE:
            return _FONT_CACHE[size]
        for path in FONT_CANDIDATES:
            if Path(path).exists():
                try:
                    font = ImageFont.truetype(path, size)
                    _FONT_CACHE[size] = font
                    return font
                except Exception:
                    continue
        font = ImageFont.load_default()
        _FONT_CACHE[size] = font
        return font

_FONT_CACHE = {}

# ============================================================
# EbookLib 导入
# ============================================================
try:
    from ebooklib import epub
except ImportError:
    print("请先安装 ebooklib: pip install ebooklib")
    sys.exit(1)


# ============================================================
# Markdown 解析
# ============================================================

def _md_to_html_basic(text: str) -> str:
    """将 Markdown 文本转为基础 HTML (无需外部库)"""
    lines = text.split('\n')
    out_lines = []
    i = 0
    in_code = False
    code_buf = []
    code_lang = ''
    in_ul = False
    in_ol = False
    ol_counter = 0

    def flush_code():
        nonlocal code_buf, code_lang
        if code_buf:
            lang_attr = f' class="language-{html.escape(code_lang)}"' if code_lang else ''
            code_text = html.escape('\n'.join(code_buf))
            out_lines.append(f'<pre><code{lang_attr}>{code_text}</code></pre>')
            code_buf = []
            code_lang = ''

    def flush_ul():
        nonlocal in_ul
        if in_ul:
            out_lines.append('</ul>')
            in_ul = False

    def flush_ol():
        nonlocal in_ol, ol_counter
        if in_ol:
            out_lines.append('</ol>')
            in_ol = False
        ol_counter = 0

    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.startswith('```'):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_code()
                in_code = True
                code_lang = line[3:].strip()
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        stripped = line.strip()

        # 空行
        if not stripped:
            flush_ul()
            flush_ol()
            i += 1
            continue

        # 标题
        h_match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if h_match:
            flush_ul()
            flush_ol()
            level = len(h_match.group(1))
            title_text = h_match.group(2).strip()
            # 生成锚点 ID
            anchor_id = re.sub(r'[^\w一-鿿\- ]', '', title_text).replace(' ', '-').lower()
            out_lines.append(f'<h{level} id="{html.escape(anchor_id)}">{_inline_md(title_text)}</h{level}>')
            i += 1
            continue

        # 水平线
        if re.match(r'^---+\s*$', stripped) or re.match(r'^\*\*\*+\s*$', stripped):
            flush_ul()
            flush_ol()
            out_lines.append('<hr/>')
            i += 1
            continue

        # 无序列表
        ul_match = re.match(r'^[\*\-]\s+(.+)$', stripped)
        if ul_match:
            flush_ol()
            if not in_ul:
                out_lines.append('<ul>')
                in_ul = True
            out_lines.append(f'<li>{_inline_md(ul_match.group(1))}</li>')
            i += 1
            continue

        # 有序列表
        ol_match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
        if ol_match:
            flush_ul()
            if not in_ol:
                out_lines.append('<ol>')
                in_ol = True
            out_lines.append(f'<li>{_inline_md(ol_match.group(2))}</li>')
            i += 1
            continue

        # 引用
        if stripped.startswith('> '):
            flush_ul()
            flush_ol()
            quote_text = re.sub(r'^>\s?', '', stripped)
            out_lines.append(f'<blockquote>{_inline_md(quote_text)}</blockquote>')
            i += 1
            continue

        # 段落
        flush_ul()
        flush_ol()
        para = _inline_md(stripped)
        # 检测图片段落
        if para.startswith('<img') and para.endswith('/>'):
            out_lines.append(para)
        else:
            out_lines.append(f'<p>{para}</p>')
        i += 1

    flush_code()
    flush_ul()
    flush_ol()
    return '\n'.join(out_lines)


def _inline_md(text: str) -> str:
    """处理内联 Markdown 格式"""
    # 图片 ![alt](src)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)',
                  r'<img src="\2" alt="\1"/>', text)
    # 链接 [text](url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  r'<a href="\2">\1</a>', text)
    # 粗体 **text** 或 __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # 斜体 *text* 或 _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    # 行内代码 `code`
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # 删除线 ~~text~~
    text = re.sub(r'~~(.+?)~~', r'<del>\1</del>', text)
    # HTML 转义 (防止已有标签被转义)
    return text


def _extract_headings(md_text: str) -> list:
    """从 Markdown 文本中提取 H1/H2 标题列表, 用于 TOC"""
    headings = []
    for line in md_text.split('\n'):
        m = re.match(r'^(#{1,2})\s+(.+)$', line.strip())
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor_id = re.sub(r'[^\w一-鿿\- ]', '', title).replace(' ', '-').lower()
            headings.append((level, title, anchor_id))
    return headings


def _extract_h1_title(md_text: str) -> str:
    """从 Markdown 文本中提取第一个 H1 作为章节标题"""
    for line in md_text.split('\n'):
        m = re.match(r'^#\s+(.+)$', line.strip())
        if m:
            return m.group(1).strip()
    return ''


def _make_section_html(md_text: str) -> str:
    """将 Markdown 文本转换为 EPUB 章节 HTML"""
    body = _md_to_html_basic(md_text)
    return f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head>
<meta charset="utf-8"/>
<style>
  body {{
    font-family: "PingFang SC", "Heiti SC", -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.8;
    font-size: 1em;
    color: #333;
    padding: 1em;
  }}
  h1 {{ font-size: 1.6em; color: #1a1a2e; margin-top: 1.5em; border-bottom: 2px solid #e9c46a; padding-bottom: 0.3em; }}
  h2 {{ font-size: 1.3em; color: #1a1a2e; margin-top: 1.2em; }}
  h3 {{ font-size: 1.1em; color: #16213e; margin-top: 1em; }}
  p {{ margin: 0.8em 0; text-indent: 0; }}
  blockquote {{
    border-left: 3px solid #e9c46a;
    margin: 1em 0;
    padding: 0.5em 1em;
    background: #f8f6f0;
    color: #555;
  }}
  pre {{
    background: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 0.8em;
    font-size: 0.85em;
    overflow-x: auto;
    white-space: pre-wrap;
  }}
  code {{ background: #f0f0f0; padding: 0.1em 0.3em; border-radius: 3px; font-size: 0.9em; }}
  img {{ max-width: 100%; height: auto; display: block; margin: 1em auto; }}
  hr {{ border: none; border-top: 1px solid #e9c46a; margin: 2em 0; }}
  ul, ol {{ margin: 0.5em 0; padding-left: 2em; }}
  li {{ margin: 0.3em 0; }}
  a {{ color: #2a9d8f; }}
  del {{ color: #999; }}
</style>
</head>
<body>
{body}
</body>
</html>'''


def _make_toc_page(chapters: list, book_title: str) -> str:
    """生成目录页 HTML"""
    items_html = ''
    for ch_title in chapters:
        anchor_id = re.sub(r'[^\w一-鿿\- ]', '', ch_title).replace(' ', '-').lower()
        items_html += f'<li><a href="ch-{anchor_id}.xhtml">{html.escape(ch_title)}</a></li>\n'

    return f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>目录</title>
<style>
  body {{
    font-family: "PingFang SC", "Heiti SC", -apple-system, BlinkMacSystemFont, sans-serif;
    padding: 2em;
    line-height: 2;
  }}
  h1 {{ color: #1a1a2e; border-bottom: 2px solid #e9c46a; padding-bottom: 0.3em; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ margin: 0.8em 0; font-size: 1.1em; }}
  a {{ color: #1a1a2e; text-decoration: none; }}
  a:hover {{ color: #e9c46a; }}
</style>
</head>
<body>
<h1>目录</h1>
<ul>
{items_html}
</ul>
</body>
</html>'''


def _make_copyright_page(author: str, year: str = None, extra: str = '') -> str:
    """生成版权页 HTML"""
    if year is None:
        year = str(datetime.now().year)
    body = f'''<h1>版权信息</h1>
<p>作者: {html.escape(author)}</p>
<p>© {year} {html.escape(author)}. All rights reserved.</p>
<p>本电子书仅供购买者个人阅读，未经授权不得转载、复制或分发。</p>'''
    if extra:
        body += f'\n<p>{html.escape(extra)}</p>'

    return f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>版权信息</title>
<style>
  body {{
    font-family: "PingFang SC", "Heiti SC", -apple-system, BlinkMacSystemFont, sans-serif;
    padding: 2em;
    line-height: 2;
    color: #555;
    text-align: center;
  }}
  h1 {{ color: #1a1a2e; margin-top: 3em; }}
</style>
</head>
<body>
{body}
</body>
</html>'''


def _make_about_page(text: str, heading: str = '前言') -> str:
    """生成前/后记页面"""
    body = _md_to_html_basic(text)
    return f'''<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>{html.escape(heading)}</title>
<style>
  body {{
    font-family: "PingFang SC", "Heiti SC", -apple-system, BlinkMacSystemFont, sans-serif;
    padding: 2em;
    line-height: 2;
    color: #333;
  }}
  h1 {{ color: #1a1a2e; }}
</style>
</head>
<body>
<h1>{html.escape(heading)}</h1>
{body}
</body>
</html>'''


# ============================================================
# 封面生成 (Pillow)
# ============================================================

def generate_cover_png(title: str, author: str, output_path: str,
                       subtitle: str = '',
                       series: str = '', series_index: int = 0) -> str:
    """生成电子书封面 PNG, 使用品牌色板

    封面尺寸: EPUB 标准 1600x2560 (宽高比 5:8)
    """
    width, height = 1600, 2560
    deep_blue = BRAND_RGB['deep_blue']
    navy = BRAND_RGB['navy']
    yellow = BRAND_RGB['yellow']
    red = BRAND_RGB['red']
    white = BRAND_RGB['white']

    img = Image.new('RGB', (width, height), deep_blue)
    draw = ImageDraw.Draw(img)

    # --- 渐变背景: 深蓝 → 深海蓝 ---
    for y in range(height):
        ratio = y / height
        r = int(deep_blue[0] * (1 - ratio) + navy[0] * ratio)
        g = int(deep_blue[1] * (1 - ratio) + navy[1] * ratio)
        b = int(deep_blue[2] * (1 - ratio) + navy[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # --- 几何装饰: 左上角黄色三角 ---
    tri_size = int(width * 0.45)
    draw.polygon([(0, 0), (tri_size, 0), (0, tri_size)],
                 fill=(max(0, yellow[0] - 80), max(0, yellow[1] - 80), max(0, yellow[2] - 80)))
    tri_small = int(tri_size * 0.6)
    draw.polygon([(0, 0), (tri_small, 0), (0, tri_small)],
                 fill=yellow)

    # --- 右下角装饰圆环 ---
    circle_r = int(width * 0.35)
    cx = width - int(circle_r * 0.25)
    cy = height - int(circle_r * 0.25)
    very_dark = tuple(max(0, c - 20) for c in navy)
    draw.ellipse([(cx - circle_r, cy - circle_r),
                  (cx + circle_r, cy + circle_r)],
                 fill=very_dark)

    # --- 顶部装饰线 ---
    draw.line([(0, 6), (width, 6)], fill=yellow, width=6)

    # --- 底部装饰线 ---
    draw.line([(0, height - 12), (width, height - 12)], fill=yellow, width=3)

    # --- 系列标识 ---
    if series:
        series_font = find_font(28)
        draw.text((60, 50), series, fill=yellow, font=series_font)

    if series_index > 0:
        vol_font = find_font(24)
        vol_text = f'VOL. {series_index}'
        draw.text((width - 200, 55), vol_text, fill=(200, 200, 200), font=vol_font)

    # --- 主标题 ---
    # 标题较长时分两行
    title_font_large = find_font(72)
    title_font_small = find_font(56)
    max_title_w = width - 120

    if len(title) > 14:
        # 尝试在标点处或空格处折行
        mid = len(title) // 2
        break_points = [i for i, c in enumerate(title) if c in '，。！？；、:： ']
        if break_points:
            split_i = min(break_points, key=lambda x: abs(x - mid)) + 1
            line1 = title[:split_i].strip()
            line2 = title[split_i:].strip()
        else:
            line1 = title[:mid]
            line2 = title[mid:]

        # 大号字尝试 line1
        bbox1 = draw.textbbox((0, 0), line1, font=title_font_large)
        tw1 = bbox1[2] - bbox1[0]
        if tw1 > max_title_w:
            font_line1 = title_font_small
            font_line2 = title_font_small
        else:
            font_line1 = title_font_large
            font_line2 = title_font_small

        bbox1 = draw.textbbox((0, 0), line1, font=font_line1)
        tw1 = bbox1[2] - bbox1[0]
        bbox2 = draw.textbbox((0, 0), line2, font=font_line2)
        tw2 = bbox2[2] - bbox2[0]

        y1 = int(height * 0.25)
        draw.text(((width - tw1) // 2, y1), line1, fill=white, font=font_line1)
        y2 = y1 + bbox1[3] - bbox1[1] + 20
        draw.text(((width - tw2) // 2, y2), line2, fill=white, font=font_line2)
    else:
        bbox = draw.textbbox((0, 0), title, font=title_font_large)
        tw = bbox[2] - bbox[0]
        y = int(height * 0.28)
        draw.text(((width - tw) // 2, y), title, fill=white, font=title_font_large)

    # --- 副标题 ---
    if subtitle:
        sub_font = find_font(32)
        sbbox = draw.textbbox((0, 0), subtitle, font=sub_font)
        sw = sbbox[2] - sbbox[0]
        sy = int(height * 0.50)
        draw.text(((width - sw) // 2, sy), subtitle, fill=yellow, font=sub_font)

    # --- 红色强调块 ---
    accent_y = int(height * 0.72)
    accent_font = find_font(26)
    accent_text = f'作者: {author}'
    abbox = draw.textbbox((0, 0), accent_text, font=accent_font)
    aw = abbox[2] - abbox[0]
    # 红色底色条
    bar_pad = 30
    bar_y = accent_y - 15
    bar_h = 60
    draw.rectangle([(bar_pad, bar_y), (width - bar_pad, bar_y + bar_h)],
                   fill=red)
    draw.text(((width - aw) // 2, accent_y), accent_text,
              fill=white, font=accent_font)

    # 底部版权年份
    year_font = find_font(22)
    year_text = f'{datetime.now().year}'
    ybbox = draw.textbbox((0, 0), year_text, font=year_font)
    yw = ybbox[2] - ybbox[0]
    draw.text(((width - yw) // 2, height - 80), year_text,
              fill=(150, 150, 150), font=year_font)

    # 保存
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out), 'PNG', optimize=True)
    print(f"  Cover image saved: {out} ({width}x{height})")
    return str(out)


# ============================================================
# EPUB 构建
# ============================================================

def build_epub(
    chapters: list,
    output_path: str,
    title: str = 'Untitled',
    author: str = '一言一行',
    lang: str = 'zh-CN',
    cover_path: str = '',
    no_cover: bool = False,
    no_toc: bool = False,
    copyright_notice: str = '',
    series: str = '',
    series_index: int = 0,
    preface_text: str = '',
    afterword_text: str = '',
) -> str:
    """构建 EPUB 文件

    Args:
        chapters: 章节列表, 每个元素为 (filename, html_content, chapter_title)
        output_path: 输出 .epub 路径
        title: 书名
        author: 作者
        lang: 语言代码
        cover_path: 封面图片路径 (若提供则用于封面页)
        no_cover: 跳过封面页
        no_toc: 跳过目录页
        copyright_notice: 版权声明
        series: 系列名
        series_index: 系列卷号
        preface_text: 前言 Markdown 文本
        afterword_text: 后记 Markdown 文本
    """

    # --- 创建 EPUB 书籍 ---
    book = epub.EpubBook()

    # --- 元数据 ---
    book.set_identifier(f'urn:uuid:{title}-{author}-{datetime.now().strftime("%Y%m%d%H%M%S")}')
    book.set_title(title)
    book.set_language(lang)
    book.add_author(author)
    book.add_metadata('DC', 'date', datetime.now().strftime('%Y-%m-%d'))

    # 系列元数据 (EPUB 3 通过 opf:collection)
    if series:
        book.add_metadata('OPF', 'meta', series,
                          {'property': 'belongs-to-collection', 'id': 'collection'})
        if series_index > 0:
            book.add_metadata('OPF', 'meta', str(series_index),
                              {'property': 'group-position', 'refines': '#collection'})

    # --- 封面 ---
    if not no_cover and cover_path and Path(cover_path).exists():
        with open(cover_path, 'rb') as f:
            cover_img_data = f.read()
        book.set_cover('cover.png', cover_img_data)

    # --- 导航栏构建 ---
    spine = ['nav']
    toc_items = []

    # --- 版权页 ---
    if not no_cover:
        year = str(datetime.now().year)
        cp_text = copyright_notice or f'© {year} {author}'
        copyright_html = _make_copyright_page(author, year, copyright_notice)
        cp_page = epub.EpubHtml(
            title='版权信息',
            file_name='copyright.xhtml',
            lang=lang,
        )
        cp_page.content = copyright_html
        book.add_item(cp_page)
        spine.append(cp_page)

    # --- 前言 ---
    if preface_text:
        preface_html = _make_about_page(preface_text, '前言')
        preface_page = epub.EpubHtml(
            title='前言',
            file_name='preface.xhtml',
            lang=lang,
        )
        preface_page.content = preface_html
        book.add_item(preface_page)
        spine.append(preface_page)

    # --- 目录页 ---
    if not no_toc:
        ch_titles = [ch[2] for ch in chapters]
        toc_html = _make_toc_page(ch_titles, title)
        toc_page = epub.EpubHtml(
            title='目录',
            file_name='toc.xhtml',
            lang=lang,
        )
        toc_page.content = toc_html
        book.add_item(toc_page)
        spine.append(toc_page)

    # --- 章节 ---
    for idx, (filename, html_content, ch_title) in enumerate(chapters, 1):
        # 文件名: ch-{title}.xhtml
        ch_file = filename
        ch_html = html_content

        ch_page = epub.EpubHtml(
            title=ch_title,
            file_name=ch_file,
            lang=lang,
        )
        ch_page.content = ch_html
        book.add_item(ch_page)
        spine.append(ch_page)

        # 构建 TOC 条目
        toc_item = epub.Link(ch_file, ch_title, ch_file.replace('.xhtml', ''))
        toc_items.append(toc_item)

    # --- 后记 ---
    if afterword_text:
        afterword_html = _make_about_page(afterword_text, '后记')
        afterword_page = epub.EpubHtml(
            title='后记',
            file_name='afterword.xhtml',
            lang=lang,
        )
        afterword_page.content = afterword_html
        book.add_item(afterword_page)
        spine.append(afterword_page)

    # --- CSS 样式 ---
    css_style = '''
    @namespace epub "http://www.idpf.org/2007/ops";
    body {
        font-family: "PingFang SC", "Heiti SC", -apple-system, BlinkMacSystemFont, sans-serif;
        line-height: 1.8;
        font-size: 1em;
        color: #333;
        padding: 1em;
    }
    h1 { font-size: 1.6em; color: #1a1a2e; margin-top: 1.5em; border-bottom: 2px solid #e9c46a; padding-bottom: 0.3em; }
    h2 { font-size: 1.3em; color: #1a1a2e; margin-top: 1.2em; }
    h3 { font-size: 1.1em; color: #16213e; margin-top: 1em; }
    p { margin: 0.8em 0; }
    blockquote { border-left: 3px solid #e9c46a; margin: 1em 0; padding: 0.5em 1em; background: #f8f6f0; }
    pre { background: #f5f5f5; border: 1px solid #ddd; padding: 0.8em; font-size: 0.85em; }
    code { background: #f0f0f0; padding: 0.1em 0.3em; border-radius: 3px; }
    '''
    nav_css = epub.EpubItem(
        uid='style_nav',
        file_name='style/nav.css',
        media_type='text/css',
        content=css_style,
    )
    book.add_item(nav_css)

    # --- 每个页面引用 CSS ---
    for item in book.get_items():
        if isinstance(item, epub.EpubHtml):
            item.add_item(nav_css)

    # --- 目录结构 ---
    book.toc = toc_items

    # --- spine 顺序 ---
    book.spine = spine

    # --- 添加导航 (EPUB3) ---
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # --- 写入 EPUB ---
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    epub.write_epub(str(out), book, {})
    print(f"  EPUB written: {out} ({out.stat().st_size / 1024:.0f} KB)")
    return str(out)


# ============================================================
# 主要入口
# ============================================================

def _parse_chapter_md(file_path: str) -> tuple:
    """解析单个 Markdown 文件, 返回 (filename, html, title)"""
    path = Path(file_path)
    if not path.exists():
        print(f"  [WARN] File not found: {path}")
        return None

    md_text = path.read_text(encoding='utf-8')
    ch_title = _extract_h1_title(md_text) or path.stem

    # 文件名安全化
    safe_title = re.sub(r'[^\w一-鿿\-]', '', ch_title).replace(' ', '-').lower()[:60]
    if not safe_title:
        safe_title = re.sub(r'[^\w\-]', '', path.stem)[:60]
    filename = f'ch-{safe_title}.xhtml'

    html_content = _make_section_html(md_text)
    return (filename, html_content, ch_title)


def cmd_single(args):
    """从单个 Markdown 文件生成 EPUB"""
    print(f"\n=== Single Markdown → EPUB ===")
    print(f"  Input: {args.input}")

    result = _parse_chapter_md(args.input)
    if not result:
        print("  ERROR: No valid content found")
        sys.exit(1)

    filename, html_content, ch_title = result
    chapters = [(filename, html_content, ch_title)]

    # 封面
    cover_path = ''
    if not args.no_cover:
        if args.cover_image and Path(args.cover_image).exists():
            cover_path = args.cover_image
        else:
            cover_path = args.output.replace('.epub', '-cover.png')
            generate_cover_png(
                title=args.title or ch_title,
                author=args.author,
                subtitle=args.subtitle,
                output_path=cover_path,
                series=args.series,
                series_index=args.series_index,
            )

    # 前言/后记 (从文件读取)
    preface = ''
    afterword = ''
    if args.preface:
        if Path(args.preface).exists():
            preface = Path(args.preface).read_text(encoding='utf-8')
        else:
            preface = args.preface
    if args.afterword:
        if Path(args.afterword).exists():
            afterword = Path(args.afterword).read_text(encoding='utf-8')
        else:
            afterword = args.afterword

    # 构建 EPUB
    build_epub(
        chapters=chapters,
        output_path=args.output,
        title=args.title or ch_title,
        author=args.author,
        lang=args.lang,
        cover_path=cover_path,
        no_cover=args.no_cover,
        no_toc=args.no_toc,
        copyright_notice=args.copyright,
        series=args.series,
        series_index=args.series_index,
        preface_text=preface,
        afterword_text=afterword,
    )


def cmd_dir(args):
    """从目录下的所有 Markdown 文件生成 EPUB"""
    print(f"\n=== Directory → EPUB ===")
    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"  ERROR: Not a directory: {input_dir}")
        sys.exit(1)

    md_files = sorted(input_dir.glob('*.md'))
    print(f"  Input dir: {input_dir} ({len(md_files)} .md files)")

    chapters = []
    for md_path in md_files:
        result = _parse_chapter_md(str(md_path))
        if result:
            chapters.append(result)
            print(f"    + {md_path.name} → {result[0]} ({result[2][:50]})")

    if not chapters:
        print("  ERROR: No valid markdown files found")
        sys.exit(1)

    # 封面
    cover_path = ''
    if not args.no_cover:
        if args.cover_image and Path(args.cover_image).exists():
            cover_path = args.cover_image
        else:
            cover_path = args.output.replace('.epub', '-cover.png')
            generate_cover_png(
                title=args.title,
                author=args.author,
                subtitle=args.subtitle,
                output_path=cover_path,
                series=args.series,
                series_index=args.series_index,
            )

    # 前言/后记
    preface = ''
    afterword = ''
    if args.preface:
        if Path(args.preface).exists():
            preface = Path(args.preface).read_text(encoding='utf-8')
        else:
            preface = args.preface
    if args.afterword:
        if Path(args.afterword).exists():
            afterword = Path(args.afterword).read_text(encoding='utf-8')
        else:
            afterword = args.afterword

    build_epub(
        chapters=chapters,
        output_path=args.output,
        title=args.title,
        author=args.author,
        lang=args.lang,
        cover_path=cover_path,
        no_cover=args.no_cover,
        no_toc=args.no_toc,
        copyright_notice=args.copyright,
        series=args.series,
        series_index=args.series_index,
        preface_text=preface,
        afterword_text=afterword,
    )


def cmd_custom(args):
    """从指定顺序的 Markdown 文件生成 EPUB"""
    print(f"\n=== Custom Chapters → EPUB ===")
    print(f"  Chapters ({len(args.chapters)}):")
    for ch in args.chapters:
        print(f"    - {ch}")

    chapters = []
    for ch_path in args.chapters:
        result = _parse_chapter_md(ch_path)
        if result:
            chapters.append(result)
        else:
            print(f"  [WARN] Skipping: {ch_path}")

    if not chapters:
        print("  ERROR: No valid chapters found")
        sys.exit(1)

    # 封面
    cover_path = ''
    if not args.no_cover:
        if args.cover_image and Path(args.cover_image).exists():
            cover_path = args.cover_image
        else:
            cover_path = args.output.replace('.epub', '-cover.png')
            generate_cover_png(
                title=args.title,
                author=args.author,
                subtitle=args.subtitle,
                output_path=cover_path,
                series=args.series,
                series_index=args.series_index,
            )

    # 前言/后记
    preface = ''
    afterword = ''
    if args.preface:
        if Path(args.preface).exists():
            preface = Path(args.preface).read_text(encoding='utf-8')
        else:
            preface = args.preface
    if args.afterword:
        if Path(args.afterword).exists():
            afterword = Path(args.afterword).read_text(encoding='utf-8')
        else:
            afterword = args.afterword

    build_epub(
        chapters=chapters,
        output_path=args.output,
        title=args.title,
        author=args.author,
        lang=args.lang,
        cover_path=cover_path,
        no_cover=args.no_cover,
        no_toc=args.no_toc,
        copyright_notice=args.copyright,
        series=args.series,
        series_index=args.series_index,
        preface_text=preface,
        afterword_text=afterword,
    )


def main():
    parser = argparse.ArgumentParser(
        description='Markdown → EPUB 电子书生成器 (一人公司内容工厂)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # --- single ---
    sp_single = subparsers.add_parser('single', help='单个 Markdown 文件 → EPUB')
    sp_single.add_argument('input', help='输入的 .md 文件路径')
    sp_single.add_argument('-o', '--output', required=True, help='输出 .epub 路径')
    sp_single.add_argument('--title', help='书名 (默认用 Markdown H1)')
    sp_single.add_argument('--subtitle', default='', help='封面副标题')
    sp_single.add_argument('--author', default='一言一行', help='作者名')
    sp_single.add_argument('--lang', default='zh-CN', help='语言代码')
    sp_single.add_argument('--cover-image', help='已有封面图片路径')
    sp_single.add_argument('--no-cover', action='store_true', help='跳过封面生成')
    sp_single.add_argument('--no-toc', action='store_true', help='跳过目录页')
    sp_single.add_argument('--copyright', default='', help='版权声明')
    sp_single.add_argument('--series', default='', help='系列名')
    sp_single.add_argument('--series-index', type=int, default=0, help='系列卷号')
    sp_single.add_argument('--preface', default='', help='前言 (Markdown 文本或文件路径)')
    sp_single.add_argument('--afterword', default='', help='后记 (Markdown 文本或文件路径)')

    # --- dir ---
    sp_dir = subparsers.add_parser('dir', help='目录下所有 .md 文件 → EPUB')
    sp_dir.add_argument('input_dir', help='存放 .md 文件的目录')
    sp_dir.add_argument('-o', '--output', required=True, help='输出 .epub 路径')
    sp_dir.add_argument('--title', default='合集', help='书名')
    sp_dir.add_argument('--subtitle', default='', help='封面副标题')
    sp_dir.add_argument('--author', default='一言一行', help='作者名')
    sp_dir.add_argument('--lang', default='zh-CN', help='语言代码')
    sp_dir.add_argument('--cover-image', help='已有封面图片路径')
    sp_dir.add_argument('--no-cover', action='store_true', help='跳过封面生成')
    sp_dir.add_argument('--no-toc', action='store_true', help='跳过目录页')
    sp_dir.add_argument('--copyright', default='', help='版权声明')
    sp_dir.add_argument('--series', default='', help='系列名')
    sp_dir.add_argument('--series-index', type=int, default=0, help='系列卷号')
    sp_dir.add_argument('--preface', default='', help='前言 (Markdown 文本或文件路径)')
    sp_dir.add_argument('--afterword', default='', help='后记 (Markdown 文本或文件路径)')

    # --- custom ---
    sp_custom = subparsers.add_parser('custom', help='自定义 Markdown 文件顺序 → EPUB')
    sp_custom.add_argument('chapters', nargs='+', help='按顺序排列的 .md 文件路径')
    sp_custom.add_argument('-o', '--output', required=True, help='输出 .epub 路径')
    sp_custom.add_argument('--title', default='自定义合集', help='书名')
    sp_custom.add_argument('--subtitle', default='', help='封面副标题')
    sp_custom.add_argument('--author', default='一言一行', help='作者名')
    sp_custom.add_argument('--lang', default='zh-CN', help='语言代码')
    sp_custom.add_argument('--cover-image', help='已有封面图片路径')
    sp_custom.add_argument('--no-cover', action='store_true', help='跳过封面生成')
    sp_custom.add_argument('--no-toc', action='store_true', help='跳过目录页')
    sp_custom.add_argument('--copyright', default='', help='版权声明')
    sp_custom.add_argument('--series', default='', help='系列名')
    sp_custom.add_argument('--series-index', type=int, default=0, help='系列卷号')
    sp_custom.add_argument('--preface', default='', help='前言 (Markdown 文本或文件路径)')
    sp_custom.add_argument('--afterword', default='', help='后记 (Markdown 文本或文件路径)')

    args = parser.parse_args()

    if args.command == 'single':
        cmd_single(args)
    elif args.command == 'dir':
        cmd_dir(args)
    elif args.command == 'custom':
        cmd_custom(args)
    else:
        parser.print_help()
        sys.exit(1)

    print("\nDone.")


if __name__ == '__main__':
    main()
