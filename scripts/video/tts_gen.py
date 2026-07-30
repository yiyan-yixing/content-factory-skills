#!/usr/bin/env python3
"""TTS 配音生成器 — 用 edge-tts 将文本转为配音音频。

需要先安装: pip install edge-tts

用法:
  # 简单配音
  python3 tts_gen.py "配音文本" -o audio.mp3

  # 从文件读配音稿
  python3 tts_gen.py @script.txt -o audio.mp3 --voice zh-CN-XiaoxiaoNeural --rate +10%

  # 从分镜 JSON 提取配音稿并生成
  python3 tts_gen.py script.json -o audio.mp3 --extract
"""
import argparse
import json
import sys
import asyncio
from pathlib import Path


async def generate_tts(text: str, output_path: str,
                       voice: str = "zh-CN-XiaoxiaoNeural",
                       rate: str = "+10%",
                       pitch: str = "+5Hz"):
    """Generate TTS audio using edge-tts."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(str(output_path))
    size = Path(output_path).stat().st_size
    print(f"✅ TTS 已保存: {output_path} ({size / 1024:.0f} KB)")
    return size


def extract_text_from_json(script_path: str) -> str:
    """从视频分镜 JSON 中提取配音文本"""
    with open(script_path) as f:
        data = json.load(f)
    # 支持新版格式 {shots: [...]} 和旧版纯数组
    shots = data if isinstance(data, list) else data.get("shots", [])
    parts = []
    for shot in shots:
        subtitle = shot.get("subtitle", "").strip()
        visual = shot.get("visual", "").strip()
        # 用字幕作为配音文本
        if subtitle:
            parts.append(subtitle)
        elif visual and shot.get("type") in ("text-hook", "cta"):
            parts.append(visual)
    return "。".join(parts)


def main():
    parser = argparse.ArgumentParser(description="TTS 配音生成器")
    parser.add_argument("input", help="配音文本 / @文件路径 / 分镜 JSON 路径")
    parser.add_argument("-o", "--output", required=True, help="输出音频路径 (.mp3)")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural",
                        help="音色 (默认 zh-CN-XiaoxiaoNeural)")
    parser.add_argument("--rate", default="+10%",
                        help="语速 (默认 +10%)")
    parser.add_argument("--pitch", default="+5Hz",
                        help="音高 (默认 +5Hz)")
    parser.add_argument("--extract", action="store_true",
                        help="从分镜 JSON 提取配音文本")

    args = parser.parse_args()

    # 确定文本来源
    if args.extract:
        text = extract_text_from_json(args.input)
    elif args.input.startswith("@"):
        text = Path(args.input[1:]).read_text(encoding="utf-8").strip()
    elif Path(args.input).suffix in (".txt", ".md"):
        text = Path(args.input).read_text(encoding="utf-8").strip()
    else:
        text = args.input

    if not text:
        print("❌ 错误: 配音文本为空")
        sys.exit(1)

    print(f"🎤 TTS 生成中 (voice={args.voice}, rate={args.rate})...")
    print(f"   文本长度: {len(text)} 字")

    asyncio.run(generate_tts(text, args.output,
                             voice=args.voice, rate=args.rate, pitch=args.pitch))

    # 估算视频时长
    duration_est = len(text) / 3.5  # 约 3.5 字/秒 (180-220字/分钟)
    print(f"   估算配音时长: ~{duration_est:.0f} 秒")


if __name__ == "__main__":
    main()
