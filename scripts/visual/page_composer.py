#!/usr/bin/env python3
"""
page_composer.py -- 公众号图文排版HTML生成

将Markdown文章 + 配图路径列表 合成为品牌风格的内联CSS HTML页面。
布局：封面图 -> 标题 -> 摘要 -> 正文段落+配图交替 -> 结论CTA

用法:
  python3 page_composer.py \
    --type wechat \
    --article biz/content/pipeline/writing/T1-004/draft-v1.md \
    --cover biz/content/assets/covers/T1-004/wechat-cover.png \
    --figures biz/content/assets/figures/T1-004/*.png \
    --output biz/content/assets/pages/T1-004/wechat.html
"""

import argparse
import re
import sys
from pathlib import Path

# 公共模块 — 确保从任意目录运行时可找到本模块
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_common import (
    BRAND_HEX, FONT_STACK, find_font, create_gradient_bg,
    image_to_base64_src, markdown_to_html, interleave_figures,
    html_escape, html_escape_attr,
)

# 品牌色板（直接引用公共模块的HEX色板）
C = BRAND_HEX

WECHAT_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_esc}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: {font_stack};
    background-color: {bg_color};
    color: {text_color};
    line-height: 1.8;
    max-width: 680px;
    margin: 0 auto;
    padding: 0;
  }}
  .cover-wrap {{
    width: 100%;
    max-height: 400px;
    overflow: hidden;
    position: relative;
  }}
  .cover-wrap img {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 0 0 8px 8px;
  }}
  .article-header {{
    padding: 28px 24px 16px;
    background: linear-gradient(180deg, {deep_blue} 0%, {navy} 100%);
  }}
  .article-title {{
    font-size: 26px;
    font-weight: 700;
    color: {yellow};
    line-height: 1.4;
    margin-bottom: 12px;
  }}
  .article-summary {{
    font-size: 15px;
    color: {white};
    opacity: 0.8;
    line-height: 1.6;
    padding-left: 14px;
    border-left: 3px solid {red};
  }}
  .article-body {{
    padding: 20px 24px;
    background-color: {bg_color};
  }}
  .article-body p {{
    font-size: 16px;
    color: {text_color};
    margin-bottom: 18px;
    text-align: justify;
  }}
  .article-body h2 {{
    font-size: 20px;
    font-weight: 700;
    color: {yellow};
    margin: 28px 0 14px;
    padding-bottom: 8px;
    border-bottom: 2px solid {red};
  }}
  .article-body h3 {{
    font-size: 18px;
    font-weight: 600;
    color: {white};
    margin: 22px 0 10px;
  }}
  .article-body blockquote {{
    background: linear-gradient(135deg, {navy} 0%, {deep_blue} 100%);
    border-left: 4px solid {red};
    padding: 16px 20px;
    margin: 18px 0;
    border-radius: 0 8px 8px 0;
    color: {white};
    font-size: 15px;
  }}
  .article-body code {{
    background-color: {navy};
    color: {yellow};
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 14px;
    font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  }}
  .article-body pre {{
    background-color: {deep_blue};
    border: 1px solid {navy};
    border-radius: 8px;
    padding: 16px;
    margin: 18px 0;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.6;
    color: {white};
    font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  }}
  .article-body pre code {{
    background: none;
    padding: 0;
  }}
  .article-body ul, .article-body ol {{
    padding-left: 24px;
    margin-bottom: 18px;
  }}
  .article-body li {{
    font-size: 15px;
    color: {text_color};
    margin-bottom: 8px;
    line-height: 1.7;
  }}
  .article-body strong {{
    color: {yellow};
    font-weight: 600;
  }}
  .article-body em {{
    color: {red};
    font-style: normal;
  }}
  .figure-wrap {{
    width: 100%;
    margin: 18px 0;
    text-align: center;
  }}
  .figure-wrap img {{
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }}
  .figure-wrap .fig-caption {{
    font-size: 13px;
    color: {white};
    opacity: 0.6;
    margin-top: 8px;
  }}
  .cta-section {{
    margin: 36px 24px 24px;
    padding: 24px;
    background: linear-gradient(135deg, {navy} 0%, {deep_blue} 100%);
    border-radius: 12px;
    text-align: center;
    border: 1px solid {red};
  }}
  .cta-section .cta-title {{
    font-size: 18px;
    color: {yellow};
    font-weight: 700;
    margin-bottom: 8px;
  }}
  .cta-section .cta-text {{
    font-size: 14px;
    color: {white};
    opacity: 0.8;
  }}
  .footer {{
    padding: 16px 24px;
    text-align: center;
    font-size: 12px;
    color: {white};
    opacity: 0.4;
  }}
</style>
</head>
<body>

<div class="cover-wrap">
{cover_html}
</div>

<div class="article-header">
  <div class="article-title">{title_esc}</div>
  <div class="article-summary">{summary_esc}</div>
</div>

<div class="article-body">
{body_html}
</div>

<div class="cta-section">
  <div class="cta-title">{cta_title_esc}</div>
  <div class="cta-text">{cta_text_esc}</div>
</div>

<div class="footer">
  {footer_esc}
</div>

</body>
</html>'''


def make_cover_html(cover_path: str) -> str:
    """生成封面图HTML"""
    if not cover_path:
        return ''
    src = image_to_base64_src(cover_path)
    if not src:
        return ''
    return f'  <img src="{src}" alt="cover">'


def compose_wechat_html(article_path: str, cover_path: str, figures: list,
                         output_path: str, title: str = '', summary: str = '',
                         cta_title: str = '', cta_text: str = '',
                         footer_text: str = '') -> str:
    """生成公众号图文排版HTML页面"""
    # 读取文章内容
    content = '<p>Article content not found.</p>'
    if article_path and Path(article_path).exists():
        try:
            raw = Path(article_path).read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: failed to read article: {e}")
            raw = ''

        if raw:
            # 提取标题
            if not title:
                title_match = re.match(r'^#\s+(.+)$', raw, re.MULTILINE)
                title = title_match.group(1) if title_match else 'Untitled'
            # 提取摘要
            if not summary:
                summary_match = re.search(r'<!--\s*summary:\s*(.+?)\s*-->', raw)
                if summary_match:
                    summary = summary_match.group(1)
                else:
                    paragraphs = re.split(r'\n{2,}', raw.split('\n', 1)[-1] if '\n' in raw else '')
                    for p in paragraphs:
                        p = p.strip()
                        if p and not p.startswith('#') and not p.startswith('<!--') and not p.startswith('```'):
                            summary = p[:120]
                            break
            # 从正文移除标题行和摘要标记
            content = re.sub(r'^#\s+.+$', '', raw, count=1, flags=re.MULTILINE).strip()
            content = re.sub(r'<!--\s*summary:.+?-->', '', content).strip()

    if not title:
        title = 'Untitled'
    if not summary:
        summary = ''
    if not cta_title:
        cta_title = 'Follow for more'
    if not cta_text:
        cta_text = 'Subscribe to get the latest insights delivered to your inbox.'
    if not footer_text:
        footer_text = '&copy; yiyan-yixing | Powered by AI'

    # Markdown转HTML
    body_html = markdown_to_html(content)

    # 配图交错插入正文
    body_html = interleave_figures(body_html, figures, figure_class='figure-wrap')

    # 封面HTML
    cover_html = make_cover_html(cover_path)

    # 填充模板（所有用户输入值做HTML转义防XSS）
    html = WECHAT_HTML_TEMPLATE.format(
        title_esc=html_escape(title),
        font_stack=FONT_STACK,
        bg_color=C['deep_blue'],
        text_color=C['white'],
        deep_blue=C['deep_blue'],
        navy=C['navy'],
        yellow=C['yellow'],
        white=C['white'],
        red=C['red'],
        positive=C['positive'],
        cover_html=cover_html,
        summary_esc=html_escape(summary),
        body_html=body_html,
        cta_title_esc=html_escape(cta_title),
        cta_text_esc=html_escape(cta_text),
        footer_esc=html_escape(footer_text),
    )

    # 写入文件
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f"WeChat HTML saved: {out} ({out.stat().st_size} bytes)")
    return str(out)


def main():
    parser = argparse.ArgumentParser(description='Page Composer - WeChat HTML article layout')
    parser.add_argument('--type', default='wechat', choices=['wechat'],
                        help='Page type (default: wechat)')
    parser.add_argument('--article', required=True, help='Markdown article path')
    parser.add_argument('--cover', default=None, help='Cover image path')
    parser.add_argument('--figures', nargs='*', default=[], help='Figure image paths')
    parser.add_argument('--title', default='', help='Override article title')
    parser.add_argument('--summary', default='', help='Override article summary')
    parser.add_argument('--cta-title', default='', help='CTA section title')
    parser.add_argument('--cta-text', default='', help='CTA section text')
    parser.add_argument('--footer', default='', help='Footer text')
    parser.add_argument('--output', required=True, help='Output HTML path')
    args = parser.parse_args()

    compose_wechat_html(
        article_path=args.article,
        cover_path=args.cover or '',
        figures=args.figures,
        output_path=args.output,
        title=args.title,
        summary=args.summary,
        cta_title=args.cta_title,
        cta_text=args.cta_text,
        footer_text=args.footer,
    )


if __name__ == '__main__':
    main()
