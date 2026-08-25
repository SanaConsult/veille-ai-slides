#!/usr/bin/env python3
"""
Builds a square 1080x1080 Reel video from the day's 5 slide PNGs, with a
crossfade between each slide and a randomly-picked royalty-free background
track (from assets/music/*.mp3) mixed in, faded out at the end.

Usage:
    python3 build_reel.py <slides_dir> <music_dir> <out_path>

<slides_dir> must already contain slide-1.png .. slide-N.png (rendered by
render_slides.js). Requires ffmpeg on PATH.
"""
import glob
import os
import random
import subprocess
import sys

SLIDE_SECONDS = 3.5
XFADE_SECONDS = 0.5


def build_filter_complex(n, slide_seconds, xfade_seconds, audio_index):
    scale_parts = []
    for i in range(n):
        scale_parts.append(f"[{i}:v]scale=1080:1080,setsar=1,fps=30[v{i}]")

    xfade_parts = []
    prev_label = "v0"
    cumulative_offset = 0.0
    for i in range(1, n):
        cumulative_offset += slide_seconds - xfade_seconds
        out_label = f"x{i}" if i < n - 1 else "vout"
        xfade_parts.append(
            f"[{prev_label}][v{i}]xfade=transition=fade:duration={xfade_seconds}:"
            f"offset={cumulative_offset:.2f}[{out_label}]"
        )
        prev_label = out_label

    total_duration = cumulative_offset + slide_seconds
    fade_start = max(total_duration - 1.0, 0.0)
    audio_part = (
        f"[{audio_index}:a]atrim=0:{total_duration:.2f},"
        f"afade=t=out:st={fade_start:.2f}:d=1[aout]"
    )

    filter_complex = ";".join(scale_parts + xfade_parts + [audio_part])
    return filter_complex, total_duration


def main():
    if len(sys.argv) < 4:
        print("Usage: build_reel.py <slides_dir> <music_dir> <out_path>", file=sys.stderr)
        sys.exit(1)

    slides_dir, music_dir, out_path = sys.argv[1], sys.argv[2], sys.argv[3]

    slide_files = sorted(glob.glob(os.path.join(slides_dir, "slide-*.png")))
    if not slide_files:
        print(f"ERROR: no slide-*.png found in {slides_dir}", file=sys.stderr)
        sys.exit(1)

    music_files = sorted(glob.glob(os.path.join(music_dir, "*.mp3")))
    if not music_files:
        print(f"ERROR: no *.mp3 found in {music_dir}", file=sys.stderr)
        sys.exit(1)

    track = random.choice(music_files)
    print(f"Selected track: {track}", file=sys.stderr)

    n = len(slide_files)
    audio_index = n
    filter_complex, total_duration = build_filter_complex(
        n, SLIDE_SECONDS, XFADE_SECONDS, audio_index
    )

    cmd = ["ffmpeg", "-y"]
    for f in slide_files:
        cmd += ["-loop", "1", "-t", str(SLIDE_SECONDS), "-i", f]
    cmd += ["-i", track]
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        "-movflags", "+faststart",
        out_path,
    ]

    print("Running:", " ".join(cmd), file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {out_path} (~{total_duration:.1f}s)")


if __name__ == "__main__":
    main()
