#!/usr/bin/env python3
"""
mkv_to_mp4_converter.py

A robust command-line Python helper to convert or remux MKV files to MP4 using ffmpeg.

Features:
 - Checks for ffmpeg/ffprobe availability
 - Uses ffprobe to inspect codecs and decides whether remuxing (no re-encode) is safe
 - Option to force re-encoding video and/or audio
 - Provides sensible defaults for TV compatibility (h.264 + AAC + yuv420p)
 - Batch mode for directories
 - Simple logging and error messages

Usage examples:
  # Single file - automatic (remux if safe, else re-encode)
  python mkv_to_mp4_converter.py "MyShow.mkv"

  # Force re-encode to h264 + aac with CRF 23 (good quality)
  python mkv_to_mp4_converter.py "MyShow.mkv" --reencode-video --crf 23 --preset medium --audio-bitrate 192k

  # Batch convert all mkv files in current folder, place outputs in "converted/"
  python mkv_to_mp4_converter.py --batch . --output-dir converted

Notes:
 - You must have ffmpeg and ffprobe installed and available in PATH.
 - For stubborn color/brightness issues with HDR or HEVC sources, use --force-yuv420 to add -pix_fmt yuv420p which improves compatibility on many TVs.

"""

from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Dict, Optional, Tuple, List


def check_tool(name: str) -> bool:
    return shutil.which(name) is not None


def run_ffprobe(file: str) -> Dict:
    """Run ffprobe and return parsed JSON metadata for the file."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        file,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(proc.stdout)
    except subprocess.CalledProcessError as e:
        print(f"ffprobe failed: {e}.\nstderr:\n{e.stderr}")
        raise


def get_primary_codecs(file: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (video_codec, audio_codec) for the first video/audio streams found."""
    info = run_ffprobe(file)
    vcodec = None
    acodec = None
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and vcodec is None:
            vcodec = s.get("codec_name")
        if s.get("codec_type") == "audio" and acodec is None:
            acodec = s.get("codec_name")
        if vcodec and acodec:
            break
    return vcodec, acodec


# A conservative set of codecs that are usually safe in MP4 container for most players
SAFE_VIDEO_CODECS = {"h264", "mpeg4"}  # hevc may be supported but is often problematic on older TVs
SAFE_AUDIO_CODECS = {"aac", "mp3", "ac3"}  # ac3 in mp4 may not be widely supported on all devices


def is_remux_safe(vcodec: Optional[str], acodec: Optional[str]) -> bool:
    """Decide whether we can simply copy streams into MP4 without re-encoding.

    This is a heuristic: if codecs are in SAFE sets then remuxing is attempted.
    """
    if vcodec is None:
        return False
    # treat hevc (h265) as unsafe by default for broad compatibility
    low_v = vcodec.lower()
    low_a = acodec.lower() if acodec else None
    if low_v in SAFE_VIDEO_CODECS and (low_a is None or low_a in SAFE_AUDIO_CODECS):
        return True
    return False


def build_ffmpeg_cmd(
    infile: str,
    outfile: str,
    reencode_video: bool,
    reencode_audio: bool,
    crf: int,
    preset: str,
    audio_bitrate: str,
    force_yuv420: bool,
    extra_args: Optional[List[str]] = None,
) -> List[str]:
    cmd = ["ffmpeg", "-y", "-i", infile]

    if not reencode_video:
        cmd += ["-c:v", "copy"]
    else:
        cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf)]
        if force_yuv420:
            cmd += ["-pix_fmt", "yuv420p"]

    if not reencode_audio:
        cmd += ["-c:a", "copy"]
    else:
        # Use AAC audio which is broadly compatible
        cmd += ["-c:a", "aac", "-b:a", audio_bitrate, "-ac", "2"]

    if extra_args:
        cmd += extra_args

    # mp4 container
    cmd += ["-movflags", "+faststart", outfile]
    return cmd


def convert_file(
    infile: str,
    outfile: str,
    reencode_video: bool,
    reencode_audio: bool,
    crf: int,
    preset: str,
    audio_bitrate: str,
    force_yuv420: bool,
    verbose: bool = True,
) -> None:
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    cmd = build_ffmpeg_cmd(infile, outfile, reencode_video, reencode_audio, crf, preset, audio_bitrate, force_yuv420)
    if verbose:
        print("Running ffmpeg:\n", " ".join(cmd))
    try:
        # stream ffmpeg output to console so the user can see progress
        subprocess.run(cmd, check=True)
        if verbose:
            print(f"Done: {outfile}")
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed on {infile} with return code {e.returncode}")
        raise


def safe_output_path(input_path: str, output_dir: str) -> str:
    base = os.path.splitext(os.path.basename(input_path))[0]
    out = os.path.join(output_dir, base + ".mp4")
    # avoid overwriting existing file unless user wants that; for now allow overwrite
    return out


def find_mkv_files(path: str) -> List[str]:
    files = []
    if os.path.isfile(path) and path.lower().endswith(".mkv"):
        files.append(path)
    elif os.path.isdir(path):
        for entry in os.listdir(path):
            if entry.lower().endswith(".mkv"):
                files.append(os.path.join(path, entry))
    return sorted(files)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Convert MKV files to MP4 (remux or re-encode with ffmpeg)")
    p.add_argument("input", nargs="?", help="Input file or directory (use --batch to treat as folder)")
    p.add_argument("--batch", action="store_true", help="Treat input as a directory and convert all .mkv files inside")
    p.add_argument("--output-dir", default=".", help="Directory to write outputs into")
    p.add_argument("--reencode-video", action="store_true", help="Force re-encoding video to h264")
    p.add_argument("--reencode-audio", action="store_true", help="Force re-encoding audio to AAC")
    p.add_argument("--crf", type=int, default=23, help="CRF for x264 (lower = higher quality, default 23)")
    p.add_argument("--preset", default="medium", help="x264 preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)")
    p.add_argument("--audio-bitrate", default="160k", help="Audio bitrate for AAC when re-encoding, e.g. 128k, 192k")
    p.add_argument("--force-yuv420", action="store_true", help="Force pixel format to yuv420p (improves compatibility on many TVs)")
    p.add_argument("--yes", "-y", action="store_true", help="Automatically overwrite existing files without prompting")
    p.add_argument("--no-ffprobe", action="store_true", help="Skip ffprobe inspection and assume remux is okay (not recommended)")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not check_tool("ffmpeg"):
        print("Error: ffmpeg is not installed or not found in PATH.\nPlease install ffmpeg and ffprobe and try again.\nExamples:\n  Ubuntu: sudo apt install ffmpeg\n  Mac (Homebrew): brew install ffmpeg\n  Windows: install ffmpeg and add to PATH")
        sys.exit(1)

    inputs: List[str] = []
    if args.batch:
        if not args.input:
            print("--batch requires an input directory (or path).")
            sys.exit(1)
        inputs = find_mkv_files(args.input)
        if not inputs:
            print(f"No .mkv files found in {args.input}")
            sys.exit(0)
    else:
        if not args.input:
            print("Please specify an input MKV file or use --batch to process a directory.")
            sys.exit(1)
        inputs = [args.input]

    for infile in inputs:
        if not os.path.isfile(infile):
            print(f"Skipping missing file: {infile}")
            continue

        outpath = safe_output_path(infile, args.output_dir)

        # if user didn't request re-encoding, use ffprobe to inspect
        reenc_video = args.reencode_video
        reenc_audio = args.reencode_audio

        if not args.no_ffprobe and (not reenc_video or not reenc_audio):
            try:
                vcodec, acodec = get_primary_codecs(infile)
                print(f"Detected codecs for {infile}: video={vcodec} audio={acodec}")
                if not reenc_video and not is_remux_safe(vcodec, acodec):
                    # Remux is not safe -> recommend re-encoding video/audio
                    print("Remuxing may be incompatible with MP4 on many players. Will re-encode to h264/AAC by default.")
                    reenc_video = True
                    reenc_audio = True
                else:
                    print("Codec combination looks safe for remuxing -> will copy streams into MP4 (fast).")
            except Exception as e:
                print(f"Warning: ffprobe failed; falling back to re-encoding. Error: {e}")
                reenc_video = True
                reenc_audio = True

        # Build and run ffmpeg command
        try:
            convert_file(
                infile,
                outpath,
                reencode_video=reenc_video,
                reencode_audio=reenc_audio,
                crf=args.crf,
                preset=args.preset,
                audio_bitrate=args.audio_bitrate,
                force_yuv420=args.force_yuv420,
            )
        except Exception as e:
            print(f"Failed converting {infile}: {e}")


if __name__ == "__main__":
    main()
