#!/usr/bin/env python3
"""
xhs_card_composer.py -- 小红书图文卡片组生成

将文章内容 + 配图列表 合成为3-6张3:4竖版卡片(1080x1440 PNG)。

5段叙事弧线（替代旧的机械拆分）：
  Cover  → 吸引停留（大字钩子+核心数字）
  Setup  → 建立共鸣（背景铺垫+为什么重要）
  Core   → 核心价值（数据图/关键发现/对比表）
  Payoff → 可执行收获（读者能拿走什么）
  Ending → 行动引导（关注+品牌+下一期预告）

3种大纲策略 (--strategy)：
  story  — Story-Driven (5-6张, 情感叙事, 适合失败/成长/教训)
  info   — Information-Dense (3-5张, 事实密度, 适合横评/数据/教程)
  visual — Visual-First (3-4张, 氛围为主, 适合概念/体验/展示)

6种Swipe Hook（卡片间视觉钩子）：
  arrow  — 右箭头"看下一个→"
  number — "2/4"页码
  question — "为什么？"悬念钩子
  reveal — "真相在第3页"
  teaser — "下页更关键"
  none   — 无hook（封面和CTA卡不用）

画布安全区：
  底部10%避让小红书标题栏
  右上角避让点赞按钮区域
  安全内容区：top 5% ~ bottom 85%, left 5% ~ right 90%

用法:
  python3 xhs_card_composer.py \
    --article-id T1-004 \
    --title "17个量化策略全失败" \
    --content "文章正文或关键数据点..." \
    --figures biz/content/assets/figures/T1-004/sharpe-comparison.png \
    --output-dir biz/content/assets/cards/T1-004/ \
    --card-count 5 \
    --strategy story
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 公共模块 -- 确保从任意目录运行时可找到本模块
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from composer_common import (
    BRAND_RGB, find_font, create_gradient_bg, create_xhs_gradient_bg,
    THREAD_ACCENT_MAP,
)

# 品牌色板（RGB，Pillow用）
BRAND = BRAND_RGB

# ============================================================
# 卡片尺寸与安全区
# ============================================================

CARD_WIDTH = 1080
CARD_HEIGHT = 1440

# 安全区参数（百分比，0.0-1.0）
SAFE_TOP_PCT = 0.05
SAFE_BOTTOM_PCT = 0.85
SAFE_LEFT_PCT = 0.05
SAFE_RIGHT_PCT = 0.90

# 像素级安全区
SAFE_LEFT = int(CARD_WIDTH * SAFE_LEFT_PCT)       # 54
SAFE_RIGHT = int(CARD_WIDTH * SAFE_RIGHT_PCT)     # 972
SAFE_TOP = int(CARD_HEIGHT * SAFE_TOP_PCT)        # 72
SAFE_BOTTOM = int(CARD_HEIGHT * SAFE_BOTTOM_PCT)  # 1224

# 安全区宽高
SAFE_WIDTH = SAFE_RIGHT - SAFE_LEFT    # 918
SAFE_HEIGHT = SAFE_BOTTOM - SAFE_TOP   # 1152

# 小红书底部标题栏避让区（底部10%）
XHS_BOTTOM_AVOID = int(CARD_HEIGHT * 0.90)  # 1296 -- 此线以下不画主要内容

# 小红书右上角点赞按钮避让区
XHS_LIKE_AVOID_LEFT = int(CARD_WIDTH * 0.82)   # 886
XHS_LIKE_AVOID_TOP = int(CARD_HEIGHT * 0.05)   # 72

# Swipe Hook 绘制区 -- 故意放在XHS避让区内：利用小红书标题栏旁的空间
HOOK_BG_Y = XHS_BOTTOM_AVOID + 20
HOOK_TEXT_Y = HOOK_BG_Y + 6

# 内容卡片最大要点数（防止溢出）
MAX_BULLETS = 5
# 内容卡片文字最大行数（防止溢出）
MAX_TEXT_LINES = 6

# ============================================================
# 叙事弧线段定义
# ============================================================

ARC_SEGMENTS = ['cover', 'setup', 'core', 'payoff', 'ending']

# 各段中文名与角色
ARC_LABELS = {
    'cover':  '封面',
    'setup':  '背景',
    'core':   '核心',
    'payoff': '收获',
    'ending': '行动',
}

# ============================================================
# 大纲策略 -- 定义各策略下弧线段的卡片分配
# ============================================================

STRATEGY_TEMPLATES = {
    'story': {
        'label': 'Story-Driven',
        'min_cards': 5,   # cover+setup+core(1)+payoff+ending = 5 minimum
        'max_cards': 6,
        # story: 完整5段弧线，core可扩展为多张
        'segments': [
            {'arc': 'cover',  'count': 1},
            {'arc': 'setup',  'count': 1},
            {'arc': 'core',   'count': 'flex'},  # 占据剩余卡片数 - 4(cover+setup+payoff+ending)
            {'arc': 'payoff', 'count': 1},
            {'arc': 'ending', 'count': 1},
        ],
    },
    'info': {
        'label': 'Information-Dense',
        'min_cards': 3,
        'max_cards': 5,
        # info: 跳过setup和payoff，core为主
        'segments': [
            {'arc': 'cover',  'count': 1},
            {'arc': 'core',   'count': 'flex'},  # 占据剩余卡片数 - 2(cover+ending)
            {'arc': 'ending', 'count': 1},
        ],
    },
    'visual': {
        'label': 'Visual-First',
        'min_cards': 3,
        'max_cards': 4,
        # visual: 最少卡片，氛围为主
        'segments': [
            {'arc': 'cover',  'count': 1},
            {'arc': 'core',   'count': 'flex'},  # 占据剩余卡片数 - 2(cover+ending)
            {'arc': 'ending', 'count': 1},
        ],
    },
}

# ============================================================
# Swipe Hook 策略
# ============================================================

HOOK_TYPES = ['arrow', 'number', 'question', 'reveal', 'teaser', 'none']

# 各弧线段默认的hook类型（封面和ending不用hook）
DEFAULT_HOOKS = {
    'cover':  'none',
    'setup':  'question',
    'core':   'number',
    'payoff': 'teaser',
    'ending': 'none',
}

# Hook 文案模板
HOOK_TEXT = {
    'arrow':   '看下一个  →',
    'number':  '{current}/{total}',
    'question': '为什么？',
    'reveal':  '真相在第{reveal_page}页',
    'teaser':  '下页更关键',
    'none':    '',
}


# ============================================================
# 绘制辅助函数
# ============================================================

def draw_centered_text(draw: ImageDraw.Draw, text: str, y: int, font: ImageFont.FreeTypeFont,
                        fill: tuple, width: int = CARD_WIDTH, max_width: int = None) -> int:
    """居中绘制文字，自动换行，返回文字下方的Y坐标。遵守安全区宽度约束。

    字符宽度估算系数0.55适用于中英混排近似，纯CJK偏窄纯ASCII偏宽。
    """
    mw = max_width or (SAFE_WIDTH)
    lines = []
    for line in text.split('\n'):
        wrapped = textwrap.wrap(line, width=int(mw / (font.size * 0.55)))
        if not wrapped:
            lines.append('')
        else:
            lines.extend(wrapped)

    line_height = int(font.size * 1.5)
    for line in lines:
        if line == '':
            y += line_height // 2
            continue
        # 确保不超出安全区底部
        if y + line_height > XHS_BOTTOM_AVOID:
            break
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (width - lw) // 2
        # 水平安全区约束
        x = max(SAFE_LEFT, min(x, SAFE_RIGHT - lw))
        draw.text((x, y), line, fill=fill, font=font)
        y += line_height
    return y


def draw_left_text(draw: ImageDraw.Draw, text: str, x: int, y: int,
                    font: ImageFont.FreeTypeFont, fill: tuple,
                    max_width: int = None, max_lines: int = None) -> int:
    """左对齐绘制文字，自动换行，返回文字下方的Y坐标。遵守安全区约束。

    字符宽度估算系数0.55适用于中英混排近似，纯CJK偏窄纯ASCII偏宽。
    """
    # 水平安全区约束
    x = max(x, SAFE_LEFT)
    mw = max_width or (SAFE_RIGHT - x - 20)
    lines = []
    for line in text.split('\n'):
        wrapped = textwrap.wrap(line, width=int(mw / (font.size * 0.55)))
        if not wrapped:
            lines.append('')
        else:
            lines.extend(wrapped)

    # 截断超出最大行数的文字（中英文句号均处理）
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines]
        if lines[-1]:
            lines[-1] = lines[-1].rstrip('.。') + '...'

    line_height = int(font.size * 1.5)
    for line in lines:
        if line == '':
            y += line_height // 2
            continue
        # 确保不超出安全区底部
        if y + line_height > XHS_BOTTOM_AVOID:
            break
        draw.text((x, y), line, fill=fill, font=font)
        y += line_height
    return y


# ============================================================
# 系列标识覆盖层（封面左上系列名+右上集数+底部进度条+线索色标）
# ============================================================

THREAD_COLOR_MAP = {
    'red': BRAND['red'],
    'blue': (42, 157, 143),    # positive/teal
    'yellow': BRAND['yellow'],
}


def _draw_series_overlay(draw: ImageDraw.Draw, series: str, episode: str,
                          thread_color: str, total_episodes: int,
                          current_episode: int) -> None:
    """在封面卡上绘制系列标识覆盖层。

    元素:
      - 左上角: 系列名（白色14pt）
      - 右上角: 集数（白色12pt）
      - 左下线索色标: 🔴/🔵/🟡 小圆点
      - 底部: 10格进度条（已发=亮色，未发=暗色40%透明）
    """
    # --- 左上角: 系列名 ---
    series_font = find_font(14)
    # 半透明背景条（用navy近似）
    bar_h = 28
    draw.rectangle([(0, 0), (SAFE_RIGHT, bar_h)], fill=BRAND['navy'])
    draw.text((SAFE_LEFT + 5, 5), series, fill=BRAND['white'], font=series_font)

    # --- 右上角: 集数 ---
    if episode:
        ep_font = find_font(12)
        ep_bbox = draw.textbbox((0, 0), episode, font=ep_font)
        ep_w = ep_bbox[2] - ep_bbox[0]
        draw.text((SAFE_RIGHT - ep_w - 10, 7), episode,
                  fill=BRAND['white'], font=ep_font)

    # --- 线索色标 ---
    if thread_color and thread_color in THREAD_COLOR_MAP:
        dot_color = THREAD_COLOR_MAP[thread_color]
        dot_r = 10
        dot_x = SAFE_LEFT + 5
        dot_y = XHS_BOTTOM_AVOID - 30
        draw.ellipse([(dot_x, dot_y), (dot_x + dot_r * 2, dot_y + dot_r * 2)],
                     fill=dot_color)

    # --- 进度条 ---
    if total_episodes > 0 and current_episode > 0:
        bar_y = XHS_BOTTOM_AVOID + 10
        bar_h = 8
        n_slots = min(total_episodes, 10)  # 最多10格
        slot_w = 40
        gap = 6
        total_bar_w = n_slots * slot_w + (n_slots - 1) * gap
        bar_x = (CARD_WIDTH - total_bar_w) // 2

        for i in range(n_slots):
            sx = bar_x + i * (slot_w + gap)
            if i < current_episode:
                # 已发: 亮色
                color = BRAND['yellow']
            else:
                # 未发: 暗色（用navy近似40%透明）
                color = BRAND['navy']
            draw.rectangle([(sx, bar_y), (sx + slot_w, bar_y + bar_h)],
                          fill=color, outline=BRAND['navy'])


# ============================================================
# Swipe Hook 绘制
# ============================================================

def draw_swipe_hook(draw: ImageDraw.Draw, hook_type: str,
                     card_index: int, total_cards: int,
                     reveal_page: int = 3) -> None:
    """在卡片底部避让区绘制Swipe Hook视觉钩子。

    Hook有意放置在小红书底部标题栏避让区(y > 90%)内，
    利用标题栏旁的视觉空间引导用户滑动。

    hook_type: arrow/number/question/reveal/teaser/none
    card_index: 当前卡片序号(0-based)
    total_cards: 总卡片数
    reveal_page: reveal hook 指向的页码
    """
    if hook_type == 'none':
        return

    hook_font = find_font(22)
    hook_color = BRAND['yellow']

    # 准备hook文案
    if hook_type == 'number':
        text = HOOK_TEXT['number'].format(
            current=card_index + 1, total=total_cards
        )
    elif hook_type == 'reveal':
        text = HOOK_TEXT['reveal'].format(reveal_page=reveal_page)
    else:
        text = HOOK_TEXT.get(hook_type, '')

    if not text:
        return

    # 绘制hook背景条（半透明效果用纯色近似）
    bg_h = 36
    draw.rectangle(
        [(SAFE_LEFT, HOOK_BG_Y), (SAFE_RIGHT, HOOK_BG_Y + bg_h)],
        fill=BRAND['navy']
    )

    # 绘制hook文字（右对齐，留出左侧内容空间）
    bbox = draw.textbbox((0, 0), text, font=hook_font)
    tw = bbox[2] - bbox[0]
    tx = SAFE_RIGHT - tw - 10
    draw.text((tx, HOOK_TEXT_Y), text, fill=hook_color, font=hook_font)

    # arrow hook 额外绘制箭头指示符
    if hook_type == 'arrow':
        arrow_x = SAFE_RIGHT - 20
        arrow_y = HOOK_TEXT_Y + 8
        draw.polygon(
            [(arrow_x, arrow_y - 6), (arrow_x + 10, arrow_y), (arrow_x, arrow_y + 6)],
            fill=hook_color
        )

    # question hook 额外绘制问号装饰
    if hook_type == 'question':
        q_font = find_font(28)
        qx = SAFE_LEFT + 20
        draw.text((qx, HOOK_TEXT_Y - 4), '?', fill=BRAND['red'], font=q_font)


# ============================================================
# 弧线段卡片绘制函数
# ============================================================

def compose_cover_card(headline: str, subtitle: str,
                        core_number: str = '',
                        series: str = '', episode: str = '',
                        thread_color: str = '',
                        total_episodes: int = 0,
                        current_episode: int = 0) -> Image.Image:
    """Cover: 吸引停留（大字钩子+核心数字） — XHS 亮色版"""
    img = create_xhs_gradient_bg(CARD_WIDTH, CARD_HEIGHT, thread_color=thread_color)
    draw = ImageDraw.Draw(img)

    accent = THREAD_ACCENT_MAP.get(thread_color, BRAND['yellow'])

    # --- 系列标识覆盖层 ---
    if series:
        _draw_series_overlay(draw, series, episode, thread_color,
                            total_episodes, current_episode)

    # 顶部线索色粗线
    y_top = SAFE_TOP + 30 if series else SAFE_TOP + 10
    draw.line([(SAFE_LEFT, y_top), (SAFE_RIGHT, y_top)],
              fill=accent, width=4)

    # 核心数字超大突出（比旧版大50%）
    y = y_top + 60
    if core_number:
        num_font = find_font(140)  # 旧版96 → 140
        y = draw_centered_text(draw, core_number, y, num_font, BRAND['red'])
        y += 10

    # 大字钩子 (主标题) — 加大字号
    title_font = find_font(88)  # 旧版72 → 88
    y = max(y, SAFE_TOP + 160)
    # 用线索色画主标题
    y = draw_centered_text(draw, headline, y, title_font, accent)

    # 分割线 — 粗且有色
    y += 25
    cx = CARD_WIDTH // 2
    draw.line([(cx - 80, y), (cx + 80, y)], fill=BRAND['red'], width=4)
    y += 25

    # 副标题 — 加大
    sub_font = find_font(36)  # 旧版32 → 36
    if subtitle:
        y = draw_centered_text(draw, subtitle, y, sub_font, BRAND['white'])

    # 底部品牌 — 用亮色而不是白色小字
    brand_font = find_font(24)  # 旧版20 → 24
    draw_centered_text(draw, '一言一行 · yiyan-yixing', XHS_BOTTOM_AVOID + 35,
                       brand_font, accent, CARD_WIDTH)

    # 底部品牌粗线
    draw.line([(SAFE_LEFT, XHS_BOTTOM_AVOID + 70), (SAFE_RIGHT, XHS_BOTTOM_AVOID + 70)],
              fill=accent, width=3)

    return img


def compose_setup_card(title: str, text: str, highlight: str = '',
                       thread_color: str = '') -> Image.Image:
    """Setup: 建立共鸣（背景铺垫+为什么重要）— XHS 亮色版"""
    img = create_xhs_gradient_bg(CARD_WIDTH, CARD_HEIGHT, thread_color=thread_color)
    draw = ImageDraw.Draw(img)

    accent = THREAD_ACCENT_MAP.get(thread_color, BRAND['yellow'])

    # 顶部线索色粗条
    draw.rectangle([(0, 0), (CARD_WIDTH, 8)], fill=accent)

    # 弧线段标签 — 用亮色背景块
    arc_font = find_font(20)
    draw.rounded_rectangle([(SAFE_LEFT, SAFE_TOP), (SAFE_LEFT + 100, SAFE_TOP + 36)],
                             radius=8, fill=accent)
    draw.text((SAFE_LEFT + 12, SAFE_TOP + 6), ARC_LABELS['setup'],
              fill=BRAND['deep_blue'], font=arc_font)

    # 标题 — 加大
    y = SAFE_TOP + 56
    title_font = find_font(52)  # 旧版44 → 52
    y = draw_centered_text(draw, title, y, title_font, accent)

    # 分割线 — 粗
    y += 18
    draw.line([(SAFE_LEFT + 30, y), (SAFE_RIGHT - 30, y)],
              fill=BRAND['red'], width=3)
    y += 22

    # 背景铺垫文字 — 加大
    text_font = find_font(32)  # 旧版28 → 32
    y = draw_left_text(draw, text, SAFE_LEFT + 20, y, text_font, BRAND['white'],
                       max_width=SAFE_WIDTH - 40, max_lines=MAX_TEXT_LINES + 2)

    # "为什么重要"高亮 — 用线索色边框色块
    if highlight:
        y += 25
        if y + 80 < XHS_BOTTOM_AVOID:
            draw.rounded_rectangle(
                [(SAFE_LEFT + 10, y - 10), (SAFE_RIGHT - 10, y + 65)],
                radius=12, fill=BRAND['navy_mid'], outline=accent, width=3
            )
            hl_font = find_font(34)  # 旧版30 → 34
            y = draw_centered_text(draw, highlight, y + 5, hl_font, BRAND['red'])

    # 底部品牌
    brand_font = find_font(20)
    draw_centered_text(draw, '一言一行', XHS_BOTTOM_AVOID + 40, brand_font,
                       accent, CARD_WIDTH)

    return img


def compose_core_figure_card(text: str, figure_path: str = '',
                              caption: str = '',
                              thread_color: str = '') -> Image.Image:
    """Core: 核心价值（数据图+关键发现）— XHS 亮色版"""
    img = create_xhs_gradient_bg(CARD_WIDTH, CARD_HEIGHT, thread_color=thread_color)
    draw = ImageDraw.Draw(img)

    accent = THREAD_ACCENT_MAP.get(thread_color, BRAND['red'])

    # 顶部红色粗条（核心段专属）
    draw.rectangle([(0, 0), (CARD_WIDTH, 8)], fill=BRAND['red'])

    # 弧线段标签 — 红色背景块
    arc_font = find_font(20)
    draw.rounded_rectangle([(SAFE_LEFT, SAFE_TOP), (SAFE_LEFT + 80, SAFE_TOP + 36)],
                             radius=8, fill=BRAND['red'])
    draw.text((SAFE_LEFT + 12, SAFE_TOP + 6), ARC_LABELS['core'],
              fill=BRAND['white'], font=arc_font)

    if figure_path and Path(figure_path).exists():
        y = SAFE_TOP + 50
        text_font = find_font(30)  # 旧版28 → 30
        y = draw_left_text(draw, text, SAFE_LEFT + 20, y, text_font, BRAND['white'],
                           max_width=SAFE_WIDTH - 40, max_lines=MAX_TEXT_LINES)

        # 数据图嵌入 — 加大图框，用线索色边框
        figure_y = max(y + 30, SAFE_TOP + 180)
        max_h = max(100, XHS_BOTTOM_AVOID - figure_y - 80)

        try:
            fig_img = Image.open(figure_path)
            try:
                max_w = SAFE_WIDTH - 40
                fig_img.thumbnail((max_w, max_h), Image.LANCZOS)
                fx = (CARD_WIDTH - fig_img.width) // 2
                fx = max(SAFE_LEFT + 10, min(fx, SAFE_RIGHT - fig_img.width - 10))
                fy = figure_y + 10

                # 图片框：线索色粗边框
                frame_margin = 10
                draw.rounded_rectangle(
                    [(fx - frame_margin, fy - frame_margin),
                     (fx + fig_img.width + frame_margin, fy + fig_img.height + frame_margin)],
                    radius=12, fill=BRAND['navy_mid'], outline=accent, width=3
                )
                img.paste(fig_img, (fx, fy))

                if caption:
                    cap_font = find_font(22)
                    cap_y = fy + fig_img.height + 14
                    if cap_y + 30 < XHS_BOTTOM_AVOID:
                        draw_centered_text(draw, caption, cap_y, cap_font, accent)
            finally:
                fig_img.close()
        except Exception as e:
            print(f"Warning: figure embedding failed: {e}")
            _draw_core_fallback(draw, text)
    else:
        _draw_core_fallback(draw, text)

    # 底部品牌
    brand_font = find_font(20)
    draw_centered_text(draw, '一言一行', XHS_BOTTOM_AVOID + 40, brand_font,
                       accent, CARD_WIDTH)

    return img


def _draw_core_fallback(draw: ImageDraw.Draw, text: str) -> None:
    """Core卡片无配图时的降级绘制：居中大字+装饰线"""
    y = SAFE_TOP + 100
    y = draw_centered_text(draw, text, y, find_font(36), BRAND['white'])
    draw.line([(SAFE_LEFT + 30, XHS_BOTTOM_AVOID - 40),
               (SAFE_RIGHT - 30, XHS_BOTTOM_AVOID - 40)],
              fill=BRAND['yellow'], width=2)


def compose_core_text_card(title: str, bullets: list, highlight: str = '',
                            thread_color: str = '') -> Image.Image:
    """Core: 核心价值（纯文字要点列表）— XHS 亮色版"""
    img = create_xhs_gradient_bg(CARD_WIDTH, CARD_HEIGHT, thread_color=thread_color)
    draw = ImageDraw.Draw(img)

    accent = THREAD_ACCENT_MAP.get(thread_color, BRAND['red'])

    # 顶部红色粗条
    draw.rectangle([(0, 0), (CARD_WIDTH, 8)], fill=BRAND['red'])

    # 弧线段标签 — 红色背景块
    arc_font = find_font(20)
    draw.rounded_rectangle([(SAFE_LEFT, SAFE_TOP), (SAFE_LEFT + 80, SAFE_TOP + 36)],
                             radius=8, fill=BRAND['red'])
    draw.text((SAFE_LEFT + 12, SAFE_TOP + 6), ARC_LABELS['core'],
              fill=BRAND['white'], font=arc_font)

    # 标题 — 加大
    y = SAFE_TOP + 50
    title_font = find_font(46)  # 旧版40 → 46
    y = draw_centered_text(draw, title, y, title_font, accent)

    # 分割线 — 粗
    y += 14
    draw.line([(SAFE_LEFT + 30, y), (SAFE_RIGHT - 30, y)],
              fill=BRAND['red'], width=3)
    y += 22

    # 要点列表 — 加大字号，用线索色数字
    bullet_font = find_font(32)  # 旧版28 → 32
    num_font = find_font(44)     # 旧版36 → 44
    display_bullets = bullets[:MAX_BULLETS]
    if len(bullets) > MAX_BULLETS:
        display_bullets[-1] = display_bullets[-1].rstrip('.。') + '...'

    for i, bullet in enumerate(display_bullets):
        if y > XHS_BOTTOM_AVOID - 180:
            break
        draw.text((SAFE_LEFT + 20, y), str(i + 1), fill=accent, font=num_font)
        y = draw_left_text(draw, bullet, SAFE_LEFT + 90, y + 8, bullet_font, BRAND['white'],
                           max_width=SAFE_WIDTH - 110)
        y += 16

    # 高亮结论 — 用线索色边框色块
    if highlight and y + 80 < XHS_BOTTOM_AVOID - 20:
        y += 20
        draw.rounded_rectangle(
            [(SAFE_LEFT + 10, y - 10), (SAFE_RIGHT - 10, y + 65)],
            radius=12, fill=BRAND['navy_mid'], outline=accent, width=3
        )
        hl_font = find_font(34)
        y = draw_centered_text(draw, highlight, y + 5, hl_font, BRAND['red'])

    # 底部品牌
    brand_font = find_font(20)
    draw_centered_text(draw, '一言一行', XHS_BOTTOM_AVOID + 40, brand_font,
                       accent, CARD_WIDTH)

    return img


def compose_payoff_card(title: str, text: str, bullets: list = None,
                         highlight: str = '',
                         thread_color: str = '') -> Image.Image:
    """Payoff: 可执行收获（读者能拿走什么）— XHS 亮色版"""
    img = create_xhs_gradient_bg(CARD_WIDTH, CARD_HEIGHT, thread_color=thread_color)
    draw = ImageDraw.Draw(img)

    accent = THREAD_ACCENT_MAP.get(thread_color, BRAND['positive'])

    # 顶部绿/青色粗条（收获段专属）
    draw.rectangle([(0, 0), (CARD_WIDTH, 8)], fill=BRAND['positive'])

    # 弧线段标签 — 绿色背景块
    arc_font = find_font(20)
    draw.rounded_rectangle([(SAFE_LEFT, SAFE_TOP), (SAFE_LEFT + 80, SAFE_TOP + 36)],
                             radius=8, fill=BRAND['positive'])
    draw.text((SAFE_LEFT + 12, SAFE_TOP + 6), ARC_LABELS['payoff'],
              fill=BRAND['white'], font=arc_font)

    # 标题 — 加大，用绿色
    y = SAFE_TOP + 56
    title_font = find_font(50)  # 旧版44 → 50
    y = draw_centered_text(draw, title, y, title_font, BRAND['positive'])

    # 分割线 — 黄色粗线
    y += 18
    draw.line([(SAFE_LEFT + 30, y), (SAFE_RIGHT - 30, y)],
              fill=accent, width=3)
    y += 22

    # 收获要点 — 加大，用大对勾
    if bullets:
        bullet_font = find_font(32)  # 旧版28 → 32
        check_font = find_font(40)   # 旧版32 → 40
        display_bullets = bullets[:MAX_BULLETS]
        for bullet in display_bullets:
            if y > XHS_BOTTOM_AVOID - 160:
                break
            draw.text((SAFE_LEFT + 20, y), '✓', fill=BRAND['positive'], font=check_font)
            y = draw_left_text(draw, bullet, SAFE_LEFT + 80, y + 6, bullet_font, BRAND['white'],
                               max_width=SAFE_WIDTH - 100)
            y += 14
    elif text:
        text_font = find_font(34)
        y = draw_left_text(draw, text, SAFE_LEFT + 20, y, text_font, BRAND['white'],
                           max_width=SAFE_WIDTH - 40, max_lines=MAX_TEXT_LINES)

    # 底部高亮框 — 用黄色边框（更醒目）
    if highlight and y + 80 < XHS_BOTTOM_AVOID - 20:
        y += 20
        draw.rounded_rectangle(
            [(SAFE_LEFT + 10, y - 10), (SAFE_RIGHT - 10, y + 65)],
            radius=12, fill=BRAND['navy_mid'], outline=accent, width=3
        )
        hl_font = find_font(34)
        y = draw_centered_text(draw, highlight, y + 5, hl_font, accent)

    # 底部品牌
    brand_font = find_font(20)
    draw_centered_text(draw, '一言一行', XHS_BOTTOM_AVOID + 40, brand_font,
                       accent, CARD_WIDTH)

    return img


def compose_ending_card(brand_name: str = 'yiyan-yixing',
                         cta_text: str = 'Follow for more insights',
                         next_teaser: str = '',
                         thread_color: str = '') -> Image.Image:
    """Ending: 行动引导（关注+品牌+下一期预告）— XHS 亮色版"""
    # Ending 用反转渐变：顶部深蓝，底部更深的纯黑
    img = create_xhs_gradient_bg(CARD_WIDTH, CARD_HEIGHT, thread_color=thread_color)
    draw = ImageDraw.Draw(img)

    accent = THREAD_ACCENT_MAP.get(thread_color, BRAND['yellow'])

    # 顶部红色粗条
    draw.rectangle([(0, 0), (CARD_WIDTH, 8)], fill=BRAND['red'])

    # 弧线段标签
    arc_font = find_font(20)
    draw.rounded_rectangle([(SAFE_LEFT, SAFE_TOP), (SAFE_LEFT + 80, SAFE_TOP + 36)],
                             radius=8, fill=accent)
    draw.text((SAFE_LEFT + 12, SAFE_TOP + 6), ARC_LABELS['ending'],
              fill=BRAND['deep_blue'], font=arc_font)

    # 大字CTA — 用线索色，更大
    y = SAFE_TOP + 150
    cta_font = find_font(56)  # 旧版48 → 56
    y = draw_centered_text(draw, cta_text, y, cta_font, accent)

    # 分割
    y += 40
    draw.line([(CARD_WIDTH // 2 - 60, y), (CARD_WIDTH // 2 + 60, y)],
              fill=accent, width=3)
    y += 50

    # 二维码占位 — 用线索色边框
    qr_size = 240  # 旧版220 → 240
    qr_x = (CARD_WIDTH - qr_size) // 2
    qr_x = max(SAFE_LEFT + 10, min(qr_x, SAFE_RIGHT - qr_size - 10))
    draw.rounded_rectangle([(qr_x, y), (qr_x + qr_size, y + qr_size)],
                            radius=12, fill=BRAND['white'], outline=accent, width=4)
    qr_label_font = find_font(24)  # 旧版22 → 24
    draw_centered_text(draw, '扫码关注', y + qr_size // 2 - 14, qr_label_font,
                       BRAND['deep_blue'], CARD_WIDTH)

    y += qr_size + 40

    # 品牌名 — 加大
    brand_font_large = find_font(42)  # 旧版36 → 42
    y = draw_centered_text(draw, '一言一行', y, brand_font_large, BRAND['white'], CARD_WIDTH)

    # 下一期预告 — 用线索色背景条
    if next_teaser:
        y += 30
        teaser_font = find_font(28)
        if y + 50 < XHS_BOTTOM_AVOID:
            draw.rounded_rectangle(
                [(SAFE_LEFT + 20, y - 10), (SAFE_RIGHT - 20, y + 42)],
                radius=10, fill=BRAND['navy_mid'], outline=accent, width=2
            )
            draw_centered_text(draw, f'→ {next_teaser}', y, teaser_font,
                               accent)

    # 底部装饰线
    draw.line([(SAFE_LEFT, XHS_BOTTOM_AVOID + 70), (SAFE_RIGHT, XHS_BOTTOM_AVOID + 70)],
              fill=accent, width=3)

    return img


# ============================================================
# 内容拆分逻辑（策略感知 + 叙事弧线）
# ============================================================

def extract_core_number(title: str, content: str) -> str:
    """从标题/内容中提取核心数字，用于封面突出显示"""
    nums = re.findall(r'(\d+)', title)
    if nums:
        return nums[0]
    return ''


def split_content_by_strategy(content: str, card_count: int,
                               figures: list, strategy: str) -> list:
    """根据策略将内容拆分为弧线段卡片数据结构。

    返回列表，每项为dict，包含:
      type: cover/setup/core_figure/core_text/payoff/ending
      arc: cover/setup/core/payoff/ending
      hook_type: arrow/number/question/reveal/teaser/none
      以及各段对应的标题/文字/要点/配图等字段
    """
    template = STRATEGY_TEMPLATES.get(strategy, STRATEGY_TEMPLATES['story'])

    # 约束卡片数在策略范围内
    card_count = max(template['min_cards'], min(template['max_cards'], card_count))

    cards = []
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]

    # 计算flex段（core）的卡片数
    fixed_count = sum(1 for seg in template['segments'] if seg['count'] != 'flex')
    flex_count = card_count - fixed_count

    # 按弧线段生成卡片
    figure_idx = 0
    para_idx = 0

    for seg in template['segments']:
        arc = seg['arc']
        seg_count = seg['count'] if seg['count'] != 'flex' else max(1, flex_count)

        if arc == 'cover':
            cards.append({
                'type': 'cover',
                'arc': 'cover',
                'hook_type': 'none',
                'headline': '',
                'subtitle': '',
                'core_number': '',
            })

        elif arc == 'setup':
            # Setup 取第一段内容
            setup_text = paragraphs[0] if paragraphs else ''
            setup_title = 'Why this matters'
            # 尝试从内容提取"为什么重要"
            setup_highlight = ''
            if len(paragraphs) > 1:
                setup_highlight = paragraphs[1][:80]
            cards.append({
                'type': 'setup',
                'arc': 'setup',
                'hook_type': DEFAULT_HOOKS['setup'],
                'title': setup_title,
                'text': setup_text,
                'highlight': setup_highlight,
            })
            para_idx = min(2, len(paragraphs))

        elif arc == 'core':
            # Core 占据多张卡片，分配段落和配图
            remaining_paras = paragraphs[para_idx:] if para_idx < len(paragraphs) else []
            # Core段从总段落中去掉setup占用的和最后留给payoff的
            payoff_reserve = 1 if 'payoff' in [s['arc'] for s in template['segments']] else 0
            core_paras = remaining_paras[:max(0, len(remaining_paras) - payoff_reserve)]

            for ci in range(seg_count):
                # 分配段落
                group_size = max(1, len(core_paras) // seg_count)
                start = ci * group_size
                end = start + group_size if ci < seg_count - 1 else len(core_paras)
                group_text = '\n'.join(core_paras[start:end])

                card_data = {
                    'arc': 'core',
                    'hook_type': DEFAULT_HOOKS['core'],
                    'highlight': '',
                    'caption': '',
                }

                # 分配配图
                if figure_idx < len(figures):
                    card_data['type'] = 'core_figure'
                    card_data['text'] = group_text
                    card_data['figure'] = figures[figure_idx]
                    card_data['caption'] = Path(figures[figure_idx]).stem.replace('-', ' ').replace('_', ' ')
                    figure_idx += 1
                else:
                    card_data['type'] = 'core_text'
                    card_data['title'] = f'Key Insight {ci + 1}'
                    card_data['bullets'] = group_text.split('\n')[:MAX_BULLETS]

                cards.append(card_data)

        elif arc == 'payoff':
            # Payoff 取最后一段内容
            payoff_text = paragraphs[-1] if len(paragraphs) > 1 else ''
            payoff_title = 'What you can take away'
            payoff_highlight = ''
            # 尝试提取关键收获
            if payoff_text:
                sentences = payoff_text.replace('。', '。\n').split('\n')
                payoff_highlight = sentences[-1].strip()[:80] if sentences else ''
            cards.append({
                'type': 'payoff',
                'arc': 'payoff',
                'hook_type': DEFAULT_HOOKS['payoff'],
                'title': payoff_title,
                'text': payoff_text,
                'bullets': payoff_text.split('\n')[:MAX_BULLETS] if payoff_text else [],
                'highlight': payoff_highlight,
            })

        elif arc == 'ending':
            cards.append({
                'type': 'ending',
                'arc': 'ending',
                'hook_type': 'none',
                'brand_name': 'yiyan-yixing',
                'cta_text': 'Follow for more insights',
                'next_teaser': '',
            })

    # 填充ending预告
    for card in cards:
        if card['type'] == 'ending':
            card['next_teaser'] = 'Next: more deep dives'

    return cards


# ============================================================
# 卡片组生成主函数
# ============================================================

def compose_card_group(article_id: str, title: str, content: str,
                        figures: list, output_dir: str,
                        card_count: int = 5, strategy: str = 'story',
                        series: str = '', episode: str = '',
                        thread_color: str = '',
                        total_episodes: int = 0,
                        current_episode: int = 0) -> list:
    """生成小红书卡片组，返回输出文件路径列表"""
    if not title or not content:
        print("Warning: empty title or content, generating blank cards")

    card_data_list = split_content_by_strategy(content, card_count, figures, strategy)
    total_cards = len(card_data_list)

    # 用实际标题覆盖封面卡数据
    if card_data_list and card_data_list[0]['type'] == 'cover':
        card_data_list[0]['headline'] = title
        first_line = content.split('\n')[0].strip() if content else ''
        card_data_list[0]['subtitle'] = first_line[:60] if first_line else ''
        card_data_list[0]['core_number'] = extract_core_number(title, content)
        # 系列信息传入封面卡
        card_data_list[0]['series'] = series
        card_data_list[0]['episode'] = episode
        card_data_list[0]['thread_color'] = thread_color
        card_data_list[0]['total_episodes'] = total_episodes
        card_data_list[0]['current_episode'] = current_episode

    # 将 thread_color 传入所有卡片（用于背景渐变）
    for cd in card_data_list:
        cd['thread_color'] = thread_color

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 计算reveal页码（用于reveal hook）
    reveal_page = 3  # 默认第3页
    for i, cd in enumerate(card_data_list):
        if cd['arc'] == 'core':
            reveal_page = i + 1
            break

    output_paths = []
    for i, card_data in enumerate(card_data_list):
        card_type = card_data['type']

        if card_type == 'cover':
            img = compose_cover_card(
                headline=card_data.get('headline', title),
                subtitle=card_data.get('subtitle', ''),
                core_number=card_data.get('core_number', ''),
                series=card_data.get('series', ''),
                episode=card_data.get('episode', ''),
                thread_color=card_data.get('thread_color', ''),
                total_episodes=card_data.get('total_episodes', 0),
                current_episode=card_data.get('current_episode', 0),
            )
        elif card_type == 'setup':
            img = compose_setup_card(
                title=card_data.get('title', 'Why this matters'),
                text=card_data.get('text', ''),
                highlight=card_data.get('highlight', ''),
                thread_color=card_data.get('thread_color', ''),
            )
        elif card_type == 'core_figure':
            img = compose_core_figure_card(
                text=card_data.get('text', ''),
                figure_path=card_data.get('figure', ''),
                caption=card_data.get('caption', ''),
                thread_color=card_data.get('thread_color', ''),
            )
        elif card_type == 'core_text':
            img = compose_core_text_card(
                title=card_data.get('title', f'Card {i + 1}'),
                bullets=card_data.get('bullets', []),
                highlight=card_data.get('highlight', ''),
                thread_color=card_data.get('thread_color', ''),
            )
        elif card_type == 'payoff':
            img = compose_payoff_card(
                title=card_data.get('title', 'What you can take away'),
                text=card_data.get('text', ''),
                bullets=card_data.get('bullets'),
                highlight=card_data.get('highlight', ''),
                thread_color=card_data.get('thread_color', ''),
            )
        elif card_type == 'ending':
            img = compose_ending_card(
                brand_name=card_data.get('brand_name', 'yiyan-yixing'),
                cta_text=card_data.get('cta_text', 'Follow for more'),
                next_teaser=card_data.get('next_teaser', ''),
                thread_color=card_data.get('thread_color', ''),
            )
        else:
            continue

        # 绘制Swipe Hook
        draw = ImageDraw.Draw(img)
        hook_type = card_data.get('hook_type', 'none')
        draw_swipe_hook(draw, hook_type, i, total_cards, reveal_page=reveal_page)

        card_path = out / f'{article_id}-card-{i + 1:02d}.png'
        img.save(str(card_path), 'PNG', optimize=True)
        output_paths.append(str(card_path))
        arc_label = ARC_LABELS.get(card_data.get('arc', ''), '')
        hook_label = f'hook={hook_type}' if hook_type != 'none' else ''
        print(f"Card {i + 1}/{total_cards} [{card_type}|{arc_label}] {hook_label} -> {card_path}")

    return output_paths


# ============================================================
# CLI 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='XHS Card Composer - Xiaohongshu card group generator (narrative arc edition)'
    )
    parser.add_argument('--article-id', required=True, help='Article ID, e.g. T1-004')
    parser.add_argument('--title', required=True, help='Main title / hook text')
    parser.add_argument('--content', required=True, help='Article content text')
    parser.add_argument('--figures', nargs='*', default=[], help='Figure image paths')
    parser.add_argument('--output-dir', required=True, help='Output directory for cards')
    parser.add_argument('--card-count', type=int, default=5, help='Number of cards (3-6)')
    parser.add_argument('--strategy', choices=['story', 'info', 'visual'],
                        default='story',
                        help='Outline strategy: story(5-6, narrative), info(3-5, data-dense), visual(3-4, visual-first)')
    # 系列标识参数
    parser.add_argument('--series', default='', help='Series name, e.g. "一人AI实战记"')
    parser.add_argument('--episode', default='', help='Episode label, e.g. "D1/10"')
    parser.add_argument('--thread-color', default='', choices=['red', 'blue', 'yellow', ''],
                        help='Thread color indicator: red(quant), blue(AI infra), yellow(tools)')
    parser.add_argument('--total-episodes', type=int, default=0, help='Total episodes in series (for progress bar)')
    parser.add_argument('--current-episode', type=int, default=0, help='Current episode number (for progress bar)')
    args = parser.parse_args()

    card_count = max(3, min(6, args.card_count))

    template = STRATEGY_TEMPLATES[args.strategy]
    if card_count < template['min_cards']:
        card_count = template['min_cards']
        print(f"Note: strategy '{args.strategy}' requires min {template['min_cards']} cards, adjusted to {card_count}")
    if card_count > template['max_cards']:
        card_count = template['max_cards']
        print(f"Note: strategy '{args.strategy}' supports max {template['max_cards']} cards, adjusted to {card_count}")

    print(f"Strategy: {template['label']} | Cards: {card_count} | Arc: {' > '.join(ARC_LABELS[s['arc']] for s in template['segments'])}")

    paths = compose_card_group(
        article_id=args.article_id,
        title=args.title,
        content=args.content,
        figures=args.figures,
        output_dir=args.output_dir,
        card_count=card_count,
        strategy=args.strategy,
        series=args.series,
        episode=args.episode,
        thread_color=args.thread_color,
        total_episodes=args.total_episodes,
        current_episode=args.current_episode,
    )

    print(f"\nGenerated {len(paths)} cards ({template['label']} strategy):")
    for p in paths:
        print(f"  {p}")


if __name__ == '__main__':
    main()
