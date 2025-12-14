#!/usr/bin/env python3
"""
inspect_mp4_profile.py

This script inspects a *known-working MP4 file* (one that plays correctly on your LCD TV)
and prints detailed media parameters. You can then use these values as a reference profile
when converting other videos (MKV -> MP4) for maximum compatibility.

It uses ffprobe (part of ffmpeg).

Usage:
  python inspect_mp4_profile.py working_sample.mp4

Output includes:
 - Container format
 - Video codec, profile, level
 - Resolution, frame rate
 - Pixel format (VERY important for TV compatibility)
 - Audio codec, channels, sample rate, bitrate

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
        print("Usage: python inspect_mp4_profile.py working_sample.mp4")
        sys.exit(1)

    mp4_file = sys.argv[1]
    info = run_ffprobe(mp4_file)

    print("=" * 60)
    print("MP4 COMPATIBILITY PROFILE (REFERENCE)")
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
            print(f"  Profile           : {stream.get('profile')}")
            print(f"  Level             : {stream.get('level')}")
            print(f"  Resolution        : {stream.get('width')}x{stream.get('height')}")
            print(f"  Frame rate        : {fps_from_ratio(stream.get('avg_frame_rate'))} fps")
            print(f"  Pixel format      : {stream.get('pix_fmt')}")
            print(f"  Color space       : {stream.get('color_space')}")
            print(f"  Color range       : {stream.get('color_range')}")
            print(f"  Bitrate           : {stream.get('bit_rate')} bps")

        elif stream.get("codec_type") == "audio":
            print("\nAudio Stream")
            print(f"  Codec             : {stream.get('codec_name')}")
            print(f"  Channels          : {stream.get('channels')}")
            print(f"  Sample rate       : {stream.get('sample_rate')} Hz")
            print(f"  Bitrate           : {stream.get('bit_rate')} bps")
            print(f"  Channel layout    : {stream.get('channel_layout')}")

    print("\n" + "=" * 60)
    print("Use these values as your TARGET profile when converting other videos.")
    print("Example ffmpeg settings often matching TV-compatible MP4:")
    print("  -c:v libx264 -profile:v high -level 4.1 -pix_fmt yuv420p")
    print("  -c:a aac -ac 2 -ar 48000 -b:a 160k")
    print("=" * 60)


if __name__ == "__main__":
    main()
