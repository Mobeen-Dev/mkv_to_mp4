#!/usr/bin/env python3
"""
inspect_mkv_profile.py

This script inspects an MKV file and prints detailed audio/video parameters.
It is meant to be used together with inspect_mp4_profile.py so you can:

1) Inspect a *working MP4* that plays on your LCD TV
2) Inspect a *problematic MKV*
3) Compare both outputs and convert MKV -> MP4 using matching parameters

Uses ffprobe (part of ffmpeg).

Usage:
  python inspect_mkv_profile.py sample.mkv

Requirements:
 - ffmpeg / ffprobe installed and available in PATH
"""

import json
import subprocess
import sys
from fractions import Fraction


def run_ffprobe(path: str) -> dict:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


def fps_from_ratio(r: str) -> str:
    try:
        return f"{float(Fraction(r)):.3f}"
    except Exception:
        return "unknown"


def main():
    if len(sys.argv) != 2:
        print("Usage: python inspect_mkv_profile.py sample.mkv")
        sys.exit(1)

    mkv_file = sys.argv[1]
    info = run_ffprobe(mkv_file)

    print("=" * 60)
    print("MKV MEDIA PROFILE (SOURCE FILE)")
    print("=" * 60)

    # Container info
    fmt = info.get("format", {})
    print("Container")
    print(f"  Format name       : {fmt.get('format_name')}")
    print(f"  Duration          : {fmt.get('duration')} sec")
    print(f"  Bitrate           : {fmt.get('bit_rate')} bps")

    # Streams
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video":
            print("\nVideo Stream")
            print(f"  Codec             : {stream.get('codec_name')}")
            print(f"  Codec long name   : {stream.get('codec_long_name')}")
            print(f"  Profile           : {stream.get('profile')}")
            print(f"  Level             : {stream.get('level')}")
            print(f"  Resolution        : {stream.get('width')}x{stream.get('height')}")
            print(f"  Frame rate        : {fps_from_ratio(stream.get('avg_frame_rate'))} fps")
            print(f"  Pixel format      : {stream.get('pix_fmt')}")
            print(f"  Bit depth         : {stream.get('bits_per_raw_sample')}")
            print(f"  Color space       : {stream.get('color_space')}")
            print(f"  Color primaries   : {stream.get('color_primaries')}")
            print(f"  Color transfer    : {stream.get('color_transfer')}")
            print(f"  Color range       : {stream.get('color_range')}")
            print(f"  Bitrate           : {stream.get('bit_rate')} bps")

        elif stream.get("codec_type") == "audio":
            print("\nAudio Stream")
            print(f"  Codec             : {stream.get('codec_name')}")
            print(f"  Codec long name   : {stream.get('codec_long_name')}")
            print(f"  Channels          : {stream.get('channels')}")
            print(f"  Sample rate       : {stream.get('sample_rate')} Hz")
            print(f"  Bitrate           : {stream.get('bit_rate')} bps")
            print(f"  Channel layout    : {stream.get('channel_layout')}")

        elif stream.get("codec_type") == "subtitle":
            print("\nSubtitle Stream")
            print(f"  Codec             : {stream.get('codec_name')}")
            print(f"  Language          : {stream.get('tags', {}).get('language')}")

    print("\n" + "=" * 60)
    print("This output shows WHY the MKV may not play correctly on your LCD.")
    print("Common problem indicators:")
    print("  - Video codec: hevc / h265")
    print("  - Pixel format: yuv420p10le (10‑bit)")
    print("  - HDR metadata (bt2020 / smpte2084)")
    print("  - Audio codec: dts / truehd / eac3")
    print("=" * 60)


if __name__ == "__main__":
    main()
