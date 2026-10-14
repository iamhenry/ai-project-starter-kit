#!/usr/bin/env python3
"""watch_video.py - timestamped speech transcript plus frame sheets for a narrated screen recording.

Needs Python 3 with Pillow (contact sheets), ffmpeg/ffprobe, whisper.cpp (whisper-cli on PATH), the ggml-base
model at ~/.cache/whisper/ggml-base.bin, and the Silero VAD model at ~/.cache/whisper/ggml-silero-v5.1.2.bin
(unless --no-vad). Same code on macOS and Linux. Setup: SKILL.md.

Usage: watch_video.py <video> [--out DIR] [--window 1.5] [--max-bursts 12] [--scene 0.02]
"""
import argparse
import bisect
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("[watch-video] ERROR: Pillow is missing. Install: python3 -m pip install --user pillow "
             "(Debian/Ubuntu: sudo apt install python3-pil)")

MODEL_DEFAULT = Path.home() / ".cache" / "whisper" / "ggml-base.bin"
VAD_MODEL_DEFAULT = Path.home() / ".cache" / "whisper" / "ggml-silero-v5.1.2.bin"
VAD_THRESHOLD_DEFAULT = 0.3
WHISPER_NAMES = ("whisper-cli", "whisper-cpp", "main")  # Homebrew, Debian, and source builds name it differently
LABEL_FONT_PX = 13
LABEL_H = 20
MAX_SHEET_W = 1600
JPEG_QUALITY = 80
OVERVIEW_MAX = 40
OVERVIEW_COLS = 8
DETAIL_COLS = 10
DETAIL_ROWS = 6
PAUSE_S = 0.6
MAX_WORDS_PER_LINE = 14
MAX_SECONDS_WITHOUT_FORCE = 300


def log(msg):
    print(f"[watch-video] {msg}", file=sys.stderr, flush=True)


def die(msg, code=1):
    log(f"ERROR: {msg}")
    sys.exit(code)


def need(cmd):
    if shutil.which(cmd) is None:
        die(f"'{cmd}' not on PATH. One-time setup: see SKILL.md (brew install whisper-cpp, model download).")


def run(cmd, what):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"{what} failed: {r.stderr.strip()[-800:]}")
    return r


def find_whisper():
    for name in WHISPER_NAMES:
        path = shutil.which(name)
        if path:
            return path
    die("whisper.cpp not on PATH (looked for whisper-cli, whisper-cpp, main). One-time setup: see SKILL.md.")


def probe(video):
    r = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(video)],
            "ffprobe")
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    if v is None:
        die("no video stream in input")
    num, den = (v.get("avg_frame_rate") or "0/1").split("/")
    fps = float(num) / float(den) if float(den or 0) else 0.0
    return {
        "duration": float(d["format"]["duration"]),
        "size_bytes": int(d["format"]["size"]),
        "width": v["width"],
        "height": v["height"],
        "fps_avg": round(fps, 2),
        "has_audio": any(s["codec_type"] == "audio" for s in d["streams"]),
    }


def frame_times(video):
    """Presentation-order timestamps. Frame index n in ffmpeg filters equals the position here."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "frame=pts_time",
             "-of", "csv=p=0", str(video)], "ffprobe frames")
    pts = []
    for line in r.stdout.splitlines():
        try:
            pts.append(float(line.strip().rstrip(",")))
        except ValueError:
            pass
    if not pts:
        die("no frame timestamps found")
    return sorted(pts)


def group_lines(words):
    lines, cur = [], []

    def flush():
        if cur:
            lines.append({"start": cur[0]["start"], "end": cur[-1]["end"],
                          "text": " ".join(w["text"] for w in cur)})
            cur.clear()

    for w in words:
        if cur and (w["start"] - cur[-1]["end"] > PAUSE_S or len(cur) >= MAX_WORDS_PER_LINE):
            flush()
        cur.append(w)
        last = w["text"][-1]
        if last in ".?!" or (last == "," and len(cur) >= 6):
            flush()
    flush()
    return lines


def transcribe(video, info, work, model, lang, vad_model, whisper_bin):
    if not info["has_audio"]:
        log("no audio stream: skipping transcript")
        return [], []
    wav = work / "audio.wav"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(wav)], "audio extract")
    prefix = work / "words"
    cmd = [whisper_bin, "-m", str(model), "-f", str(wav), "-l", lang, "-ml", "1", "-sow",
           "-oj", "-of", str(prefix)]
    if vad_model is not None:
        # Silero VAD stops Whisper from placing words early after pauses (smoke test: up to 2 s late -> 0.3 s).
        cmd += ["--vad", "-vm", str(vad_model), "-vt", str(VAD_THRESHOLD_DEFAULT)]
    run(cmd, "whisper.cpp")
    data = json.loads(prefix.with_suffix(".json").read_text())
    words = []
    for seg in data.get("transcription", []):
        text = seg.get("text", "").strip()
        if not text or text.startswith("["):
            continue
        words.append({"start": seg["offsets"]["from"] / 1000.0,
                      "end": seg["offsets"]["to"] / 1000.0, "text": text})
    return group_lines(words), words


def motion_bursts(video, threshold, gap, max_bursts):
    """Scene-change hits (ffmpeg select gt(scene)), clustered into bursts; keep the strongest."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-an", "-vf",
                        f"select='gt(scene,{threshold})',metadata=print:key=lavfi.scene_score",
                        "-f", "null", "-"], capture_output=True, text=True)
    hits = []
    for line in r.stderr.splitlines():
        m = re.search(r"pts_time:([0-9.]+)", line)
        if m:
            hits.append([float(m.group(1)), 0.0])
            continue
        m = re.search(r"lavfi\.scene_score=([0-9.]+)", line)
        if m and hits:
            hits[-1][1] = float(m.group(1))
    hits.sort()
    bursts = []
    for t, s in hits:
        if bursts and t - bursts[-1]["end"] <= gap:
            b = bursts[-1]
            b["end"] = t
            b["hits"] += 1
            if s > b["peak_score"]:
                b["peak_score"], b["peak_t"] = s, t
        else:
            bursts.append({"start": t, "end": t, "hits": 1, "peak_t": t, "peak_score": s})
    total = len(bursts)
    kept = sorted(bursts, key=lambda b: -b["peak_score"])[:max_bursts]
    return sorted(kept, key=lambda b: b["start"]), total


def build_moments(lines, bursts, window, duration):
    """One moment per speech line (padded by window). Motion bursts only where no speech window covers them."""
    moments = []
    for ln in lines:
        moments.append({"kind": "say", "start": max(0.0, ln["start"] - window),
                        "end": min(duration, ln["end"] + window), "lines": [ln], "bursts": []})
    for b in bursts:
        a = max(0.0, b["start"] - window)
        e = min(duration, b["end"] + window)
        covered = next((m for m in moments if m["start"] <= b["peak_t"] <= m["end"]), None)
        if covered is not None:
            covered["bursts"].append(b)
        else:
            moments.append({"kind": "motion", "start": a, "end": e, "lines": [], "bursts": [b]})
    moments.sort(key=lambda m: m["start"])
    return moments


def extract(video, indices, out_dir, width=None):
    """Write the given frame indices (contiguous or not) as JPEGs, in order. Returns sorted file list."""
    out_dir.mkdir(parents=True, exist_ok=True)
    if not indices:
        return []
    lo, hi = indices[0], indices[-1]
    if hi - lo + 1 == len(indices):
        sel = f"between(n\\,{lo}\\,{hi})"
    else:
        sel = "+".join(f"eq(n\\,{i})" for i in indices)
    vf = f"select='{sel}'" + (f",scale={width}:-2" if width else "")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", vf, "-fps_mode", "passthrough",
         "-q:v", "4", str(out_dir / "f_%05d.jpg")], "frame extract")
    return sorted(out_dir.glob("f_*.jpg"))


def sheet(rows, out, cols, cell_w):
    """rows: list of (image_path, label). One labelled contact sheet, cells row by row, label band above each image."""
    cols = max(1, min(cols, MAX_SHEET_W // cell_w))
    font = ImageFont.load_default(size=LABEL_FONT_PX)
    thumbs, thumb_h = [], None
    for path, label in rows:
        with Image.open(path) as src:
            im = src.convert("RGB")
        if thumb_h is None:
            thumb_h = round(cell_w * im.height / im.width)
        thumbs.append((im.resize((cell_w, thumb_h), Image.LANCZOS), label))
    cell_h = LABEL_H + thumb_h
    canvas = Image.new("RGB", (cols * cell_w, -(-len(thumbs) // cols) * cell_h), (31, 31, 31))
    draw = ImageDraw.Draw(canvas)
    for i, (thumb, label) in enumerate(thumbs):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        draw.rectangle([x, y, x + cell_w - 1, y + LABEL_H - 1], fill=(0, 0, 0))
        draw.text((x + 4, y + 3), label, font=font, fill=(255, 235, 102))
        canvas.paste(thumb, (x, y + LABEL_H))
    canvas.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)


def fmt_t(t):
    return f"{t:.3f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--out", type=Path, default=None, help="output dir (default: <video>.watch next to video)")
    ap.add_argument("--window", type=float, default=1.5, help="seconds before/after each moment (default 1.5)")
    ap.add_argument("--scene", type=float, default=0.02, help="scene-change threshold for motion bursts")
    ap.add_argument("--max-bursts", type=int, default=12, help="strongest motion bursts to keep")
    ap.add_argument("--thumb-width", type=int, default=150, help="detail frame width in px")
    ap.add_argument("--model", type=Path, default=MODEL_DEFAULT)
    ap.add_argument("--vad-model", type=Path, default=VAD_MODEL_DEFAULT, help="Silero VAD model (default on)")
    ap.add_argument("--no-vad", action="store_true", help="skip voice activity detection (faster to set up, less accurate timing)")
    ap.add_argument("--lang", default="en", help="whisper language code, or auto")
    ap.add_argument("--force", action="store_true", help=f"allow videos longer than {MAX_SECONDS_WITHOUT_FORCE}s")
    args = ap.parse_args()

    t0 = time.time()
    video = args.video.expanduser().resolve()
    if not video.is_file():
        die(f"no such file: {video}")
    for cmd in ("ffmpeg", "ffprobe"):
        need(cmd)
    if not args.model.is_file():
        die(f"model missing: {args.model}. One-time setup in SKILL.md.")
    vad_model = None
    if not args.no_vad:
        if not args.vad_model.is_file():
            die(f"VAD model missing: {args.vad_model}. One-time setup in SKILL.md (or pass --no-vad).")
        vad_model = args.vad_model
    whisper_bin = find_whisper()

    out = (args.out or video.with_name(video.stem + ".watch")).expanduser().resolve()
    info = probe(video)
    if info["duration"] > MAX_SECONDS_WITHOUT_FORCE and not args.force:
        die(f"video is {info['duration']:.0f}s; trim it first or pass --force")
    log(f"video {info['width']}x{info['height']}, {info['duration']:.2f}s, ~{info['fps_avg']} fps, "
        f"audio={'yes' if info['has_audio'] else 'no'}")

    out.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(out / "moments", ignore_errors=True)
    shutil.rmtree(out / "keyframes", ignore_errors=True)
    work = Path(tempfile.mkdtemp(prefix="watch-video-"))
    try:
        pts = frame_times(video)
        log(f"{len(pts)} frames")

        log("transcribing (whisper.cpp, base model" + (", Silero VAD)" if vad_model else ", no VAD)"))
        lines, words = transcribe(video, info, work, args.model, args.lang, vad_model, whisper_bin)
        log(f"{len(lines)} speech lines")

        log("scanning for motion bursts")
        bursts, burst_total = motion_bursts(video, args.scene, 0.35, args.max_bursts)
        log(f"{burst_total} bursts found, keeping {len(bursts)}")

        # Overview: evenly spaced frames, about one per 2 s, capped.
        n_over = min(OVERVIEW_MAX, max(2, round(info["duration"] / 2)))
        over_idx = sorted({min(len(pts) - 1, bisect.bisect_left(pts, k * info["duration"] / n_over))
                           for k in range(n_over)})
        over_files = extract(video, over_idx, work / "overview", width=180)
        over_rows = [(str(f), f"#{i} t={fmt_t(pts[i])}s") for f, i in zip(over_files, over_idx)]
        sheet(over_rows, out / "overview.jpg", OVERVIEW_COLS, 180)
        log(f"overview: {len(over_files)} frames")

        # Detail: every native frame inside each moment, labelled.
        moments = build_moments(lines, bursts, args.window, info["duration"])
        detail_rows_total = 0
        moment_index = []
        per_sheet = DETAIL_COLS * DETAIL_ROWS
        for mi, m in enumerate(moments, 1):
            i0 = bisect.bisect_left(pts, m["start"] - 1e-6)
            i1 = bisect.bisect_right(pts, m["end"] + 1e-6) - 1
            if i1 < i0:
                continue
            idx = list(range(i0, i1 + 1))
            mdir = out / "moments" / f"m{mi:02d}-{m['kind']}-{m['start']:.2f}-{m['end']:.2f}"
            mdir.mkdir(parents=True, exist_ok=True)
            files = extract(video, idx, work / f"m{mi:02d}", width=args.thumb_width)
            if len(files) != len(idx):
                log(f"warning: moment {mi} expected {len(idx)} frames, got {len(files)}")
            tsv = ["frame_index\tpts_s\tsheet\tposition"]
            sheets_written = []
            for s_no, start in enumerate(range(0, len(idx), per_sheet), 1):
                chunk = idx[start:start + per_sheet]
                rows = []
                for pos, fi in enumerate(chunk):
                    rows.append((str(files[start + pos]), f"#{fi} t={fmt_t(pts[fi])}s"))
                    tsv.append(f"{fi}\t{fmt_t(pts[fi])}\tsheet-{s_no:02d}.jpg\t{pos + 1}")
                name = f"sheet-{s_no:02d}.jpg"
                sheet(rows, mdir / name, DETAIL_COLS, args.thumb_width)
                sheets_written.append({"path": f"{mdir.name}/{name}", "t0": pts[chunk[0]], "t1": pts[chunk[-1]]})
            (mdir / "frames.tsv").write_text("\n".join(tsv) + "\n")
            detail_rows_total += len(idx)
            shutil.rmtree(work / f"m{mi:02d}", ignore_errors=True)
            moment_index.append({"n": mi, "kind": m["kind"], "start": m["start"], "end": m["end"],
                                 "dir": mdir.name, "frames": len(idx), "sheets": sheets_written,
                                 "lines": m["lines"], "bursts": m["bursts"]})
        log(f"detail: {len(moment_index)} moments, {detail_rows_total} frames")

        # Full-size key frames at each kept motion peak.
        kf_dir = out / "keyframes"
        for b in bursts:
            i = min(len(pts) - 1, bisect.bisect_left(pts, b["peak_t"] - 1e-6))
            extract(video, [i], kf_dir / "tmp")
            tmp = next((kf_dir / "tmp").glob("f_*.jpg"), None)
            if tmp:
                kf_dir.mkdir(parents=True, exist_ok=True)
                tmp.rename(kf_dir / f"motion-{b['peak_t']:.3f}s.jpg")
            shutil.rmtree(kf_dir / "tmp", ignore_errors=True)

        write_index(out, video, info, lines, words, bursts, burst_total, moment_index, over_idx, pts, args)
        size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
        log(f"done in {time.time() - t0:.1f}s; output {size / 1e6:.1f} MB at {out}")
        print(out / "index.md")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def write_index(out, video, info, lines, words, bursts, burst_total, moments, over_idx, pts, args):
    srt = []
    for i, ln in enumerate(lines, 1):
        srt.append(f"{i}\n{srt_ts(ln['start'])} --> {srt_ts(ln['end'])}\n{ln['text']}\n")
    (out / "transcript.srt").write_text("\n".join(srt))
    (out / "transcript.json").write_text(json.dumps({"lines": lines, "words": words}, indent=1))

    md = [f"# watch-video: {video.name}", "",
          f"- Source: {info['duration']:.2f} s, {info['width']}x{info['height']}, ~{info['fps_avg']} fps, "
          f"audio {'yes' if info['has_audio'] else 'no'}",
          f"- Overview: `overview.jpg` ({len(over_idx)} frames, about 1 per 2 s, timestamps on each cell)",
          f"- Motion bursts: {burst_total} found, {len(bursts)} kept (scene > {args.scene}, window +/-{args.window} s)",
          f"- Detail window: +/-{args.window} s around each speech line and each motion burst outside speech",
          "- Read order: transcript, then the detail sheets for each moment, then judge the frames.",
          "- Transcript is Whisper base output with Silero VAD. Times can still be off by about 1 s, and names or numbers may be wrong. "
          "Check the frames.",
          "", "## Transcript", ""]
    if lines:
        md += ["| Start | End | Words |", "|---|---|---|"]
        md += [f"| {ln['start']:.2f} | {ln['end']:.2f} | {ln['text']} |" for ln in lines]
    else:
        md.append("_No speech found (or no audio stream)._")
    md += ["", "## Moments", "",
           "Each moment is every frame from its start to end. Sheets are labelled `#frame t=seconds`.", ""]
    for m in moments:
        md.append(f"### m{m['n']:02d} {m['kind']} {m['start']:.2f} to {m['end']:.2f} s ({m['frames']} frames)")
        if m["lines"]:
            md.append("- Heard: " + " / ".join(f"\"{ln['text']}\" ({ln['start']:.2f} s)" for ln in m["lines"]))
        if m["bursts"]:
            md.append("- Motion peaks: " + ", ".join(f"{b['peak_t']:.3f} s (score {b['peak_score']:.3f})"
                                                       for b in m["bursts"]))
        md.append(f"- Frame list: `moments/{m['dir']}/frames.tsv`")
        md += [f"- Sheet: `moments/{s['path']}`, frames {s['t0']:.3f} to {s['t1']:.3f} s" for s in m["sheets"]]
        md.append("")
    kfs = sorted((out / "keyframes").glob("motion-*.jpg")) if (out / "keyframes").exists() else []
    if kfs:
        md += ["## Full-size key frames", ""] + [f"- `keyframes/{k.name}`" for k in kfs] + [""]
    (out / "index.md").write_text("\n".join(md) + "\n")


def srt_ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


if __name__ == "__main__":
    main()
