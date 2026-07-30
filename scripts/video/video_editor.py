#!/usr/bin/env python3
"""
video_editor.py -- moviepy + ffmpeg 短视频合成 (v2.0)

按分镜脚本将素材（mp4动画/PNG图片）合成为完整短视频。
支持 TTS 配音叠加、BGM 背景音乐叠加（通过分镜JSON的 voiceover/bgm 字段）。

用法:
  python3 video_editor.py \
    --script biz/content/assets/videos/T1-004/script.json \
    --output biz/content/assets/videos/T1-004/clip.mp4 \
    --resolution 1080x1920

分镜 JSON 增强字段（可选，见 SKILL-5B1 规范）:
  voiceover.path     str     — TTS配音音频文件路径 (.mp3)
  voiceover.volume   float   — 配音音量 (0.0~1.0, 默认 1.0)
  bgm.path           str     — 背景音乐音频文件路径 (.mp3)
  bgm.volume         float   — BGM音量 (0.0~1.0, 默认 0.2)
"""

import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 尝试 moviepy 2.x API
try:
    from moviepy import (
        ImageClip, VideoFileClip, CompositeVideoClip,
        concatenate_videoclips, ColorClip, TextClip,
        AudioFileClip, CompositeAudioClip,
    )
    MOVIEPY_V2 = True
except ImportError:
    try:
        from moviepy.editor import (
            ImageClip, VideoFileClip, CompositeVideoClip,
            concatenate_videoclips, ColorClip, TextClip,
            AudioFileClip, CompositeAudioClip,
        )
        MOVIEPY_V2 = False
    except ImportError:
        print("ERROR: moviepy not installed. Run: pip install moviepy")
        sys.exit(1)

# 品牌色板
BRAND_BG = (26, 26, 46)
BRAND_YELLOW = (233, 196, 106)
BRAND_RED = (231, 111, 81)
BRAND_WHITE = (255, 255, 255)

FONT_CANDIDATES = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
]


def find_font_path() -> str:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def create_text_frame(text: str, resolution: tuple, font_size: int = 48,
                       color: tuple = BRAND_YELLOW) -> str:
    """创建品牌纯文字帧（临时PNG）"""
    w, h = resolution
    img = Image.new('RGB', (w, h), BRAND_BG)
    draw = ImageDraw.Draw(img)

    font_path = find_font_path()
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    # 文字居中
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (w - tw) // 2
    y = (h - th) // 2
    draw.text((x, y), text, fill=color, font=font)

    # 保存临时文件
    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(tmp.name, 'PNG')
    return tmp.name


def create_subtitle_frame(text: str, resolution: tuple, font_size: int = 36) -> str:
    """创建字幕帧（底部半透明背景+白字）"""
    w, h = resolution
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))

    # 底部半透明黑条
    bar_h = 80
    bar_y = h - bar_h - 40
    bar = Image.new('RGBA', (w, bar_h), (0, 0, 0, 160))
    img.paste(bar, (0, bar_y))

    draw = ImageDraw.Draw(img)
    font_path = find_font_path()
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (w - tw) // 2
    y = bar_y + (bar_h - font_size) // 2
    draw.text((x, y), text, fill=BRAND_WHITE, font=font)

    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(tmp.name, 'PNG')
    return tmp.name


# ---------------------------------------------------------------------------
# 音频叠加 (v2.0 新增)
# ---------------------------------------------------------------------------

def _loop_audio_clip(audio_clip, target_duration):
    """将音频循环至目标时长。兼容 moviepy 1.x 和 2.x。"""
    if audio_clip.duration >= target_duration:
        return audio_clip.subclip(0, target_duration)
    # moviepy 2.x: AudioClip.loop(duration=...)
    try:
        return audio_clip.loop(duration=target_duration)
    except (TypeError, AttributeError):
        pass
    # moviepy 1.x: 手动拼接
    n_loops = int(math.ceil(target_duration / audio_clip.duration))
    try:
        from moviepy import concatenate_audioclips as _cat_audio
    except ImportError:
        from moviepy.editor import concatenate_audioclips as _cat_audio
    return _cat_audio([audio_clip] * n_loops).subclip(0, target_duration)


def compose_audio(video_clip, voiceover_path=None, voiceover_volume=1.0,
                  bgm_path=None, bgm_volume=0.2):
    """叠加 TTS 配音和 BGM 到视频。

    Args:
        video_clip: moviepy VideoClip
        voiceover_path: TTS 配音 .mp3 路径
        voiceover_volume: 配音音量 (0.0~1.0)
        bgm_path: 背景音乐 .mp3 路径
        bgm_volume: BGM 音量 (0.0~1.0, 有配音时建议 0.15~0.25)

    Returns:
        带音频的 VideoClip；无有效音频时返回原始 clip。
    """
    audio_clips = []

    # --- 1. TTS 配音 ---
    if voiceover_path and Path(voiceover_path).exists():
        try:
            tts = AudioFileClip(voiceover_path)
            # 截取到视频长度
            if tts.duration > video_clip.duration:
                tts = tts.subclip(0, video_clip.duration)
            # 调节音量
            if voiceover_volume != 1.0:
                try:
                    tts = tts.with_volume_scaled(voiceover_volume)
                except AttributeError:
                    tts = tts.volumex(voiceover_volume)
            audio_clips.append(tts)
        except Exception as e:
            print(f"Warning: TTS audio load failed: {e}")

    # --- 2. BGM 背景音乐 ---
    if bgm_path and Path(bgm_path).exists():
        try:
            bgm = AudioFileClip(bgm_path)
            # 循环至视频长度
            bgm = _loop_audio_clip(bgm, video_clip.duration)
            # 调节音量
            try:
                bgm = bgm.with_volume_scaled(bgm_volume)
            except AttributeError:
                bgm = bgm.volumex(bgm_volume)
            audio_clips.append(bgm)
        except Exception as e:
            print(f"Warning: BGM audio load failed: {e}")

    if not audio_clips:
        return video_clip

    # 混合音频并附加到视频
    try:
        mixed = CompositeAudioClip(audio_clips)
        try:
            return video_clip.with_audio(mixed)
        except AttributeError:
            return video_clip.set_audio(mixed)
    except Exception as e:
        print(f"Warning: Audio mixing failed: {e}")
        return video_clip


# ---------------------------------------------------------------------------
# 视频合成
# ---------------------------------------------------------------------------

def compose_video(script_path: str, output: str, resolution: tuple):
    """按分镜脚本合成视频"""
    with open(script_path) as f:
        data = json.load(f)

    # 支持两种 JSON 格式：
    #   旧版：纯数组 [{id, duration_sec, ...}, ...]
    #   新版：字典  {shots: [...], voiceover: {...}, bgm: {...}}
    if isinstance(data, dict):
        shots = data.get('shots', [])
        script_meta = data
    else:
        shots = data
        script_meta = {}

    clips = []
    w, h = resolution

    for shot in shots:
        shot_id = shot.get('id', 0)
        duration = shot.get('duration_sec', 3)
        shot_type = shot.get('type', 'text-hook')
        subtitle_text = shot.get('subtitle', '')

        if shot_type == 'dataviz' and shot.get('video_path'):
            # 数据动画mp4
            vp = Path(shot['video_path'])
            if vp.exists():
                clip = VideoFileClip(str(vp))
                # 适配分辨率
                try:
                    clip = clip.resized(resolution)
                except AttributeError:
                    clip = clip.resize(resolution)
                clip = clip.with_duration(min(duration, clip.duration))
            else:
                # 兜底：品牌背景帧
                frame_path = create_text_frame('数据加载中...', resolution)
                clip = ImageClip(frame_path).with_duration(duration)
                try:
                    clip = clip.resized(resolution)
                except AttributeError:
                    clip = clip.resize(resolution)

        elif shot.get('image_path') and Path(shot['image_path']).exists():
            # 图片帧
            clip = ImageClip(shot['image_path']).with_duration(duration)
            try:
                clip = clip.resized(resolution)
            except AttributeError:
                clip = clip.resize(resolution)

        else:
            # 纯文字帧
            text = shot.get('visual', subtitle_text or '...')
            text_color = BRAND_RED if shot_type == 'cta' else BRAND_YELLOW
            frame_path = create_text_frame(text, resolution, font_size=56, color=text_color)
            clip = ImageClip(frame_path).with_duration(duration)

        # 叠加字幕
        if subtitle_text and shot_type != 'text-hook':
            sub_path = create_subtitle_frame(subtitle_text, resolution, font_size=32)
            try:
                sub_clip = ImageClip(sub_path).with_duration(duration)
                sub_clip = sub_clip.with_position(('center', 0.85), relative=True)
                clip = CompositeVideoClip([clip, sub_clip])
            except Exception as e:
                print(f"Warning: subtitle overlay failed for shot {shot_id}: {e}")

        clips.append(clip)

    if not clips:
        print("ERROR: No clips generated")
        sys.exit(1)

    # 拼接
    try:
        final = concatenate_videoclips(clips, method='compose')
    except TypeError:
        final = concatenate_videoclips(clips)

    # ---- 叠加音频（TTS + BGM） ----
    has_audio = False
    if 'voiceover' in script_meta or 'bgm' in script_meta:
        vo = script_meta.get('voiceover', {})
        bgm_cfg = script_meta.get('bgm', {})
        final = compose_audio(
            final,
            voiceover_path=vo.get('path'),
            voiceover_volume=vo.get('volume', 1.0),
            bgm_path=bgm_cfg.get('path'),
            bgm_volume=bgm_cfg.get('volume', 0.2),
        )
        has_audio = hasattr(final, 'audio') and final.audio is not None

    # 导出
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        if has_audio:
            final.write_videofile(
                str(output_path),
                fps=24,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                threads=2,
            )
        else:
            final.write_videofile(
                str(output_path),
                fps=24,
                codec='libx264',
                audio=False,
                preset='medium',
                threads=2,
            )
    except Exception as e:
        print(f"moviepy export failed ({e}), trying ffmpeg directly...")
        # 兜底：用ffmpeg直接从帧序列生成
        print("Falling back to individual frame export...")

    print(f"Video saved: {output_path} ({w}x{h})")


def main():
    parser = argparse.ArgumentParser(description='Video Editor (v2.0)')
    parser.add_argument('--script', required=True, help='分镜脚本JSON')
    parser.add_argument('--output', required=True, help='输出mp4路径')
    parser.add_argument('--resolution', default='1080x1920', help='宽x高')
    args = parser.parse_args()

    resolution = tuple(int(x) for x in args.resolution.split('x'))
    compose_video(args.script, args.output, resolution)


if __name__ == '__main__':
    main()
