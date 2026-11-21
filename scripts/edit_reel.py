#!/usr/bin/env python3
"""Edit a raw clip into an Instagram Reel with one ffmpeg pass.

What it does (each step optional except the reframe):
  * trim to --start/--end
  * reframe to 1080x1920 (9:16), cropping to fill; --focus shifts the crop
    left/right (0 = left edge, 0.5 = centre, 1 = right edge)
  * --slowmo A-B@F  slow the part between A and B seconds (source time) to
    factor F (0.25 = 4x slower), audio slowed with it
  * --hook TEXT     big hook card from frame 1 for --hook-secs seconds
  * --card A-B:TEXT extra on-screen cards (repeatable), output-time seconds
  * --music FILE    replace or mix the audio (--music-only to drop original)
  * loudness normalised to -14 LUFS (Instagram's playback level)

Text stays inside the Reels safe zone (y 230..1440, right 230px clear).

Examples
  python3 scripts/edit_reel.py in.mp4 out.mp4 --start 2 --end 14 \
      --slowmo 8-10@0.3 --hook "Olympian vs 10 hurdles"
  python3 scripts/edit_reel.py in.mp4 out.mp4 --hook "POV: 400m hurdles" \
      --card "3-6:hurdle 7 hurts" --card "6-9:hurdle 10 hurts more"
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
W, H = 1080, 1920
SAFE_W = W - 230  # keep the right action rail clear


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
         "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    has_audio = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    return float(d["format"]["duration"]), has_audio


TMP = tempfile.mkdtemp(prefix="reel_text_")
_count = [0]


def textfile(line):
    """Write one line to a file so drawtext needs no escaping at all."""
    _count[0] += 1
    path = os.path.join(TMP, f"t{_count[0]}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(line)
    return path


def atempo_chain(f):
    parts = []
    while f < 0.5:
        parts.append("atempo=0.5")
        f /= 0.5
    parts.append(f"atempo={f:.4f}")
    return ",".join(parts)


def drawtext(text, start, end, y, size):
    # Wrap long text roughly to fit the safe width.
    words, lines, cur = text.split(), [], ""
    max_chars = max(8, int(SAFE_W / (size * 0.62)))
    for w in words:
        if len(cur) + len(w) + 1 > max_chars and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    out = []
    for i, line in enumerate(lines):
        out.append(
            f"drawtext=fontfile={FONT}:textfile={textfile(line)}:expansion=none"
            f":fontsize={size}:fontcolor=white"
            f":box=1:boxcolor=black@0.55:boxborderw=18"
            f":x=(({SAFE_W})-text_w)/2+20:y={y + i * int(size * 1.35)}"
            f":enable='between(t,{start},{end})'")
    return out


def main():
    ap = argparse.ArgumentParser(description="Edit a clip into a 9:16 Reel.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float)
    ap.add_argument("--focus", type=float, default=0.5, help="horizontal crop position 0..1")
    ap.add_argument("--slowmo", help="A-B@F in source seconds, e.g. 8-10@0.3")
    ap.add_argument("--hook", help="hook text shown from frame 1")
    ap.add_argument("--hook-secs", type=float, default=2.5)
    ap.add_argument("--card", action="append", default=[], help="A-B:TEXT (output seconds)")
    ap.add_argument("--music")
    ap.add_argument("--music-only", action="store_true")
    ap.add_argument("--fps", type=int, default=30)
    args = ap.parse_args()

    dur, has_audio = probe(args.input)
    s, e = args.start, min(args.end or dur, dur)
    if e <= s:
        sys.exit("--end must be after --start")

    frame = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
             f"crop={W}:{H}:(in_w-{W})*{args.focus}:(in_h-{H})/2,setsar=1,fps={args.fps}")

    # Segments in source time: [(a, b, factor)]
    segs = [(s, e, 1.0)]
    if args.slowmo:
        rng, f = args.slowmo.split("@")
        a, b = (float(x) for x in rng.split("-"))
        f = float(f)
        a, b = max(a, s), min(b, e)
        segs = [x for x in [(s, a, 1.0), (a, b, f), (b, e, 1.0)] if x[1] - x[0] > 0.05]

    fg, vlabels, alabels = [], [], []
    for i, (a, b, f) in enumerate(segs):
        fg.append(f"[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{f},{frame}[v{i}]")
        vlabels.append(f"[v{i}]")
        if has_audio:
            tempo = f",{atempo_chain(f)}" if f != 1.0 else ""
            fg.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS{tempo}[a{i}]")
            alabels.append(f"[a{i}]")
    out_len = sum((b - a) / f for a, b, f in segs)

    n = len(segs)
    if has_audio:
        fg.append("".join(v + a for v, a in zip(vlabels, alabels)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    else:
        fg.append("".join(vlabels) + f"concat=n={n}:v=1:a=0[vc]")

    texts = []
    if args.hook:
        texts += drawtext(args.hook, 0, args.hook_secs, 300, 84)
    for c in args.card:
        rng, text = c.split(":", 1)
        a, b = (float(x) for x in rng.split("-"))
        texts += drawtext(text, a, b, 300, 72)
    fg.append("[vc]" + (",".join(texts) if texts else "null") + "[vout]")

    inputs = ["-i", args.input]
    if args.music:
        inputs += ["-stream_loop", "-1", "-i", args.music]
        if has_audio and not args.music_only:
            fg.append("[ac][1:a]amix=inputs=2:duration=first:weights=1 0.35[am]")
        else:
            fg.append(f"[1:a]atrim=0:{out_len},asetpts=PTS-STARTPTS[am]")
        alast = "[am]"
    elif has_audio:
        alast = "[ac]"
    else:
        alast = None
    if alast:
        fg.append(f"{alast}loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
           "-filter_complex", ";".join(fg), "-map", "[vout]"]
    if alast:
        cmd += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    cmd += ["-t", f"{out_len:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", args.output]
    subprocess.run(cmd, check=True)
    print(f"wrote {args.output}  {out_len:.1f}s  1080x1920 @ {args.fps}fps")


if __name__ == "__main__":
    main()
