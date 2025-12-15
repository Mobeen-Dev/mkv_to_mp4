import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_DIR = "Naruto_S6"
OUTPUT_DIR = "Naruto_S6_"
MAX_WORKERS = 4  # safe default

os.makedirs(OUTPUT_DIR, exist_ok=True)

def convert(file):
    infile = os.path.join(INPUT_DIR, file)
    outfile = os.path.join(OUTPUT_DIR, os.path.splitext(file)[0] + ".mp4")

    cmd = [
        "ffmpeg", "-y",
        "-i", infile,
        "-map", "0:v:0", "-map", "0:a:0",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level:v", "4.0",
        "-preset", "medium",
        "-crf", "20",
        "-vf", "scale=1280:720,format=yuv420p",
        "-r", "30000/1001",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ac", "2",
        "-ar", "32000",
        "-movflags", "+faststart",
        outfile
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return file

files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".mkv")]

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(convert, f) for f in files]
    for f in as_completed(futures):
        print("Finished:", f.result())
