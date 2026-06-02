import argparse
import json
import os
import sys
from pathlib import Path


def add_tool_path():
    root = Path(__file__).resolve().parents[1]
    for tool_dir in [Path.cwd() / ".tools" / "python", root / ".tools" / "python"]:
        if tool_dir.exists():
            sys.path.insert(0, str(tool_dir))


def clear_proxy_env():
    for key in list(os.environ):
        if "PROXY" in key.upper():
            os.environ.pop(key, None)


def srt_time(seconds):
    ms = int(round((seconds - int(seconds)) * 1000))
    seconds = int(seconds)
    return f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d},{ms:03d}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wav")
    parser.add_argument("--model", default="base")
    parser.add_argument("--language", default="zh")
    args = parser.parse_args()

    add_tool_path()
    clear_proxy_env()
    root = Path(__file__).resolve().parents[1]
    os.environ.setdefault("HF_HOME", str(root / ".models" / "huggingface"))

    from faster_whisper import WhisperModel

    wav = Path(args.wav)
    out_dir = wav.parent / "transcript"
    out_dir.mkdir(exist_ok=True)

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments_iter, info = model.transcribe(
        str(wav),
        language=args.language,
        vad_filter=True,
        beam_size=5,
    )
    segments = []
    for segment in segments_iter:
        item = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
        }
        segments.append(item)
        print(f"[{srt_time(segment.start)} --> {srt_time(segment.end)}] {item['text']}", flush=True)

    (out_dir / "transcript.json").write_text(
        json.dumps(
            {
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "segments": segments,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "transcript.txt").write_text(
        "\n".join(
            f"[{srt_time(item['start'])} - {srt_time(item['end'])}] {item['text']}"
            for item in segments
        ),
        encoding="utf-8",
    )
    srt_lines = []
    for index, item in enumerate(segments, 1):
        srt_lines.extend(
            [
                str(index),
                f"{srt_time(item['start'])} --> {srt_time(item['end'])}",
                item["text"],
                "",
            ]
        )
    (out_dir / "transcript.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    print(str((out_dir / "transcript.txt").resolve()))


if __name__ == "__main__":
    main()
