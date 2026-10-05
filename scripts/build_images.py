"""Make web images for every project in content/projects.json.

    python3 scripts/build_images.py          # convert new images only
    python3 scripts/build_images.py --force  # redo everything that has a source

For each image with a "source" (TIFF, JPG, PNG, PSD composite) or "source_pdf"
(PDF page and panel bbox, rendered with Poppler), writes assets/work/<id>/<file>-800.webp and -1600.webp (long edge,
raster sources never upscaled, no metadata). Colour: embedded ICC -> sRGB; untagged CMYK uses
Adobe US Web Coated SWOP if installed, else macOS Generic CMYK.

Then records each image's size in content/images.json for scripts/build_site.py.
"""
import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "work"
SIZES = (800, 1600)
Image.MAX_IMAGE_PIXELS = None
SRGB = ImageCms.createProfile("sRGB")
CMYK_PROFILES = [
    Path("/Library/Application Support/Adobe/Color/Profiles/Recommended/USWebCoatedSWOP.icc"),
    Path("/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc"),
]


def pdf_panel(spec):
    """Render the actual PDF panel, preserving its clipping, colour and backdrop.

    Coordinates are PDF points measured from the page's top left. No automatic
    trimming or background removal is applied. Poppler also keeps vector art
    and transparency that would be lost by extracting a JPEG alone.
    """
    renderer = shutil.which("pdftoppm")
    if not renderer:
        homebrew = Path("/opt/homebrew/bin/pdftoppm")
        renderer = str(homebrew) if homebrew.exists() else None
    if not renderer:
        raise SystemExit("PDF panels require Poppler (pdftoppm). Install with brew install poppler.")
    path = ROOT / spec["path"]
    x0, y0, x1, y1 = spec["bbox"]
    if x1 <= x0 or y1 <= y0 or spec["page"] < 1:
        raise ValueError(f"Invalid PDF panel: {spec}")
    scale = max(SIZES) / max(x1 - x0, y1 - y0)
    # Round inward: never include a neighbouring caption or white page gutter.
    left, top = math.ceil(x0 * scale), math.ceil(y0 * scale)
    width, height = math.floor(x1 * scale) - left, math.floor(y1 * scale) - top
    with tempfile.TemporaryDirectory(prefix="htu-pdf-") as tmp:
        prefix = str(Path(tmp) / "panel")
        subprocess.run([renderer, "-f", str(spec["page"]), "-l", str(spec["page"]),
                        "-r", str(72 * scale), "-x", str(left), "-y", str(top),
                        "-W", str(width), "-H", str(height), "-singlefile", "-png",
                        str(path), prefix], check=True, capture_output=True)
        with Image.open(prefix + ".png") as im:
            return im.convert("RGB")


def source_key(img):
    spec = img.get("source_pdf")
    src = spec["path"] if spec else img.get("source")
    if not src:
        return None
    path = Path(src).expanduser() if src.startswith("~") else ROOT / src
    stamp = path.stat()
    value = [spec or src, stamp.st_size, stamp.st_mtime_ns, "webp-q88-v1"]
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:16]


def to_srgb(im):
    icc = im.info.get("icc_profile")
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(BytesIO(icc))
            return ImageCms.profileToProfile(im, src, SRGB, outputMode="RGB")
        except Exception:
            pass
    if im.mode == "CMYK":
        profile = next((p for p in CMYK_PROFILES if p.exists()), None)
        if profile:
            return ImageCms.profileToProfile(im, str(profile), SRGB, outputMode="RGB")
    return im.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    projects = json.loads((ROOT / "content/projects.json").read_text())["projects"]
    manifest_path = ROOT / "content/images.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    manifest = {}
    for p in projects:
        folder = OUT / p["id"]
        folder.mkdir(parents=True, exist_ok=True)
        entries = {}
        for img in p["images"]:
            stem = img["file"]
            targets = [folder / f"{stem}-{s}.webp" for s in SIZES]
            src = img.get("source")
            pdf = img.get("source_pdf")
            key = source_key(img)
            old_key = previous.get(p["id"], {}).get(stem, {}).get("source_key")
            if (src or pdf) and (args.force or key != old_key or not all(t.exists() for t in targets)):
                # "~/Documents/..." points at originals outside the repo; anything else is repo-relative
                if pdf:
                    im = pdf_panel(pdf)
                else:
                    path = Path(src).expanduser() if src.startswith("~") else ROOT / src
                    with Image.open(path) as original:
                        im = to_srgb(original)
                for size, target in zip(SIZES, targets):
                    copy = im.copy()
                    copy.thumbnail((size, size), Image.Resampling.LANCZOS)
                    copy.save(target, "WEBP", quality=88, method=6)
                print("made", p["id"], stem, im.size)
            missing = [t.name for t in targets if not t.exists()]
            if missing:
                raise SystemExit(f"{p['id']}/{stem}: missing {missing} and no source to make them from")
            with Image.open(targets[-1]) as big:
                w, h = big.size
            entries[stem] = {"w": w, "h": h}
            if key:
                entries[stem]["source_key"] = key
        manifest[p["id"]] = entries
    # drop web images nothing points at any more (originals are untouched)
    for folder in OUT.iterdir():
        if not folder.is_dir():
            continue
        used = {f"{stem}-{size}.webp" for stem in manifest.get(folder.name, {}) for size in SIZES}
        for f in folder.glob("*.webp"):
            if f.name not in used:
                f.unlink()
        if not any(folder.iterdir()):
            folder.rmdir()
    (ROOT / "content/images.json").write_text(json.dumps(manifest, indent=1))
    print("wrote content/images.json")


if __name__ == "__main__":
    main()
