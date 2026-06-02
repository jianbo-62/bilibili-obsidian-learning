import argparse
import json
import subprocess
import sys
from pathlib import Path


def add_tool_path():
    root = Path(__file__).resolve().parents[1]
    for tool_dir in [Path.cwd() / ".tools" / "python", root / ".tools" / "python"]:
        if tool_dir.exists():
            sys.path.insert(0, str(tool_dir))


def run(cmd):
    print(" ".join(str(part) for part in cmd), flush=True)
    subprocess.run([str(part) for part in cmd], check=True)


def timestamp(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}-{(seconds % 3600) // 60:02d}-{seconds % 60:02d}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("download_dir")
    parser.add_argument("--interval", type=int, default=90)
    args = parser.parse_args()

    add_tool_path()
    import imageio_ffmpeg

    download_dir = Path(args.download_dir)
    summary = json.loads((download_dir / "fetch_summary.json").read_text(encoding="utf-8"))
    duration = int(summary["duration"])
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    video = download_dir / "video.m4s"
    audio = download_dir / "audio.m4s"
    wav = download_dir / "audio_16k.wav"
    frames_dir = download_dir / "keyframes"
    frames_dir.mkdir(exist_ok=True)

    if audio.exists():
        run([
            ffmpeg,
            "-y",
            "-i",
            audio,
            "-ac",
            "1",
            "-ar",
            "16000",
            wav,
        ])

    frame_entries = []
    if video.exists():
        points = [0]
        points.extend(range(args.interval, duration, args.interval))
        if duration - 8 not in points:
            points.append(max(0, duration - 8))
        for sec in sorted(set(points)):
            out = frames_dir / f"frame_{timestamp(sec)}.jpg"
            run([
                ffmpeg,
                "-y",
                "-ss",
                str(sec),
                "-i",
                video,
                "-frames:v",
                "1",
                "-vf",
                "scale=1280:-1",
                "-q:v",
                "3",
                out,
            ])
            if out.exists() and out.stat().st_size:
                frame_entries.append({"time": sec, "path": str(out.resolve())})

    process_summary = {
        "wav": str(wav.resolve()) if wav.exists() else None,
        "frames": frame_entries,
        "ffmpeg": ffmpeg,
    }
    (download_dir / "process_summary.json").write_text(
        json.dumps(process_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(process_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
