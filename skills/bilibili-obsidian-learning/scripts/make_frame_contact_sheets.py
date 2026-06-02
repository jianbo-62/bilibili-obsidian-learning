import argparse
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def add_tool_path():
    root = Path(__file__).resolve().parents[1]
    for tool_dir in [Path.cwd() / ".tools" / "python", root / ".tools" / "python"]:
        if tool_dir.exists():
            sys.path.insert(0, str(tool_dir))


def ts(seconds):
    seconds = int(seconds)
    return f"{seconds // 3600:02d}-{(seconds % 3600) // 60:02d}-{seconds % 60:02d}"


def run(cmd):
    subprocess.run([str(part) for part in cmd], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--out", required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=1020)
    parser.add_argument("--step", type=int, default=10)
    parser.add_argument("--cols", type=int, default=4)
    args = parser.parse_args()

    add_tool_path()
    import imageio_ffmpeg

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    video = Path(args.video)
    out_dir = Path(args.out)
    frames_dir = out_dir / "frames"
    sheets_dir = out_dir / "sheets"
    frames_dir.mkdir(parents=True, exist_ok=True)
    sheets_dir.mkdir(parents=True, exist_ok=True)

    times = list(range(args.start, args.end + 1, args.step))
    frame_paths = []
    for second in times:
        path = frames_dir / f"candidate_{ts(second)}.jpg"
        if not path.exists() or path.stat().st_size == 0:
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
                "scale=480:-1",
                "-update",
                "1",
                "-q:v",
                "3",
                path,
            ])
        if path.exists() and path.stat().st_size:
            frame_paths.append((second, path))

    font = ImageFont.load_default()
    thumb_w, thumb_h = 480, 270
    label_h = 24
    cols = args.cols
    rows_per_sheet = 5
    per_sheet = cols * rows_per_sheet
    for sheet_index in range(0, len(frame_paths), per_sheet):
        batch = frame_paths[sheet_index:sheet_index + per_sheet]
        rows = (len(batch) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), "white")
        draw = ImageDraw.Draw(sheet)
        for idx, (second, path) in enumerate(batch):
            img = Image.open(path).convert("RGB").resize((thumb_w, thumb_h))
            x = (idx % cols) * thumb_w
            y = (idx // cols) * (thumb_h + label_h)
            sheet.paste(img, (x, y))
            draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(0, 0, 0))
            draw.text((x + 8, y + thumb_h + 5), ts(second).replace("-", ":"), fill=(255, 255, 255), font=font)
        sheet.save(sheets_dir / f"sheet_{sheet_index // per_sheet + 1:02d}.jpg", quality=90)

    print(sheets_dir)


if __name__ == "__main__":
    main()
