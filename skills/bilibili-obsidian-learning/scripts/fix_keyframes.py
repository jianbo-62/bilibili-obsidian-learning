import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def add_tool_path():
    root = Path(__file__).resolve().parents[1]
    for tool_dir in [Path.cwd() / ".tools" / "python", root / ".tools" / "python"]:
        if tool_dir.exists():
            sys.path.insert(0, str(tool_dir))


def run(cmd):
    subprocess.run([str(part) for part in cmd], check=True)


def extract_frame(ffmpeg, video, second, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    run([
        ffmpeg,
        "-y",
        "-ss",
        str(second),
        "-i",
        video,
        "-frames:v",
        "1",
        "-vf",
        "scale=1280:-1",
        "-update",
        "1",
        "-q:v",
        "3",
        dest,
    ])


def main():
    parser = argparse.ArgumentParser(
        description="Extract selected Bilibili keyframes and update Obsidian image links."
    )
    parser.add_argument("download_dir")
    parser.add_argument("obsidian_note")
    parser.add_argument("selection_json")
    parser.add_argument("--video-name", default="video.m4s")
    parser.add_argument("--old-prefix", default="assets/frame_")
    parser.add_argument("--selected-dir", default="assets/selected")
    args = parser.parse_args()

    add_tool_path()
    import imageio_ffmpeg

    download_dir = Path(args.download_dir)
    note_path = Path(args.obsidian_note)
    selected = json.loads(Path(args.selection_json).read_text(encoding="utf-8"))
    video = download_dir / args.video_name
    local_selected_dir = download_dir / "keyframes_selected"
    vault_selected_dir = note_path.parent / args.selected_dir
    vault_selected_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    manifest = []
    new_links = []
    for item in selected:
        filename = item["filename"]
        second = int(item["time_seconds"])
        reason = item.get("reason", "")
        local_frame = local_selected_dir / filename
        extract_frame(ffmpeg, video, second, local_frame)
        shutil.copy2(local_frame, vault_selected_dir / filename)
        manifest.append({"filename": filename, "time_seconds": second, "reason": reason})
        new_links.append(f"{args.selected_dir}/{filename}".replace("\\", "/"))

    (vault_selected_dir / "selected_keyframes_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    note = note_path.read_text(encoding="utf-8")
    old_links = [line.strip()[3:-2] for line in note.splitlines() if line.strip().startswith(f"![[{args.old_prefix}")]
    for old, new in zip(old_links, new_links):
        note = note.replace(f"![[{old}]]", f"![[{new}]]")
    note_path.write_text(note, encoding="utf-8")

    print(note_path)
    print(vault_selected_dir)


if __name__ == "__main__":
    main()
