"""Build lightweight About gallery and portrait images, preserving the originals.

    python3 scripts/build_about_images.py

Reads gallery entries throughout content/about.json and me.jpg. Writes stable
480px previews, 1200px expanded images and content/about-images.json.
"""
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

from PIL import Image, ImageCms, ImageOps


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets/about"
MANIFEST = ROOT / "content/about-images.json"
SETTINGS = "about-webp-v1-q86-exif-srgb"


def gallery_sources(node):
    """Find gallery images even when a section is nested inside a list or object."""
    sources = set()
    if isinstance(node, dict):
        for item in node.get("gallery", []):
            if isinstance(item, dict) and item.get("src"):
                sources.add(item["src"])
        for value in node.values():
            sources.update(gallery_sources(value))
    elif isinstance(node, list):
        for value in node:
            sources.update(gallery_sources(value))
    return sources


def web_image(path):
    """Respect camera orientation and embedded color profiles before resizing."""
    with Image.open(path) as original:
        im = ImageOps.exif_transpose(original)
        alpha = im.convert("RGBA").getchannel("A") if "A" in im.getbands() or "transparency" in im.info else None
        profile = im.info.get("icc_profile")
        if profile:
            try:
                # CMYK and Lab profiles need their original color mode as input.
                color = im if im.mode in ("RGB", "CMYK", "LAB") else im.convert("RGB")
                im = ImageCms.profileToProfile(
                    color, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                    ImageCms.createProfile("sRGB"), outputMode="RGB",
                )
            except (ImageCms.PyCMSError, OSError, ValueError) as error:
                print(f"warning: {path.name}: invalid color profile ({error}); using RGB conversion")
                im = im.convert("RGB")
        else:
            im = im.convert("RGB")
        if alpha is not None:
            im.putalpha(alpha)
        return im.copy()


def main():
    about = json.loads((ROOT / "content/about.json").read_text(encoding="utf-8"))
    sources = gallery_sources(about) | {"me.jpg"}
    previous = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    rebuilt = 0
    for src in sorted(sources):
        parsed = urlsplit(src)
        if parsed.scheme or parsed.netloc:
            raise ValueError(f"About gallery source must be a local file: {src}")
        source = (ROOT / unquote(parsed.path).lstrip("/")).resolve()
        if not source.is_relative_to(ROOT) or not source.is_file():
            raise FileNotFoundError(f"Missing About image within the website: {src}")
        stem = hashlib.sha1(src.encode("utf-8")).hexdigest()[:12]
        urls = {size: f"/assets/about/{stem}-{size}.webp" for size in (480, 1200)}
        stat = source.stat()
        fingerprint = hashlib.sha256(
            f"{src}|{stat.st_size}|{stat.st_mtime_ns}|{SETTINGS}".encode("utf-8")
        ).hexdigest()[:20]
        cached = previous.get(src, {})
        if cached.get("source_key") == fingerprint and all((ROOT / url.lstrip("/")).is_file() for url in urls.values()):
            manifest[src] = cached
            continue
        im = web_image(source)
        dimensions = {}
        for size, url in urls.items():
            resized = im.copy()
            resized.thumbnail((size, size), Image.Resampling.LANCZOS)
            # Clear EXIF and source profiles; pixels have already been oriented
            # and converted to sRGB. thumbnail never upscales a smaller original.
            resized.info.clear()
            resized.save(ROOT / url.lstrip("/"), "WEBP", quality=86, method=6)
            dimensions[size] = resized.size
        manifest[src] = {
            "preview": urls[480],
            "full": urls[1200],
            "w": dimensions[1200][0],
            "h": dimensions[1200][1],
            "source_key": fingerprint,
        }
        rebuilt += 1
    output = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    if not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8") != output:
        MANIFEST.write_text(output, encoding="utf-8")
    print(f"About images: {len(sources)} sources, {rebuilt} rebuilt, {len(sources) - rebuilt} cached")


if __name__ == "__main__":
    main()
