---
name: watch-video
description: Review a local screen recording that has spoken commentary by pairing a timestamped Whisper transcript with labelled frame sheets around each spoken moment and each motion burst. Use when the owner passes a screen recording of a bug, UI glitch, or motion/feature feedback, or says "watch this video", "here's a recording", or "what am I describing at 0:28".
---

# Watch video

Turn a narrated screen recording into a transcript and frame sheets, so you can match what the owner says to what is on screen. One command, no ML stack, runs in about 15 s for a 48 s clip.

## When to use

- The owner sends a screen recording and talks over it ("it snaps here", "boom, that jumps").
- A UI motion glitch, transition, or timing problem that needs frame-level judgment.
- A bug repro where the words say where to look.

## When not to use

- Silent recordings: the frames alone are enough. Use `reproduce-bug` or `argent-screen-recording`.
- Live device or simulator work: use the device skills, not this one.
- Videos over 5 minutes: trim first (`ffmpeg -ss <start> -t <len> -i in.mp4 -c copy out.mp4`), or pass `--force`.

## Run

```bash
python3 .agents/skills/watch-video/scripts/watch_video.py <video.mp4> --out <dir>
```

- `--out` defaults to `<video>.watch/` next to the video. Pick a temp dir for scratch work.
- `--window 1.5` is the seconds before and after each spoken line and motion burst that get every frame sheeted.
- `--scene 0.02` is the motion threshold. `--max-bursts 12` keeps the strongest bursts.
- `--lang` defaults to `en`. `--model` defaults to `~/.cache/whisper/ggml-base.bin`.
- Voice activity detection (Silero VAD) is on by default, using `--vad-model` (default `~/.cache/whisper/ggml-silero-v5.1.2.bin`). `--no-vad` turns it off; it is faster to set up but its transcript times drift by up to about 2 s after pauses.

Output (prints the path of `index.md` at the end):

- `index.md`: start here. Transcript table, then each moment with its heard words, motion peaks, and sheet paths.
- `transcript.srt` and `transcript.json`: word-timed transcript.
- `overview.jpg`: about 1 frame per 2 s across the whole video, timestamps on each cell.
- `moments/mNN-<kind>-<start>-<end>/sheet-KK.jpg` plus `frames.tsv`: every native frame in the window, labelled `#frame t=seconds`, 60 per sheet.
- `keyframes/motion-<t>s.jpg`: full-size frame at each kept motion peak.

## How to read the output

1. Read `index.md` transcript first. It gives the owner's words and rough times.
2. Open the sheet for the moment the owner describes. Find the timestamp in the transcript row, then the matching moment in `index.md`.
3. Judge frame by frame. Use `frames.tsv` to check exact frame numbers and times. Use `keyframes/` for a full-size look.
4. Treat a claim as confirmed only after you see it on the frames. Words alone are a hint.

## One-time setup

```bash
brew install whisper-cpp                      # provides whisper-cli, Metal on Apple Silicon
mkdir -p ~/.cache/whisper
curl -fL -o ~/.cache/whisper/ggml-base.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin
shasum -a 256 ~/.cache/whisper/ggml-base.bin  # expect 60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe
curl -fL -o ~/.cache/whisper/ggml-silero-v5.1.2.bin https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v5.1.2.bin
shasum -a 256 ~/.cache/whisper/ggml-silero-v5.1.2.bin  # expect 29940d98d42b91fbd05ce489f3ecf7c72f0a42f027e4875919a28fb4c04ea2cf
```

`ffmpeg` and `ffprobe` must already be installed. The first run compiles a small Swift helper (`sheet-maker`) into `~/.cache/watch-video/` using `swiftc` from Xcode Command Line Tools. Nothing else is installed.

Known side effect: `brew install whisper-cpp` also upgraded `sdl3` and `sdl2-compat` (smoke test: sdl3 3.4.14 to 3.4.18, sdl2-compat 2.32.70 to 2.32.74). Other Homebrew packages that use SDL were not tested.

## Footprint

- Install: whisper-cpp about 6 MB, its dependencies (sdl3, sdl2-compat, ggml) about 25 MB, base model 148 MB, VAD model 0.9 MB, helper 90 KB.
- Per run: about 0.4 MB per 1 s of recording at default settings. The 48 s smoke clip produced 19.5 MB of sheets and key frames. Scratch audio and raw frames are removed at the end.
- Speed and RAM: about 15 s wall for the 48 s clip; the largest child process (whisper-cli) peaks near 570 MB RSS with VAD.

## Anti-patterns

- Installing a Python ML stack (torch, mlx, pip venvs) for each video. Use the models above.
- Sampling sparse frames for sub-second glitches. Snaps can last 33 ms. The detail sheets keep every native frame; do not swap them for the overview.
- Reading the transcript without the frames, or the frames without the transcript. Use both, line up by time.
- Treating Whisper text as exact. Names, numbers, and UI labels can be wrong. Confirm on screen.
- Trusting Whisper timing to the second. With VAD, the smoke test matched 12 of 13 lines within 1 s; the one outlier was a reference error (the audio was silent until 1.6 s). Without VAD, two lines were 1.4 and 2.1 s late after pauses. The frames around each line (±1.5 s) still cover that, but check the wider neighborhood.
- Leaving bulk frames on disk. Keep only `index.md`, sheets, `frames.tsv`, the transcript, and a few key frames; delete the rest.
- Running on long videos without trimming. Output grows about linearly with duration and overlapping windows.
- Repeating the same analysis per video with a new model or tool. Use the same script and settings so results compare across runs.

## Known limits

- Transcript times are approximate, about ±1 s with VAD on the smoke clip. Motion-burst moments exist partly to cover snaps the transcript misses, so check them even when no line points at them.
- Overlapping windows repeat frames across neighboring moments (about 1.6x the unique frame count). This is deliberate so each moment reads on its own.
- Motion bursts are scene-change hits, not measured layout. Judge the actual movement on the frames.
- The script does not reduce the frame rate or sample sparser. Its footprint scales with narration length, not only with video length.
