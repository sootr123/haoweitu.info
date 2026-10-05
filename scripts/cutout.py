"""Make transparent cut-outs for pictures marked "cut": true in content/projects.json.

    pip install "rembg[cpu]"          # once; runs locally, nothing is uploaded
    python3 scripts/cutout.py

Writes assets/work/<id>/<file>c-800.webp and -1600.webp next to the normal files.
Pictures that are a clean rectangle on a dark ground (posters) can set
"cut_trim": true to have the dark border trimmed instead of using AI.
Check every result by eye: dark covers on dark grounds can lose parts.
"""
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "work"


def trim(im):
    rgb = im.convert("RGB")
    px = rgb.load()
    w, h = rgb.size
    bright = lambda x, y: max(px[x, y]) > 48
    rows = [y for y in range(h) if sum(bright(x, y) for x in range(0, w, 4)) > w / 4 * .08]
    cols = [x for x in range(w) if sum(bright(x, y) for y in range(0, h, 4)) > h / 4 * .08]
    return rgb.crop((min(cols), min(rows), max(cols) + 1, max(rows) + 1)).convert("RGBA")


def main():
    projects = json.loads((ROOT / "content/projects.json").read_text())["projects"]
    session = None
    for p in projects:
        for img in p["images"]:
            if not img.get("cut"):
                continue
            targets = [OUT / p["id"] / f"{img['file']}c-{s}.webp" for s in (800, 1600)]
            if all(t.exists() for t in targets):
                continue
            src = Image.open(OUT / p["id"] / f"{img['file']}-1600.webp")
            if img.get("cut_trim"):
                cut = trim(src)
            else:
                from rembg import new_session, remove
                session = session or new_session("isnet-general-use")
                cut = remove(src.convert("RGB"), session=session, post_process_mask=True)
                cut = cut.crop(cut.getchannel("A").point(lambda a: 255 if a > 20 else 0).getbbox())
            for size, t in zip((800, 1600), targets):
                c = cut.copy()
                c.thumbnail((size, size), Image.Resampling.LANCZOS)
                c.save(t, "WEBP", quality=86, method=6)
            print("cut", p["id"], img["file"])


if __name__ == "__main__":
    main()
