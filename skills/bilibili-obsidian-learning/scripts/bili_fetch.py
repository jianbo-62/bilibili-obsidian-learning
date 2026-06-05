import argparse
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


def clear_proxy_env():
    for key in list(os.environ):
        if "PROXY" in key.upper():
            os.environ.pop(key, None)


def request_bytes(url, referer=None, timeout=30):
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl._create_unverified_context()
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
        return response.read()


def request_json(url, referer=None, timeout=30):
    data = request_bytes(url, referer=referer, timeout=timeout)
    return json.loads(data.decode("utf-8", "ignore"))


def sanitize_name(name):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name[:120] or "bilibili-video"


def extract_bvid(url_or_bvid):
    match = re.search(r"(BV[0-9A-Za-z]+)", url_or_bvid)
    if not match:
        raise ValueError(f"Cannot find BV id in: {url_or_bvid}")
    return match.group(1)


def extract_page(url_or_bvid):
    parsed = urllib.parse.urlparse(url_or_bvid)
    query = urllib.parse.parse_qs(parsed.query)
    raw_page = (query.get("p") or [None])[0]
    if not raw_page:
        return 1
    try:
        page = int(raw_page)
    except ValueError as exc:
        raise ValueError(f"Invalid Bilibili page parameter p={raw_page!r}") from exc
    return max(page, 1)


def select_page(data, page_number):
    pages = data.get("pages") or []
    if not pages:
        return {"cid": data["cid"], "page": 1, "part": data.get("title") or ""}
    for page in pages:
        if int(page.get("page") or 0) == page_number:
            return page
    raise ValueError(f"Cannot find page {page_number}; available pages: {[p.get('page') for p in pages]}")


def download_file(url, dest, referer, timeout=60):
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Range": "bytes=0-",
    }
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl._create_unverified_context()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(req, context=ctx, timeout=timeout) as response:
        with dest.open("wb") as f:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                total += len(chunk)
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url_or_bvid")
    parser.add_argument("--out", default="bilibili_downloads")
    parser.add_argument("--media", action="store_true")
    args = parser.parse_args()

    clear_proxy_env()
    bvid = extract_bvid(args.url_or_bvid)
    page_number = extract_page(args.url_or_bvid)
    referer = f"https://www.bilibili.com/video/{bvid}/?p={page_number}"
    view_url = f"https://api.bilibili.com/x/web-interface/view?bvid={urllib.parse.quote(bvid)}"
    view = request_json(view_url, referer=referer)
    if view.get("code") != 0:
        raise RuntimeError(f"view API failed: {view}")

    data = view["data"]
    selected_page = select_page(data, page_number)
    title = data.get("title") or bvid
    part_title = selected_page.get("part") or title
    safe_title = sanitize_name(f"P{page_number:02d}_{part_title}")
    out_dir = Path(args.out) / f"{bvid}_{safe_title}"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "metadata.json").write_text(
        json.dumps(view, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    for key, url in {
        "cover.jpg": data.get("pic"),
        "first_frame.jpg": selected_page.get("first_frame"),
    }.items():
        if url:
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("http://"):
                url = "https://" + url[len("http://") :]
            try:
                (out_dir / key).write_bytes(request_bytes(url, referer=referer))
            except Exception as exc:
                print(f"warn: failed to download {key}: {exc}", file=sys.stderr)

    cid = selected_page["cid"]
    aid = data["aid"]
    play_url = (
        "https://api.bilibili.com/x/player/wbi/playurl?"
        f"avid={aid}&cid={cid}&bvid={urllib.parse.quote(bvid)}"
        "&qn=80&fnval=4048&fourk=1"
    )
    play = request_json(play_url, referer=referer)
    (out_dir / "playurl.json").write_text(
        json.dumps(play, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    subtitles = data.get("subtitle", {}).get("list") or []
    subtitle_results = []
    for idx, sub in enumerate(subtitles, 1):
        sub_url = sub.get("subtitle_url")
        if not sub_url:
            continue
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url
        sub_data = request_json(sub_url, referer=referer)
        path = out_dir / f"subtitle_{idx}_{sanitize_name(sub.get('lan_doc') or sub.get('lan') or 'sub')}.json"
        path.write_text(json.dumps(sub_data, ensure_ascii=False, indent=2), encoding="utf-8")
        subtitle_results.append(str(path))

    media_results = {}
    if args.media:
        dash = (play.get("data") or {}).get("dash") or {}
        videos = dash.get("video") or []
        audios = dash.get("audio") or []
        if videos:
            video = sorted(videos, key=lambda item: item.get("bandwidth", 0), reverse=True)[0]
            media_results["video_bytes"] = download_file(video["baseUrl"], out_dir / "video.m4s", referer)
        if audios:
            audio = sorted(audios, key=lambda item: item.get("bandwidth", 0), reverse=True)[0]
            media_results["audio_bytes"] = download_file(audio["baseUrl"], out_dir / "audio.m4s", referer)

    summary = {
        "bvid": bvid,
        "title": title,
        "page": page_number,
        "part": part_title,
        "owner": (data.get("owner") or {}).get("name"),
        "duration": selected_page.get("duration") or data.get("duration"),
        "pubdate": data.get("pubdate"),
        "cid": cid,
        "aid": aid,
        "out_dir": str(out_dir.resolve()),
        "subtitle_files": subtitle_results,
        **media_results,
    }
    (out_dir / "fetch_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
