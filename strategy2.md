Great — thanks for the profiles. Your MKV is AV1 10-bit @ 1916×1076; the working MP4 target is H.264 8-bit @ 1280×720 with `yuv420p` pixfmt and AAC audio. You’ll need to **re-encode video** (AV1 → H.264), **convert 10-bit → 8-bit** (`yuv420p`), and **rescale** to 1280×720. Below are ready-to-run `ffmpeg` commands (single file + batch), plus short notes on options so you can tune quality/speed.

---

# Recommended single-file command (matches your MP4 profile)

This selects the first video and first audio track, downscales to 1280×720, forces `yuv420p` (8-bit), sets H.264 High profile level 4.0, and converts audio to AAC @ 32 kHz / 128 kbps:

```bash
ffmpeg -i input.mkv \
  -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -profile:v high -level:v 4.0 -preset medium -crf 20 \
  -vf "scale=1280:720,format=yuv420p" -r 30000/1001 \
  -c:a aac -b:a 128k -ac 2 -ar 32000 \
  -movflags +faststart \
  output.mp4
```

What each part does (quick):

* `-map 0:v:0 -map 0:a:0` → pick first video and first audio stream.
* `-c:v libx264` → encode to H.264.
* `-profile:v high -level:v 4.0` → match your TV’s profile/level (High@4.0).
* `-preset medium` → balance speed & compression (use `slow` for better compression, `fast`/`superfast` for quicker).
* `-crf 20` → quality (lower = better). 18–20 ≈ visually indistinguishable; 22–24 smaller file.
* `-vf "scale=1280:720,format=yuv420p"` → rescale and force 8-bit `yuv420p`.
* `-r 30000/1001` → ensure 29.97 fps (match target).
* `-c:a aac -b:a 128k -ac 2 -ar 32000` → stereo AAC @ 32 kHz and 128 kbps (matches your MP4 example).
* `-movflags +faststart` → streamable MP4 (plays faster on some devices).

---

# Faster / lower-quality or slower / higher-quality variants

* **Higher quality**: replace `-crf 20` with `-crf 18` and `-preset medium` → `-preset slow`.
* **Faster**: use `-preset superfast` and `-crf 22` (lower CPU, larger quality loss).
* **Use 48 kHz audio + 160k** (if you prefer the earlier generic recommendation):
  `-c:a aac -b:a 160k -ac 2 -ar 48000`

---

# If you want to keep *all* audio tracks (and drop ASS subtitles)

MP4 handles multiple audio tracks but not ASS subtitles. Example keeps ALL audio streams (transcodes them to AAC) and drops subtitles:

```bash
ffmpeg -i input.mkv \
  -map 0:v:0 \
  -map 0:a \
  -c:v libx264 -profile:v high -level:v 4.0 -preset medium -crf 20 \
  -vf "scale=1280:720,format=yuv420p" -r 30000/1001 \
  -c:a aac -b:a 128k -ac 2 -ar 32000 \
  -sn -movflags +faststart \
  output_with_all_audio.mp4
```

`-sn` disables subtitle streams (ASS cannot be copied directly into standard MP4).

---

# Quick test (avoid long runs while tuning)

Convert only first 30 seconds to verify:

```bash
ffmpeg -ss 0 -t 30 -i input.mkv ... same options ... test.mp4
```

---

# Batch conversion (bash)

Convert every `.mkv` in folder using the single-file command (keeps first audio):

```bash
mkdir -p converted
for f in *.mkv; do
  ffmpeg -i "$f" \
    -map 0:v:0 -map 0:a:0 \
    -c:v libx264 -profile:v high -level:v 4.0 -preset medium -crf 20 \
    -vf "scale=1280:720,format=yuv420p" -r 30000/1001 \
    -c:a aac -b:a 128k -ac 2 -ar 32000 \
    -movflags +faststart \
    "converted/${f%.mkv}.mp4"
done
```

Windows PowerShell one-liner (batch):

```powershell
mkdir converted
Get-ChildItem -Filter *.mkv | ForEach-Object {
  $in = $_.FullName; $out = "converted\$($_.BaseName).mp4"
  ffmpeg -i $in -map 0:v:0 -map 0:a:0 -c:v libx264 -profile:v high -level:v 4.0 -preset medium -crf 20 -vf "scale=1280:720,format=yuv420p" -r 30000/1001 -c:a aac -b:a 128k -ac 2 -ar 32000 -movflags +faststart $out
}
```

---

# Notes & gotchas

* **AV1 → H.264** re-encode is CPU-heavy (especially if file is long). Test on a short clip first.
* **10-bit → 8-bit**: `format=yuv420p` will drop to 8-bit; this is necessary because many TVs don’t support 10-bit.
* **ASS subtitles**: MP4 doesn’t carry ASS. If subtitles are important you can:

  * burn them in: add `-vf "subtitles=input.mkv"` (slower, hardcodes subtitles),
  * or extract `.srt` from ASS and re-add as `mov_text` where possible (not always perfect).
* **Color metadata**: your MKV lacked explicit color primaries; forcing `bt709` usually works for SDR content. If you see color shifts, we can add `-colorspace bt709 -color_primaries bt709 -color_trc bt709` to the command.
* **If audio sounds wrong on TV**: try using `-ar 48000` and/or `-b:a 160k` (some TVs prefer 48 kHz).

---

If you want, I can:

* give you a one-click Windows .bat or macOS Automator script for the batch loop, or
* modify your existing Python converter to automatically read the MP4 reference profile and apply the correct `ffmpeg` options.

Which would you like next?
