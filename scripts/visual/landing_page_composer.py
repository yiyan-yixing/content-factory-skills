#!/usr/bin/env python3
"""
landing_page_composer.py -- 着陆页HTML生成

将Markdown文章 + 配图 + 视频路径 合成为完整HTML着陆页。
特性：hero区域(封面图+标题) + 数据可视化动画区域 + 正文区域 + CTA
响应式布局（mobile-first），CSS动画效果（淡入+滑入），品牌色板统一。
内联CSS+JS，无外部依赖。

用法:
  python3 landing_page_composer.py \
    --article-id T1-004 \
    --title "17个量化策略全失败" \
    --content "文章正文..." \
    --cover biz/content/assets/covers/T1-004/xhs-cover.png \
    --video biz/content/assets/videos/T1-004/clip.mp4 \
    --figures biz/content/assets/figures/T1-004/*.png \
    --output biz/content/assets/pages/T1-004/landing.html
"""

import argparse
import re
import sys
from pathlib import Path

# 公共模块 — 确保从任意目录运行时可找到本模块
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_common import (
    BRAND_HEX, FONT_STACK,
    image_to_base64_src, markdown_to_html, interleave_figures,
    html_escape, html_escape_attr,
)

# 品牌色板
C = BRAND_HEX

LANDING_HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title_esc}</title>
<meta name="description" content="{summary_attr_esc}">
<meta property="og:title" content="{title_attr_esc}">
<meta property="og:description" content="{summary_attr_esc}">
<meta property="og:type" content="article">
<style>
/* Reset & Base */
*, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: {font_stack};
  background-color: {deep_blue};
  color: {white};
  line-height: 1.8;
  overflow-x: hidden;
}}

/* Animations */
@keyframes fadeInUp {{
  from {{ opacity: 0; transform: translateY(30px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
  from {{ opacity: 0; }}
  to {{ opacity: 1; }}
}}
@keyframes slideInLeft {{
  from {{ opacity: 0; transform: translateX(-40px); }}
  to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes slideInRight {{
  from {{ opacity: 0; transform: translateX(40px); }}
  to {{ opacity: 1; transform: translateX(0); }}
}}
@keyframes countUp {{
  from {{ opacity: 0; transform: scale(0.5); }}
  to {{ opacity: 1; transform: scale(1); }}
}}
.animate {{ animation: fadeInUp 0.6s ease-out forwards; opacity: 0; }}
.animate-delay-1 {{ animation-delay: 0.1s; }}
.animate-delay-2 {{ animation-delay: 0.2s; }}
.animate-delay-3 {{ animation-delay: 0.3s; }}
.animate-delay-4 {{ animation-delay: 0.4s; }}
.animate-delay-5 {{ animation-delay: 0.5s; }}

/* Hero Section */
.hero {{
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  overflow: hidden;
}}
.hero-bg {{
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-size: cover;
  background-position: center;
  z-index: 0;
}}
.hero-overlay {{
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(180deg, rgba(26,26,46,0.7) 0%, rgba(22,33,62,0.9) 100%);
  z-index: 1;
}}
.hero-content {{
  position: relative;
  z-index: 2;
  max-width: 800px;
  padding: 20px;
}}
.hero-title {{
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 800;
  color: {yellow};
  line-height: 1.2;
  margin-bottom: 20px;
  animation: fadeInUp 0.8s ease-out;
}}
.hero-subtitle {{
  font-size: clamp(1rem, 2.5vw, 1.4rem);
  color: {white};
  opacity: 0.85;
  line-height: 1.6;
  animation: fadeInUp 0.8s ease-out 0.2s forwards;
  opacity: 0;
}}
.hero-cta {{
  margin-top: 32px;
  animation: fadeInUp 0.8s ease-out 0.4s forwards;
  opacity: 0;
}}
.hero-cta a {{
  display: inline-block;
  padding: 14px 36px;
  background: linear-gradient(135deg, {red}, {yellow});
  color: {deep_blue};
  font-weight: 700;
  font-size: 1.1rem;
  border-radius: 50px;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.hero-cta a:hover {{
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(233,196,106,0.3);
}}

/* Video Section */
.video-section {{
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}}
.video-section video {{
  width: 100%;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}}
.video-section .video-caption {{
  text-align: center;
  font-size: 0.9rem;
  color: {white};
  opacity: 0.6;
  margin-top: 12px;
}}

/* Data Highlights Section */
.data-highlights {{
  padding: 60px 20px;
  background: linear-gradient(180deg, {deep_blue} 0%, {navy} 100%);
}}
.data-highlights-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
  max-width: 900px;
  margin: 0 auto;
}}
.data-card {{
  background: rgba(22,33,62,0.6);
  border: 1px solid rgba(233,196,106,0.15);
  border-radius: 12px;
  padding: 28px 20px;
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
}}
.data-card:hover {{
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(233,196,106,0.1);
}}
.data-card .number {{
  font-size: 2.8rem;
  font-weight: 800;
  color: {red};
  line-height: 1;
  animation: countUp 0.6s ease-out;
}}
.data-card .label {{
  font-size: 0.95rem;
  color: {white};
  opacity: 0.7;
  margin-top: 8px;
}}
.data-section-title {{
  text-align: center;
  font-size: 1.6rem;
  color: {yellow};
  margin-bottom: 32px;
  font-weight: 700;
}}

/* Article Body Section */
.article-section {{
  max-width: 800px;
  margin: 0 auto;
  padding: 60px 20px;
}}
.article-section h2 {{
  font-size: 1.6rem;
  color: {yellow};
  margin: 40px 0 16px;
  padding-bottom: 10px;
  border-bottom: 2px solid {red};
  font-weight: 700;
}}
.article-section h3 {{
  font-size: 1.3rem;
  color: {white};
  margin: 28px 0 12px;
  font-weight: 600;
}}
.article-section p {{
  font-size: 1.05rem;
  color: {white};
  opacity: 0.9;
  margin-bottom: 18px;
  line-height: 1.9;
}}
.article-section blockquote {{
  background: linear-gradient(135deg, {navy}, {deep_blue});
  border-left: 4px solid {red};
  padding: 18px 24px;
  margin: 24px 0;
  border-radius: 0 12px 12px 0;
  font-size: 1rem;
  color: {white};
}}
.article-section code {{
  background: {navy};
  color: {yellow};
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: 'SF Mono', Menlo, Monaco, monospace;
}}
.article-section pre {{
  background: {deep_blue};
  border: 1px solid {navy};
  border-radius: 10px;
  padding: 20px;
  margin: 24px 0;
  overflow-x: auto;
  font-size: 0.85rem;
  line-height: 1.6;
  color: {white};
  font-family: 'SF Mono', Menlo, Monaco, monospace;
}}
.article-section pre code {{
  background: none;
  padding: 0;
}}
.article-section strong {{
  color: {yellow};
  font-weight: 600;
}}
.article-section em {{
  color: {red};
  font-style: normal;
}}
.article-section ul, .article-section ol {{
  padding-left: 28px;
  margin-bottom: 18px;
}}
.article-section li {{
  font-size: 1rem;
  margin-bottom: 8px;
  opacity: 0.9;
}}
.figure-block {{
  margin: 28px 0;
  text-align: center;
}}
.figure-block img {{
  max-width: 100%;
  height: auto;
  border-radius: 10px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.35);
}}
.figure-block .fig-caption {{
  font-size: 0.85rem;
  color: {white};
  opacity: 0.5;
  margin-top: 10px;
}}

/* CTA Section */
.cta-final {{
  padding: 60px 20px;
  text-align: center;
  background: linear-gradient(135deg, {navy}, {deep_blue});
}}
.cta-final-title {{
  font-size: 1.8rem;
  color: {yellow};
  font-weight: 700;
  margin-bottom: 12px;
}}
.cta-final-text {{
  font-size: 1.1rem;
  color: {white};
  opacity: 0.8;
  margin-bottom: 28px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}}
.cta-button {{
  display: inline-block;
  padding: 16px 40px;
  background: linear-gradient(135deg, {red}, {yellow});
  color: {deep_blue};
  font-weight: 700;
  font-size: 1.15rem;
  border-radius: 50px;
  text-decoration: none;
  transition: transform 0.2s, box-shadow 0.2s;
}}
.cta-button:hover {{
  transform: translateY(-3px);
  box-shadow: 0 10px 28px rgba(233,196,106,0.3);
}}

/* Footer */
.footer {{
  padding: 20px;
  text-align: center;
  font-size: 0.8rem;
  color: {white};
  opacity: 0.35;
}}

/* Scroll-triggered animation (JS-driven) */
.scroll-animate {{
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}}
.scroll-animate.visible {{
  opacity: 1;
  transform: translateY(0);
}}

/* Responsive */
@media (max-width: 600px) {{
  .hero-title {{ font-size: 1.8rem; }}
  .hero-subtitle {{ font-size: 1rem; }}
  .data-card .number {{ font-size: 2rem; }}
  .article-section {{ padding: 30px 16px; }}
  .data-highlights {{ padding: 30px 16px; }}
}}
</style>
</head>
<body>

<!-- Hero Section -->
<section class="hero">
  <div class="hero-bg" style="background-image: url({hero_bg})"></div>
  <div class="hero-overlay"></div>
  <div class="hero-content">
    <h1 class="hero-title">{title_esc}</h1>
    <p class="hero-subtitle">{summary_esc}</p>
    <div class="hero-cta">
      <a href="#content">{cta_hero_esc}</a>
    </div>
  </div>
</section>

{video_section}

<!-- Data Highlights Section -->
<section class="data-highlights" id="data">
  <h2 class="data-section-title scroll-animate">{data_section_title_esc}</h2>
  <div class="data-highlights-grid">
    {data_cards_html}
  </div>
</section>

<!-- Article Body Section -->
<section class="article-section scroll-animate" id="content">
{body_html}
</section>

<!-- Final CTA Section -->
<section class="cta-final scroll-animate">
  <h2 class="cta-final-title">{cta_final_title_esc}</h2>
  <p class="cta-final-text">{cta_final_text_esc}</p>
  <a href="#" class="cta-button">{cta_button_esc}</a>
</section>

<!-- Footer -->
<footer class="footer">
  {footer_esc}
</footer>

<script>
// Scroll-triggered animations
(function() {{
  var els = document.querySelectorAll('.scroll-animate');
  var observer = new IntersectionObserver(function(entries) {{
    entries.forEach(function(entry) {{
      if (entry.isIntersecting) {{
        entry.target.classList.add('visible');
      }}
    }});
  }}, {{ threshold: 0.1 }});
  els.forEach(function(el) {{ observer.observe(el); }});
}})();
</script>

</body>
</html>'''


def extract_data_highlights(content: str, title: str) -> list:
    """从文章内容提取关键数据点，用于数据高亮卡片。

    查找模式：
    - "17个" -> number: 17, label: "..."
    - "Sharpe最高的1.03" -> number: 1.03, label: "Sharpe最高"
    - 含粗体数字的行
    """
    highlights = []
    number_patterns = [
        r'(\d+\.?\d*)\s*(个|次|天|%|倍)',
        r'[Ss]harpe[^0-9]*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*%',
    ]

    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('```'):
            continue
        bold_nums = re.findall(r'\*\*(\d+\.?\d*)\*\*', line)
        if bold_nums:
            label = re.sub(r'\*\*', '', line)[:60]
            highlights.append({'number': html_escape(bold_nums[0]), 'label': html_escape(label)})
            if len(highlights) >= 4:
                break
        for pat in number_patterns:
            match = re.search(pat, line)
            if match and len(highlights) < 4:
                label = line[:50].strip()
                highlights.append({'number': html_escape(match.group(1)), 'label': html_escape(label)})
                break

    if not highlights:
        highlights = [
            {'number': html_escape('0'), 'label': html_escape('Strategies Passed')},
            {'number': html_escape('17'), 'label': html_escape('Strategies Tested')},
        ]

    return highlights


def compose_landing_html(article_id: str, title: str, content: str,
                          cover_path: str = '', video_path: str = '',
                          figures: list = None, output_path: str = '',
                          summary: str = '', cta_hero_text: str = '',
                          cta_final_title: str = '', cta_final_text: str = '',
                          cta_button_text: str = '',
                          footer_text: str = '') -> str:
    """生成着陆页HTML"""
    figures = figures or []

    if not summary:
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('```') and not line.startswith('<!--'):
                summary = line[:150]
                break
    if not summary:
        summary = title

    if not cta_hero_text:
        cta_hero_text = 'Read the Full Story'
    if not cta_final_title:
        cta_final_title = 'Want More Insights?'
    if not cta_final_text:
        cta_final_text = 'Subscribe to get our latest research and analysis delivered to your inbox.'
    if not cta_button_text:
        cta_button_text = 'Subscribe Now'
    if not footer_text:
        footer_text = '&copy; yiyan-yixing | Built with AI'

    # Hero背景
    hero_bg = image_to_base64_src(cover_path) if cover_path else ''

    # 视频区域
    video_section_html = ''
    if video_path and Path(video_path).exists():
        video_section_html = f'''
<!-- Video Section -->
<section class="video-section scroll-animate">
  <video controls preload="metadata" poster="{hero_bg}">
    <source src="{Path(video_path).name}" type="video/mp4">
    Your browser does not support video.
  </video>
  <p class="video-caption">{html_escape(title)} - Video Overview</p>
</section>
'''

    # 数据高亮
    data_highlights = extract_data_highlights(content, title)
    data_section_title = 'Key Numbers'
    data_cards_html = ''
    for i, dh in enumerate(data_highlights):
        delay_class = f'animate-delay-{i + 1}'
        data_cards_html += f'''
    <div class="data-card scroll-animate {delay_class}">
      <div class="number">{dh["number"]}</div>
      <div class="label">{dh["label"]}</div>
    </div>
'''

    # 正文HTML
    body_html = markdown_to_html(content)

    # 配图交错插入
    body_html = interleave_figures(body_html, figures, figure_class='figure-block')

    # 填充模板（所有用户输入做HTML转义防XSS）
    html = LANDING_HTML_TEMPLATE.format(
        title_esc=html_escape(title),
        title_attr_esc=html_escape_attr(title),
        summary_esc=html_escape(summary),
        summary_attr_esc=html_escape_attr(summary),
        font_stack=FONT_STACK,
        deep_blue=C['deep_blue'],
        navy=C['navy'],
        yellow=C['yellow'],
        white=C['white'],
        red=C['red'],
        positive=C['positive'],
        hero_bg=hero_bg,
        cta_hero_esc=html_escape(cta_hero_text),
        video_section=video_section_html,
        data_section_title_esc=html_escape(data_section_title),
        data_cards_html=data_cards_html,
        body_html=body_html,
        cta_final_title_esc=html_escape(cta_final_title),
        cta_final_text_esc=html_escape(cta_final_text),
        cta_button_esc=html_escape(cta_button_text),
        footer_esc=html_escape(footer_text),
    )

    # 写入文件
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f"Landing page saved: {out} ({out.stat().st_size} bytes)")
    return str(out)


def main():
    parser = argparse.ArgumentParser(description='Landing Page Composer')
    parser.add_argument('--article-id', required=True, help='Article ID')
    parser.add_argument('--title', required=True, help='Page title')
    parser.add_argument('--content', required=True, help='Article content (Markdown or text)')
    parser.add_argument('--cover', default=None, help='Cover image path')
    parser.add_argument('--video', default=None, help='Video file path (mp4)')
    parser.add_argument('--figures', nargs='*', default=[], help='Figure image paths')
    parser.add_argument('--summary', default='', help='Page summary/description')
    parser.add_argument('--cta-hero', default='', help='Hero CTA text')
    parser.add_argument('--cta-final-title', default='', help='Final CTA title')
    parser.add_argument('--cta-final-text', default='', help='Final CTA text')
    parser.add_argument('--cta-button', default='', help='CTA button text')
    parser.add_argument('--footer', default='', help='Footer text')
    parser.add_argument('--output', required=True, help='Output HTML file path')
    args = parser.parse_args()

    compose_landing_html(
        article_id=args.article_id,
        title=args.title,
        content=args.content,
        cover_path=args.cover or '',
        video_path=args.video or '',
        figures=args.figures,
        output_path=args.output,
        summary=args.summary,
        cta_hero_text=args.cta_hero,
        cta_final_title=args.cta_final_title,
        cta_final_text=args.cta_final_text,
        cta_button_text=args.cta_button,
        footer_text=args.footer,
    )


if __name__ == '__main__':
    main()
