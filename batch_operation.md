Great 👍
Since the **single ffmpeg command works**, the best next step is a **parallel batch script** so your whole folder converts faster.

Below are **clean, safe, and practical** options. Pick the one that matches your OS.

---

## ✅ **Option 1: Python parallel script (BEST & portable)**

This runs **multiple ffmpeg jobs in parallel**, limited by your CPU cores.

### `batch_mkv_to_mp4_parallel.py`

```python
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

INPUT_DIR = "input"
OUTPUT_DIR = "output"
MAX_WORKERS = os.cpu_count() // 2 or 2  # safe default

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
```

### Folder structure

```
project/
 ├─ batch_mkv_to_mp4_parallel.py
 ├─ input/      ← MKV files
 └─ output/     ← MP4 files
```

### Run

```bash
python batch_mkv_to_mp4_parallel.py
```

### Why this is ideal

* Uses your **exact working ffmpeg command**
* Parallel execution
* CPU-safe
* Cross-platform (Windows / Linux / macOS)

---

## ✅ **Option 2: Linux / macOS (GNU Parallel – FASTEST)**

If you have `parallel` installed:

```bash
mkdir -p output

parallel -j 4 '
ffmpeg -y -i {} \
  -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -profile:v high -level:v 4.0 -preset medium -crf 20 \
  -vf "scale=1280:720,format=yuv420p" -r 30000/1001 \
  -c:a aac -b:a 128k -ac 2 -ar 32000 \
  -movflags +faststart \
  output/{/.}.mp4
' ::: *.mkv
```

Change `-j 4` to number of parallel jobs.

---

## ✅ **Option 3: Windows PowerShell (Parallel)**

PowerShell 7+ only:

```powershell
mkdir output

Get-ChildItem *.mkv | ForEach-Object -Parallel {
  $out = "output\$($_.BaseName).mp4"
  ffmpeg -y -i $_.FullName `
    -map 0:v:0 -map 0:a:0 `
    -c:v libx264 -profile:v high -level:v 4.0 -preset medium -crf 20 `
    -vf "scale=1280:720,format=yuv420p" -r 30000/1001 `
    -c:a aac -b:a 128k -ac 2 -ar 32000 `
    -movflags +faststart `
    $out
} -ThrottleLimit 4
```

---

## 🔧 Performance tuning tips

* **AV1 → H.264 is heavy** → don’t exceed `CPU cores / 2`
* If your CPU supports it, you can speed up with:

  * `-preset fast` (slightly larger files)
* Avoid GPU encoders for TVs unless tested (many TVs reject odd H.264 profiles)

