"""Build the application-specific selection at /rising/.

Content lives in content/rising.json. The main site builder calls build(page,
PROJECTS); this file can also run on its own without rebuilding other pages.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def esc(value):
    return html.escape(str(value or ""), quote=True)


def bi(value):
    if isinstance(value, str):
        return esc(value)
    en = value.get("en", "")
    zh = value.get("zh") or en
    if en == zh:
        return esc(en)
    return f'<span class="en">{esc(en)}</span><span class="zh" lang="zh-Hant">{esc(zh)}</span>'


def build(page_func, projects):
    content = json.loads((ROOT / "content/rising.json").read_text(encoding="utf-8"))
    image_data = json.loads((ROOT / "content/images.json").read_text(encoding="utf-8"))
    project_by_id = {p["id"]: p for p in projects}
    selected = content["projects"]
    cards = []
    for number, item in enumerate(selected, 1):
        pid, stem = item["id"], item["image"]
        project = project_by_id[pid]
        source = next(image for image in project["images"] if image["file"] == stem)
        meta = image_data[pid][stem]
        w, h = meta["w"], meta["h"]
        thumb_width = round(w * min(1, 800 / max(w, h)))
        href = f"/work/{pid}/"
        loading = 'fetchpriority="high"' if number == 1 else 'loading="lazy" decoding="async"'
        date = f'<span class="rising-year">{esc(item["project_date"])}</span>' if item.get("project_date") else ""
        cards.append(f"""
<article class="rising-project" aria-labelledby="rising-title-{number}">
  <div class="rising-project-top"><span class="rising-number num">{number:02d}</span><p>{bi(item["relevance"])}</p>{date}</div>
  <a class="rising-image" href="{href}" aria-labelledby="rising-title-{number}">
    <img src="/assets/work/{pid}/{stem}-1600.webp" srcset="/assets/work/{pid}/{stem}-800.webp {thumb_width}w, /assets/work/{pid}/{stem}-1600.webp {w}w" sizes="(max-width: 700px) calc(100vw - 32px), calc(50vw - 48px)" width="{w}" height="{h}" alt="{esc(source["alt"])}" {loading}>
  </a>
  <div class="rising-project-copy">
    <h2 id="rising-title-{number}"><a href="{href}">{bi(item["title"])}<span class="rising-arrow" aria-hidden="true">↗</span></a></h2>
    <p class="rising-summary">{bi(item["summary"])}</p>
    <p class="rising-role"><span class="rising-role-label">{bi({"en": "Role", "zh": "角色"})}</span>{bi(item["role"])}</p>
    <a class="rising-case-link" href="{href}">{bi({"en": "View project", "zh": "查看專案"})}<span aria-hidden="true">↗</span></a>
  </div>
</article>""")

    title = bi(content["title"])
    # Keep the heading's line break intentional in both language variants.
    title = title.replace("Selected work for RISING", "Selected work<br>for RISING")
    title = title.replace("為 RISING 精選的作品", "為 RISING<br>精選的作品")
    body = f"""
<section class="rising-intro" aria-labelledby="rising-heading">
  <div class="rising-kicker"><span>Hao Wei Tu</span><span>{bi({"en": "Melbourne / Communication design", "zh": "墨爾本 / 視覺傳達設計"})}</span></div>
  <div class="rising-heading-row">
    <h1 id="rising-heading">{title}</h1>
    <div class="rising-intro-copy"><p>{bi(content["summary"])}</p><a href="#selected-work">{bi({"en": "Explore the selection", "zh": "瀏覽精選作品"})}<span aria-hidden="true">↓</span></a></div>
  </div>
</section>
<section class="rising-selection" id="selected-work" aria-label="Selected work">
  <div class="rising-selection-bar"><span>{bi({"en": "Selected projects", "zh": "精選專案"})}</span><span class="num">01—{len(selected):02d}</span></div>
  <div class="rising-projects">{"".join(cards)}</div>
</section>
<section class="rising-contact" aria-labelledby="rising-contact-heading">
  <h2 id="rising-contact-heading">{bi({"en": "Continue the conversation.", "zh": "期待進一步交流。"})}</h2>
  <div><a href="mailto:haowei@haoweitu.info">haowei@haoweitu.info <span aria-hidden="true">↗</span></a><a href="/work/">{bi({"en": "Explore all work", "zh": "瀏覽所有作品"})}<span aria-hidden="true">↗</span></a></div>
</section>"""

    output = page_func(
        "/rising/",
        "Selected work for RISING — Hao Wei Tu / HTU.",
        content["summary"]["en"],
        body,
        image=f'https://haoweitu.info/assets/work/{selected[0]["id"]}/{selected[0]["image"]}-1600.webp',
        body_cls="rising-page",
    )
    css_version = int((ROOT / "assets/rising.css").stat().st_mtime)
    output = output.replace(
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        '<meta name="robots" content="noindex, follow">',
    )
    output = output.replace("</head>", f'<link rel="stylesheet" href="/assets/rising.css?v={css_version}">\n</head>')
    destination = ROOT / "rising/index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    import build_site

    build_site.CSS_V = int((ROOT / "assets/site.css").stat().st_mtime)
    build_site.JS_V = int((ROOT / "assets/site.js").stat().st_mtime)
    build(build_site.page, build_site.PROJECTS)
    print("built rising selection")
