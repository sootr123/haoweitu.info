"""Encode project films and silent loops, rebuilding changed sources automatically.

    python3 scripts/build_media.py
    python3 scripts/build_media.py --force --project endoaware

Use --ffmpeg /path/to/ffmpeg or HTU_FFMPEG if ffmpeg is not on PATH. Legacy
encodes are adopted once; --force refreshes them. Optional start/duration fields
select a short excerpt for index previews without modifying the source film.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "media"
MANIFEST = ROOT / "content" / "media.json"


def ffmpeg(override=None):
    exe = override or os.environ.get("HTU_FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        raise SystemExit("ffmpeg not found: set HTU_FFMPEG, use --ffmpeg, or install imageio-ffmpeg")


def source_path(src):
    return Path(src).expanduser() if src.startswith("~") else ROOT / src


def fingerprint(src, previous):
    path = source_path(src)
    stat = path.stat()
    identity = {"path": src, "bytes": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    if all(previous.get(k) == v for k, v in identity.items()) and previous.get("sha256"):
        return previous
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return {**identity, "sha256": digest.hexdigest()}


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode:
        raise SystemExit(result.stderr[-4000:])


def duration(ff, path):
    result = subprocess.run([ff, "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", result.stderr)
    if not match:
        raise SystemExit(f"Cannot read encoded video duration: {path}")
    return round(int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3]), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--project", action="append", help="Only encode this project (repeatable)")
    ap.add_argument("--ffmpeg", help="Path to an ffmpeg executable")
    args = ap.parse_args()
    projects = json.loads((ROOT / "content/projects.json").read_text())["projects"]
    unknown = set(args.project or []) - {p["id"] for p in projects}
    if unknown:
        raise SystemExit(f"Unknown projects: {', '.join(sorted(unknown))}")
    previous = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    manifest = {}
    ff = None
    for p in projects:
        selected = not args.project or p["id"] in args.project
        for m in p.get("media", []):
            if m["kind"] not in ("film", "loop"):
                continue
            folder = OUT / p["id"]
            folder.mkdir(parents=True, exist_ok=True)
            mp4, jpg = folder / f"{m['name']}.mp4", folder / f"{m['name']}.jpg"
            old = previous.get(p["id"], {}).get(m["name"], {})
            if not selected:
                if not mp4.exists() or not jpg.exists():
                    raise SystemExit(f"Missing media for {p['id']}; run without --project first")
                manifest.setdefault(p["id"], {})[m["name"]] = old
                continue
            source = fingerprint(m["source"], old.get("source", {}))
            trim = {"start": float(m.get("start", 0)), "duration": m.get("duration")}
            if trim["start"] < 0 or (trim["duration"] is not None and float(trim["duration"]) <= 0):
                raise SystemExit(f"Invalid clip timing for {p['id']}/{m['name']}")
            changed = bool(old.get("source")) and old["source"].get("sha256") != source["sha256"]
            changed = changed or (bool(old.get("trim")) and old["trim"] != trim)
            encode = args.force or not mp4.exists() or changed
            ff = ff or ffmpeg(args.ffmpeg)
            if encode:
                temp = mp4.with_name(f".{m['name']}.tmp.mp4")
                cmd = [ff, "-y"]
                if trim["start"]:
                    cmd += ["-ss", str(trim["start"])]
                cmd += ["-i", str(source_path(m["source"]))]
                if trim["duration"] is not None:
                    cmd += ["-t", str(trim["duration"])]
                cmd += ["-map", "0:v:0"]
                if m["kind"] == "film":
                    cmd += ["-map", "0:a:0?", "-vf", "scale='min(1280,iw)':-2", "-c:v", "libx264",
                            "-preset", "slow", "-crf", "24", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k"]
                else:
                    vf = "scale='if(gt(iw,ih),min(1200,iw),-2)':'if(gt(iw,ih),-2,min(1200,ih))',fps=30"
                    cmd += ["-vf", vf, "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p", "-an"]
                run(cmd + ["-movflags", "+faststart", str(temp)])
                temp.replace(mp4)
                print("made", p["id"], m["name"], f"{mp4.stat().st_size / 1e6:.1f} MB", flush=True)
            seconds = duration(ff, mp4) if encode or not old.get("duration") else old["duration"]
            poster_at = min(max(0, float(m.get("poster_at", 1))), max(0, seconds - 0.1))
            if encode or not jpg.exists() or old.get("poster_at") != poster_at:
                temp = jpg.with_name(f".{m['name']}.tmp.jpg")
                run([ff, "-y", "-ss", str(poster_at), "-i", str(mp4), "-frames:v", "1", "-q:v", "3", str(temp)])
                temp.replace(jpg)
            with Image.open(jpg) as im:
                entry = {"w": im.width, "h": im.height}
            entry.update(duration=seconds, bytes=mp4.stat().st_size, poster_at=poster_at, source=source, trim=trim)
            manifest.setdefault(p["id"], {})[m["name"]] = entry
    # Only generated derivatives are removed; source files are never changed.
    wanted = {(p["id"], m["name"]) for p in projects for m in p.get("media", []) if m["kind"] in ("film", "loop")}
    for folder in list(OUT.iterdir()) if OUT.exists() else []:
        for f in folder.glob("*.*"):
            if (folder.name, f.stem) not in wanted:
                f.unlink()
        if not any(folder.iterdir()):
            folder.rmdir()
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    print("wrote content/media.json")


if __name__ == "__main__":
    main()
