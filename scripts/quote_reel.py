#!/usr/bin/env python3
"""Motivational quote reel: dark moody grade + big condensed serif text,
white lines with red emphasis lines, left-aligned inside the Reels safe zone.

Text blocks: --block "Y:line|line|*red line*"  (repeatable)
  Y      top of the block in pixels on the 1080x1920 frame (safe: 230..1440)
  |      new line;  *...*  makes that line red and bigger

Example (the "show up anyway" style):
  python3 scripts/quote_reel.py IN.mp4 out.mp4 --end 9 \
    --block "560:THE DAYS YOU|DON'T WANT TO|ARE THE DAYS|THAT COUNT|*THE MOST.*" \
    --block "1250:*SHOW UP ANYWAY.*"
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "assets", "fonts", "InstrumentSerif-Regular.ttf")
W, H = 1080, 1920
LEFT = 36
MAX_W = W - LEFT - 200  # keep clear of the right action rail
WHITE = (242, 238, 232, 255)
RED = (178, 38, 43, 255)


def fit(draw, text, size):
    """Largest font size <= size whose text fits MAX_W."""
    while size > 30:
        font = ImageFont.truetype(FONT, size)
        if draw.textlength(text, font=font) <= MAX_W:
            return font
        size -= 4
    return ImageFont.truetype(FONT, size)


def render(blocks, path, size, red_scale):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bottom = 0
    for block in blocks:
        y_str, text = block.split(":", 1)
        # Never let a block run into the one above it: keep a clear gap.
        y = max(int(y_str), bottom + int(size * 1.2) if bottom else 0)
        for raw in text.split("|"):
            red = raw.startswith("*") and raw.endswith("*") and len(raw) > 2
            line = raw.strip("*").upper().replace("'", "’")
            font = fit(d, line, int(size * (red_scale if red else 1)))
            # Faux-bold: a thin stroke in the same colour thickens the serif.
            colour = RED if red else WHITE
            sw = max(1, font.size // 45)
            d.text((LEFT, y), line, font=font, fill=colour, stroke_width=sw, stroke_fill=colour)
            asc, desc = font.getmetrics()
            y += int((asc + desc) * 0.86)
        bottom = y
    if bottom > 1440:
        print(f"warning: text reaches y={bottom}, below the safe zone (1440). "
              "Use a smaller --size or a higher Y.", file=sys.stderr)
    img.save(path)


def has_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    return any(s.get("codec_type") == "audio" for s in json.loads(out).get("streams", []))


def main():
    ap = argparse.ArgumentParser(description="Dark quote-overlay reel.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--block", action="append", required=True, help="Y:line|line|*red line*")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--focus", type=float, default=0.5, help="horizontal crop 0..1")
    ap.add_argument("--size", type=int, default=92, help="white line font size")
    ap.add_argument("--red-scale", type=float, default=1.45)
    ap.add_argument("--darkness", type=float, default=0.55, help="0 = original, 1 = black")
    ap.add_argument("--music")
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="quote_")
    png = os.path.join(tmp, "text.png")
    render(args.block, png, args.size, args.red_scale)

    trim = [] if args.start == 0 else ["-ss", str(args.start)]
    if args.end:
        trim += ["-t", str(args.end - args.start)]
    inputs = [*trim, "-i", args.input, "-i", png]
    grade = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H}:(in_w-{W})*{args.focus}:(in_h-{H})/2,setsar=1,fps=30,"
             f"eq=contrast=1.12:saturation=0.7:gamma={1 - args.darkness * 0.45:.3f},"
             f"vignette=PI/4,"
             f"drawbox=0:0:{W}:{H}:black@{args.darkness * 0.5:.2f}:t=fill")
    fg = [f"[0:v]{grade}[bg]", "[bg][1:v]overlay=0:0[vout]"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs]
    maps = ["-map", "[vout]"]
    if args.music:
        cmd += ["-stream_loop", "-1", "-i", args.music]
        fg.append("[2:a]loudnorm=I=-14:TP=-1.5[aout]")
        maps += ["-map", "[aout]", "-shortest"]
    elif has_audio(args.input):
        fg.append("[0:a]loudnorm=I=-14:TP=-1.5[aout]")
        maps += ["-map", "[aout]"]
    cmd += ["-filter_complex", ";".join(fg), *maps, "-c:v", "libx264", "-crf", "18",
            "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", args.output]
    subprocess.run(cmd, check=True)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    sys.exit(main())
