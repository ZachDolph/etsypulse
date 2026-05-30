"""
Compose the EtsyPulse demo video from screenshots + narration.
Uses FFmpeg xfade transitions and subtle Ken Burns zoom.
"""
import subprocess
import os
from pathlib import Path

BASE = Path(__file__).parent.parent.parent.parent  # project root
SHOTS_DIR = BASE / "docs/submission/screenshots"
FINAL_OUT  = BASE / "docs/submission/video/etsypulse-demo.mp4"
FINAL_COPY = BASE / "docs/submission/final/etsypulse-demo.mp4"
NARRATION  = BASE / "docs/submission/video/narration-full.mp3"
ARCH_DIAG  = BASE / "docs/submission/architecture-diagram.png"

W, H = 1440, 900  # source screenshot resolution
FPS = 30

# Scene → (screenshot, duration_on_screen_s)
# Durations derived from narration chunks + 0.8s gap padding
# S1=15.1, S2=18.4, S3=23.5, S4=24.3, S5=25.3, S6=20.8  + 5× 0.8s gaps = 131.4s
SCENE_DUR = [16.5, 20.0, 25.1, 25.9, 26.9, 17.0]  # add 1.5s overlap budget per slide

SLIDES = [
    SHOTS_DIR / "01-dashboard-hero.png",
    SHOTS_DIR / "02-shop-bootstrap.png",
    SHOTS_DIR / "03-agent-workflow.png",
    SHOTS_DIR / "04-activity-debug.png",
    SHOTS_DIR / "05-judge-brief.png",
    SHOTS_DIR / "06-market-pulse.png",
]

TRANSITION_DURATION = 1.2  # seconds for crossfade
TRANSITION_EXPR = "xfade=transition=fade:duration={dur}:offset={offset}"


def run(cmd: list[str], check: bool = True, label: str = "") -> subprocess.CompletedProcess:
    if label:
        print(f"  → {label}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stderr[-800:] if r.stderr else "")
        raise RuntimeError(f"FFmpeg failed: {' '.join(cmd[:5])}")
    return r


def get_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def make_slide_clip(img: Path, duration: float, out: Path, zoom: float = 1.025) -> None:
    """Render one still image as a video clip with subtle zoom-pan (Ken Burns)."""
    # Use zoompan to add a very gentle slow zoom from 1.0 to zoom factor
    # zoompan: d= frames, z= zoom expression (gradually increases), x/y centered
    n_frames = int(duration * FPS)
    zoom_step = (zoom - 1.0) / n_frames

    run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(img),
        "-vf", (
            f"zoompan=z='min(zoom+{zoom_step:.6f},1.05)':d={n_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
            f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=#f6e8d0"
        ),
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out)
    ], label=f"Slide: {img.name}")


def xfade_clips(clip_a: Path, clip_b: Path, out: Path,
                dur_a: float, transition_dur: float) -> None:
    """Crossfade-dissolve clip_a into clip_b; offset = dur_a - transition_dur."""
    offset = max(0.0, dur_a - transition_dur)
    run([
        "ffmpeg", "-y",
        "-i", str(clip_a), "-i", str(clip_b),
        "-filter_complex",
        f"[0:v][1:v]xfade=transition=fade:duration={transition_dur}:offset={offset}[out]",
        "-map", "[out]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p",
        str(out)
    ], label=f"xfade {clip_a.name} → {clip_b.name}")


def main() -> None:
    FINAL_OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = FINAL_OUT.parent / "tmp_compose"
    tmp.mkdir(exist_ok=True)

    # Step 1: Render each slide as a video clip
    print("Step 1: Rendering slide clips…")
    clips = []
    for i, (slide, dur) in enumerate(zip(SLIDES, SCENE_DUR)):
        out = tmp / f"slide_{i:02d}.mp4"
        make_slide_clip(slide, dur, out)
        clips.append((out, dur))

    # Step 2: Chain clips with xfade transitions
    print("\nStep 2: Joining clips with crossfade…")
    current = clips[0][0]
    current_dur = clips[0][1]
    for i in range(1, len(clips)):
        nxt, nxt_dur = clips[i]
        merged = tmp / f"merged_{i:02d}.mp4"
        xfade_clips(current, nxt, merged, current_dur, TRANSITION_DURATION)
        # new effective duration = sum − overlap
        current_dur = current_dur + nxt_dur - TRANSITION_DURATION
        current = merged

    # Step 3: Get narration duration and trim/pad video to match
    narr_dur = get_duration(NARRATION)
    print(f"\nStep 3: Narration is {narr_dur:.1f}s, video is {current_dur:.1f}s")

    # Step 4: Mux video + narration audio
    print("\nStep 4: Muxing video + narration audio…")
    run([
        "ffmpeg", "-y",
        "-i", str(current),
        "-i", str(NARRATION),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(FINAL_OUT)
    ], label="Final mux")

    # Copy to final/
    import shutil
    FINAL_COPY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(str(FINAL_OUT), str(FINAL_COPY))

    out_dur = get_duration(FINAL_OUT)
    size_mb = FINAL_OUT.stat().st_size / 1_048_576
    print(f"\n✓ Video saved → {FINAL_OUT}")
    print(f"  Duration: {out_dur:.1f}s   Size: {size_mb:.1f} MB")

    # Cleanup temp
    import shutil as _sh
    _sh.rmtree(tmp)


if __name__ == "__main__":
    main()
