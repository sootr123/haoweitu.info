"""Build every page of haoweitu.info from content/*.json.

    python3 scripts/build_images.py   # only when images were added or changed
    python3 scripts/build_site.py

Writes index.html, work/index.html, work/<id>/index.html, about/index.html,
404.html and sitemap.xml. Edit content/, not the generated HTML.
"""
import datetime as dt
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://haoweitu.info"
CSS_V = JS_V = None  # filled with file mtimes so browsers pick up new versions

C = lambda name: json.loads((ROOT / "content" / name).read_text(encoding="utf-8"))
PROJECTS = C("projects.json")["projects"]
IMAGES = C("images.json")
LAYOUTS = C("project-layouts.json")["projects"]
INDEX_LAYOUTS = C("index-layouts.json")["projects"]
ABOUT = C("about.json")
ABOUT_IMAGES = C("about-images.json") if (ROOT / "content/about-images.json").exists() else {}
PERSON = C("person.jsonld.json")
MEDIA = C("media.json") if (ROOT / "content/media.json").exists() else {}

FILTERS = [
    ("packaging", "Packaging", "包裝"),
    ("campaign", "Campaign", "倡議"),
    ("digital", "Digital", "數位"),
    ("identity", "Identity", "識別"),
    ("exhibition", "Exhibition", "展覽"),
    ("book", "Book", "書籍"),
    ("poster", "Poster", "海報"),
    ("research", "Research", "研究"),
    ("object", "Object", "物件"),
]
LINKS_FOOT = ["Instagram", "LinkedIn", "Behance", "Threads"]
EMAIL = "haowei@haoweitu.info"


# ── helpers ────────────────────────────────────────────
def esc(s):
    return html.escape(s or "", quote=True)


def bi(d, raw=False):
    """{en, zh} -> paired spans; collapses to one string when both match."""
    if d is None:
        return ""
    if isinstance(d, str):
        return d if raw else esc(d)
    en, zh = d.get("en", ""), d.get("zh", "") or d.get("en", "")
    f = (lambda s: s) if raw else esc
    if en == zh:
        return f(en)
    return f'<span class="en">{f(en)}</span><span class="zh" lang="zh-Hant">{f(zh)}</span>'


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def pad(n):
    return f"{n:02d}"


def img_meta(pid, stem):
    m = IMAGES[pid][stem]
    w, h = m["w"], m["h"]
    long = max(w, h)
    s = min(1, 800 / long)
    return w, h, round(w * s), round(h * s)


def img_url(pid, stem, size=1600):
    return f"/assets/work/{pid}/{stem}-{size}.webp"


def img_tag(p, im, sizes, lazy=True, cls=""):
    pid, stem = p["id"], im["file"]
    w, h, w8, _ = img_meta(pid, stem)
    srcset = f'{img_url(pid, stem, 800)} {w8}w, {img_url(pid, stem)} {w}w'
    load = ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high"'
    c = f' class="{cls}"' if cls else ""
    tag = (f'<img{c} src="{img_url(pid, stem)}" srcset="{srcset}" sizes="{sizes}" '
            f'width="{w}" height="{h}" alt="{esc(im["alt"])}"{load}>')
    if im.get("display_crop"):
        x0, y0, x1, y1 = im["display_crop"]
        cw, ch = x1 - x0, y1 - y0
        positioning = f'width:{100 / cw:g}%;left:{-100 * x0 / cw:g}%;top:{-100 * y0 / ch:g}%'
        tag = tag.replace('<img', f'<img style="{positioning}"', 1)
        return f'<span class="image-window" style="aspect-ratio:{w * cw / (h * ch):.6f}">{tag}</span>'
    return tag


def cover(p):
    return next(i for i in p["images"] if i["file"] == p["cover"])


def short(p):
    return p.get("short") or p["title"]


def year(p):
    return str(p["year"]) if p.get("year") else ""


def link(label):
    return next(l for l in ABOUT["links"] if l["label"] == label)


# ── page frame ─────────────────────────────────────────
def page(path, title, desc, body, *, image=None, jsonld=None, current=None, og_type="website", body_cls=""):
    url = SITE + path
    og_img = image or SITE + img_url(PROJECTS[0]["id"], PROJECTS[0]["cover"])
    nav = [("/work/", "Work", "作品", "work"), ("/about/", "About", "關於", "about"), ("#contact", "Contact", "聯絡", None)]
    here = ' aria-current="page"'
    count = f"<sup>{len(PROJECTS)}</sup>"
    nav_html = "".join(
        f'<a href="{h}"{here if key and key == current else ""}>'
        f'<span class="en">{en}</span><span class="zh">{zh}</span>{count if key == "work" else ""}</a>'
        for h, en, zh, key in nav)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    foot_links = "".join(f'<a href="{esc(link(n)["href"])}" rel="noopener" target="_blank">{n}</a>' for n in LINKS_FOOT)
    return f"""<!doctype html>
<html lang="en" data-lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}">
<link rel="alternate" hreflang="zh-Hant" href="{url}?lang=zh">
<link rel="alternate" hreflang="x-default" href="{url}">
<meta name="author" content="Hao Wei Tu">
<meta name="theme-color" content="#f0efea">
<meta name="robots" content="index, follow, max-image-preview:large">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="HTU. — Hao Wei Tu 杜浩瑋">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_img}">
<meta property="og:locale" content="en_AU">
<meta property="og:locale:alternate" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="sitemap" type="application/xml" href="/sitemap.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=Noto+Sans+TC:wght@400;500;700&family=IBM+Plex+Mono:wght@400&display=swap">
<link rel="stylesheet" href="/assets/site.css?v={CSS_V}">
<script>try{{var l=new URLSearchParams(location.search).get("lang")||localStorage.getItem("lang");if(l==="zh"){{document.documentElement.dataset.lang="zh";document.documentElement.lang="zh-Hant"}}}}catch(e){{}}</script>
{ld}
</head>
<body class="{body_cls}">
<a class="skip" href="#main"><span class="en">Skip to content</span><span class="zh">跳到內容</span></a>
<header class="hd grid">
<a class="hd-logo" href="/" aria-label="HTU. — Hao Wei Tu, home">HTU.</a>
<nav class="hd-nav" aria-label="Main">{nav_html}</nav>
<div class="hd-lang" role="group" aria-label="Language"><button type="button" data-set-lang="en" aria-pressed="true">EN</button><span class="sep">/</span><button type="button" data-set-lang="zh" aria-pressed="false" lang="zh-Hant">中<span class="full">文</span></button></div>
</header>
<main id="main">
{body}
</main>
<footer class="ft" id="contact">
<a href="mailto:{EMAIL}">{EMAIL}</a>
<span class="ft-links">{foot_links}</span>
<span class="ft-clock num"><span><span class="en">Melbourne</span><span class="zh">墨爾本</span> <time data-tz="Australia/Melbourne"></time></span> <span><span class="en">Taipei</span><span class="zh">台北</span> <time data-tz="Asia/Taipei"></time></span></span>
<span>© {dt.date.today().year} HTU.</span>
</footer>
<div class="peek" aria-hidden="true"><img alt=""></div>
<script src="/assets/site.js?v={JS_V}" defer></script>
</body>
</html>
"""


def write(rel, text):
    f = ROOT / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8")


# ── shared bits ────────────────────────────────────────
def ratio(p, stem):
    w, h, *_ = img_meta(p["id"], stem)
    im = next(im for im in p["images"] if im["file"] == stem)
    if im.get("display_crop"):
        x0, y0, x1, y1 = im["display_crop"]
        return w * (x1 - x0) / (h * (y1 - y0))
    return w / h


def card_image(p, wide=False):
    """The cover, unless a wide slot needs a landscape picture and the project has one."""
    c = cover(p)
    if wide and ratio(p, c["file"]) < 1.3:
        land = [i for i in p["images"] if ratio(p, i["file"]) >= 1.3]
        if land:
            return land[0]
    return c


def index_rows(with_i=False):
    out = []
    for n, p in enumerate(PROJECTS):
        c = cover(p)
        client = ""
        if p.get("client"):
            # the index only has room for the main name; the project page has the rest
            client = bi({k: re.split(r",\s*with |，與|（", v)[0] for k, v in p["client"].items()})
        di = f' data-i="{n}"' if with_i and p.get("selected_pdf") else ""
        out.append(
            f'<li class="idx-row" style="--accent:{p["accent"]}" data-filters="{" ".join(p["filters"])}"{di} '
            f'data-peek="{img_url(p["id"], c["file"], 800)}">'
            f'<a href="/work/{p["id"]}/"><span class="idx-num num">{pad(n + 1)}</span>'
            f'<span class="idx-title">{bi(short(p))}</span>'
            f'<span class="idx-disc">{bi(p["discipline"])}</span>'
            f'<span class="idx-client">{client}</span>'
            f'<span class="idx-year num">{year(p)}</span></a></li>')
    return "\n".join(out)


# ── home ───────────────────────────────────────────────
def home_features():
    articles = C("press.json")["articles"]
    windows = []
    for article in articles:
        key = "ca" if article["id"] == "communication-arts" else "swinburne"
        screenshots = article.get("images") or [{"src": article["image"], "width": article["width"], "height": article["height"], "alt": f'{article["publisher"]} article — website preview'}]
        shots = "".join(f'<img src="{esc(im["src"])}" width="{im["width"]}" height="{im["height"]}" loading="lazy" decoding="async" alt="{esc(im["alt"])}">' for im in screenshots)
        content = (f'<a class="window-shots" href="{esc(article["url"])}" target="_blank" rel="noopener" aria-label="Read the original {esc(article["publisher"])} article">{shots}</a>'
                   f'<div class="window-article-copy"><h3>{bi(article["title"])}</h3><p>{bi(article["description"])}</p>'
                   f'<a href="{esc(article["url"])}" target="_blank" rel="noopener"><span class="en">Read the original ↗</span><span class="zh">閱讀原文 ↗</span></a></div>')
        windows.append(desktop_window(key, article["publisher"], article["url"], content))
    yt = re.search(r"embed/([\w-]+)", ABOUT["bio"].get("video") or "")
    if yt:
        vid = yt.group(1)
        content = f'''<div class="youtube-mobile">
<div class="youtube-masthead"><span class="youtube-symbol" aria-hidden="true">▶</span><b>YouTube</b></div>
<div class="youtube-player"><iframe src="https://www.youtube-nocookie.com/embed/{vid}?rel=0" title="Generative AI as a human-centered visualisation tool — Hao Wei Tu, TEDxSwinburne University" loading="lazy" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>
<div class="youtube-details"><span class="lbl">TEDxSwinburne University</span><h3>Generative AI as a human-centered visualisation tool</h3><p class="youtube-byline">Hao Wei Tu · TEDx Talks</p><p><span class="en">Images can help us discuss ideas we cannot yet see. A talk on generative AI, visual communication and the conversations an image can begin.</span><span class="zh">圖像能否幫助我們討論還看不見的概念？談生成式 AI、視覺溝通，以及一張圖像如何成為對話的起點。</span></p><a href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener"><span class="en">Watch on YouTube ↗</span><span class="zh">在 YouTube 觀看 ↗</span></a></div></div>'''
        windows.append(desktop_window("tedx", "TEDxSwinburne", f"https://www.youtube.com/watch?v={vid}", content))
    script = ROOT / "assets/windows.js"
    version = int(script.stat().st_mtime) if script.exists() else 0
    return f'''<aside class="home-desktop" id="reading" aria-label="Articles and a talk">
<nav class="window-dock" aria-label="Open a window"><button type="button" data-window-open="ca">Communication Arts</button><button type="button" data-window-open="swinburne">Swinburne</button><button type="button" data-window-open="tedx">TEDx / YouTube</button></nav>
<div class="window-workspace" data-window-workspace>{"".join(windows)}</div>
</aside><script src="/assets/windows.js?v={version}" defer></script>'''


def desktop_window(key, title, url, content):
    domain = urlsplit(url).netloc.removeprefix("www.")
    return f'''<article class="floating-window" data-window="{key}" aria-label="{esc(title)} window">
<header class="window-titlebar" data-window-drag tabindex="0" role="group" aria-label="Move {esc(title)} window"><span class="window-title">{esc(title)}</span><div class="window-controls"><a data-window-external href="{esc(url)}" target="_blank" rel="noopener" aria-label="Open {esc(title)} in a new tab" title="Open original website">□</a><button type="button" data-window-close aria-label="Close {esc(title)} window" title="Close">×</button></div></header>
<a class="window-address" href="{esc(url)}" target="_blank" rel="noopener"><span>{esc(domain)}</span><span aria-hidden="true">↗</span></a>
<div class="window-content" tabindex="0" role="region" aria-label="{esc(title)} content">{content}</div>
<button class="window-resize" data-window-resize aria-label="Resize {esc(title)} window" title="Drag to resize"></button>
</article>'''


def build_home():
    home = C("home.json")
    body = f"""
<section class="hero" aria-label="HTU.">
<div class="hero-top"><div class="hero-intro"><span class="lbl">{bi(home['intro']['eyebrow'])}</span><p class="lede">{bi(home['intro']['body'])}</p></div></div>
<h1 class="mark" aria-label="HTU. — Hao Wei Tu 杜浩瑋"><span class="mark-type" aria-hidden="true">HTU<span class="mark-point"></span></span><span class="ground-lens" aria-hidden="true"></span></h1>
<div class="hero-bar grid"><span class="lbl"><span class="en">Melbourne / Taipei</span><span class="zh">墨爾本／台北</span></span><a class="hero-down" href="/work/"><span class="en">View selected work</span><span class="zh">瀏覽作品選輯</span><span aria-hidden="true">↗</span></a></div>
</section>
<section class="home-note grid" aria-label="About the practice">
<p><span class="en">Identity, books, exhibitions and design research. From the construction of a letter to the way an image is read in space.</span><span class="zh">品牌識別、書籍、展覽與設計研究。從一個字母的結構，到圖像在空間中被觀看的方式。</span></p>
<a href="/about/"><span class="en">About Hao Wei Tu<br>Biography, awards &amp; research ↗</span><span class="zh">關於杜浩瑋<br>簡歷、獎項與研究 ↗</span></a>
</section>
{home_features()}
"""
    ld = json.loads(json.dumps(PERSON))
    for node in ld.get("@graph", []):
        if node.get("@type") == "ProfilePage":
            node["dateModified"] = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    write("index.html", page(
        "/", "HTU. — Hao Wei Tu 杜浩瑋, communication designer & researcher",
        "Portfolio of Hao Wei Tu (杜浩瑋): identities, books, exhibitions and research between Melbourne and Taipei.",
        body, jsonld=ld, og_type="profile", body_cls="home"))


# ── work index ─────────────────────────────────────────
def work_row(p):
    """An authored group of two to four previews, preserving each image's ratio."""
    plan = INDEX_LAYOUTS[p["id"]]
    panels = []
    for item in plan["items"]:
        if item["kind"] == "loop":
            media = next(m for m in p["media"] if m.get("name") == item["name"])
            tag, r = loop_tag(p, media)
        elif item["kind"] == "custom":
            im = item if item.get("src") else p["index_image"]
            r = im["w"] / im["h"]
            tag = f'<img src="{esc(im["src"])}" width="{im["w"]}" height="{im["h"]}" alt="{esc(im["alt"])}" loading="lazy" decoding="async">'
        else:
            im = next(im for im in p["images"] if im["file"] == item["file"])
            r = ratio(p, im["file"])
            tag = img_tag(p, im, "(max-width: 720px) 46vw, 28vw")
        panels.append(f'<span style="flex:{r:.4f}">{tag}</span>')
    tags = ", ".join(x for x in [p["discipline"]["en"], year(p)] if x)
    tags_zh = "，".join(x for x in [p["discipline"]["zh"], year(p)] if x)
    return (f'<li class="w-row" id="{p["id"]}" data-filters="{" ".join(p["filters"])}"><a href="/work/{p["id"]}/">'
            f'<span class="w-text"><span class="w-title">{bi(short(p))}</span>'
            f'<span class="w-tags mono">{bi({"en": tags, "zh": tags_zh})}</span></span>'
            f'<span class="w-strip" data-count="{len(panels)}" style="--group-width:{plan["width"] * 100:g}%;--group-max:{plan.get("max_width",300)}px">{"".join(panels)}</span></a></li>')


def build_work():
    counts = {k: sum(k in p["filters"] for p in PROJECTS) for k, *_ in FILTERS}
    filt = [f'<button type="button" data-filter="all" aria-pressed="true"><span class="en">All</span><span class="zh">全部</span></button>']
    filt += [f'<button type="button" data-filter="{k}" aria-pressed="false"><span class="en">{en}</span><span class="zh">{zh}</span></button>'
             for k, en, zh in sorted(FILTERS, key=lambda f: -counts[f[0]]) if counts[k]]
    rows = "\n".join(work_row(p) for p in PROJECTS)
    body = f"""
<div class="page">
<header class="w-header"><h1 class="w-hd"><span class="en">Selected work</span><span class="zh">作品選輯</span></h1><p class="w-intro"><span class="en">Identity, editorial, exhibitions<br>and design research. 2017–now.</span><span class="zh">品牌識別、書籍、展覽與設計研究。<br>2017 至今。</span></p></header>
<div class="w-tools mono" role="group" aria-label="Filter">{"".join(filt)}<button type="button" class="motion-toggle" data-pause-previews aria-pressed="false" aria-label="Pause motion previews / 暫停動態預覽"><span class="en">Pause motion</span><span class="zh">暫停動態</span></button></div>
<ul class="w-list" data-view="index">
{rows}
</ul>
</div>
"""
    write("work/index.html", page(
        "/work/", "Work — HTU. Hao Wei Tu 杜浩瑋",
        "Selected work by Hao Wei Tu: brand identities, book covers, exhibition campaigns, packaging and design research.",
        body, current="work", body_cls="work"))


# ── project pages ──────────────────────────────────────
def loop_tag(p, m):
    meta = MEDIA.get(p["id"], {}).get(m["name"])
    if not meta:
        return None, 1
    base = f"/assets/media/{p['id']}/{m['name']}"
    w, h = meta["w"], meta["h"]
    tag = (f'<video class="loop" autoplay muted loop playsinline preload="none" poster="{base}.jpg" width="{w}" height="{h}" '
           f'aria-label="{esc(m["title"]["en"])}"><source src="{base}.mp4" type="video/mp4"></video>')
    return tag, w / h


def case_image(p, file, lazy=True):
    im = next(im for im in p["images"] if im["file"] == file)
    return (f'<figure class="case-figure">{img_tag(p, im, "(max-width: 720px) 92vw, 1100px", lazy=lazy)}'
            f'<figcaption class="mono">{bi(im.get("caption", im["alt"]))}</figcaption></figure>')


def case_sections(p, plan):
    result = []
    for n, section in enumerate(plan["sections"]):
        layout = section["layout"]
        if "images" in section:
            media_class = f"case-media layout-{layout}"
            style = ""
            if section.get("equal_height"):
                # Widths follow the originals' aspect ratios so their heights match.
                columns = " ".join(f"minmax(0,{ratio(p, file):.8f}fr)" for file in section["images"])
                media_class += " equal-height"
                style = f' style="--case-columns:{columns}"'
            visual = f'<div class="{media_class}"{style}>{"".join(case_image(p, file) for file in section["images"])}</div>'
        else:
            ids = section.get("media", [])
            entries = [m for key in ids for m in p.get("media", []) if key == m.get("name", m.get("id"))]
            if layout == "film":
                visual = films({**p, "media": entries}, img_url(p["id"], p["cover"]))
            else:
                cards = []
                for m in entries:
                    tag, r = loop_tag(p, m)
                    if tag:
                        cards.append(f'<figure class="case-figure">{tag}<figcaption class="mono">{bi(m["title"])}</figcaption></figure>')
                columns = "four" if len(cards) == 4 else "pair" if len(cards) == 2 else "wide"
                visual = f'<div class="case-media layout-{columns}">{"".join(cards)}</div>' if cards else ""
        if not visual:
            continue
        text = f'<p>{bi(section["text"])}</p>' if section.get("text") else ""
        heading = f'<h2 id="section-{n}">{bi(section["heading"])}</h2>' if section.get("heading") else ""
        result.append(f'<section class="case-section"><div class="case-copy">{heading}{text}</div>{visual}</section>')
    return "\n".join(result)


def films(p, poster):
    out = []
    for m in p.get("media", []):
        title = bi(m["title"])
        if m["kind"] == "film":
            if not MEDIA.get(p["id"], {}).get(m["name"]):
                continue
            src = f"/assets/media/{p['id']}/{m['name']}.mp4"
            poster = f"/assets/media/{p['id']}/{m['name']}.jpg"
            poster += f'?v={int((ROOT / poster.lstrip("/")).stat().st_mtime)}'
            out.append(f'<figure class="film rv"><button class="film-play" type="button" data-video="{src}" aria-label="Play: {esc(m["title"]["en"])}" '
                       f'style="background-image:url(\'{poster}\')"><span class="film-btn" aria-hidden="true"></span>'
                       f'<span class="film-label">{title}</span></button>'
                       + (f'<figcaption class="mono"><a href="{esc(m["watch_url"])}" target="_blank" rel="noopener">YouTube ↗</a></figcaption>' if m.get("watch_url") else "") + '</figure>')
        elif m["kind"] in ("youtube", "behance"):
            src = (f"https://www.youtube-nocookie.com/embed/{m['id']}?autoplay=1&rel=0" if m["kind"] == "youtube"
                   else f"https://www-ccv.adobe.io/v1/player/ccv/{m['id']}/embed?api_key=behance1&bgcolor=%23191919")
            host = "YouTube" if m["kind"] == "youtube" else "Behance"
            out.append(f'<figure class="film rv"><button class="film-play" type="button" data-src="{src}" aria-label="Play: {esc(m["title"]["en"])}" '
                       f'style="background-image:url(\'{poster}\')"><span class="film-btn" aria-hidden="true"></span>'
                       f'<span class="film-label">{title}<span class="mute"> — {host}</span></span></button></figure>')
    if not out:
        return ""
    return f'<section class="films" aria-label="Films">{"".join(out)}</section>'


def build_projects():
    total = len(PROJECTS)
    for n, p in enumerate(PROJECTS):
        nxt = PROJECTS[(n + 1) % total]
        prv = PROJECTS[n - 1]
        c = cover(p)
        meta = [("Discipline", "類型", bi(p["discipline"]))]
        if p.get("client"):
            meta.append(("Client / context", "客戶／脈絡", bi(p["client"])))
        if year(p):
            meta.append(("Year", "年份", f'<span class="num">{year(p)}</span>'))
        meta_html = "".join(f'<div><dt><span class="en">{en}</span><span class="zh">{zh}</span></dt><dd>{v}</dd></div>' for en, zh, v in meta)
        paras = (
            "".join(f'<p class="en">{esc(t)}</p>' for t in p["description"]["en"]) +
            "".join(f'<p class="zh" lang="zh-Hant">{esc(t)}</p>' for t in p["description"]["zh"]))
        credits = "".join(f"<li>{bi(cr)}</li>" for cr in p["credits"])
        side = f'<div class="side-block"><h2><span class="en">Credits</span><span class="zh">團隊</span></h2><ul>{credits}</ul></div>'
        if p.get("recognition"):
            items = []
            for r in p["recognition"]:
                label = bi({"en": r["en"], "zh": r["zh"]})
                label = f'<a href="{esc(r["href"])}" rel="noopener" target="_blank">{label}</a>' if r.get("href") else label
                items.append(f'<li><span class="yr num">{r["year"]}</span><span>{label}</span></li>')
            side += f'<div class="side-block"><h2><span class="en">Recognition</span><span class="zh">獲獎</span></h2><ul class="rec">{"".join(items)}</ul></div>'
        plan = LAYOUTS[p["id"]]
        lead = plan["lead"]
        tags = ", ".join(x for x in [p["discipline"]["en"], year(p)] if x)
        tags_zh = "，".join(x for x in [p["discipline"]["zh"], year(p)] if x)
        body = f"""
<article class="page proj">
<header class="p-head grid"><h1 class="p-title">{bi(short(p))}</h1><p class="p-tags mono">{bi({"en": tags, "zh": tags_zh})}</p></header>
<div class="case-lead layout-{lead['width']}">{case_image(p, lead['image'], lazy=False)}</div>
<section class="p-text grid">
<div class="p-body">{paras}</div>
<aside class="p-side"><dl class="p-meta">{meta_html}</dl>{side}</aside>
</section>
{case_sections(p, plan)}
<nav class="p-next"><a href="/work/"><span class="en">Index</span><span class="zh">作品列表</span></a><a href="/work/{nxt['id']}/" rel="next"><span class="en">Next</span><span class="zh">下一件</span>: {bi(short(nxt))} →</a></nav>
</article>
"""
        desc = p["description"]["en"][0]
        desc = desc if len(desc) < 300 else desc[:297].rsplit(" ", 1)[0] + "…"
        ld = {
            "@context": "https://schema.org", "@type": "CreativeWork",
            "name": p["title"]["en"], "alternateName": p["title"]["zh"] if p["title"]["zh"] != p["title"]["en"] else None,
            "url": f"{SITE}/work/{p['id']}/", "image": SITE + img_url(p["id"], c["file"]),
            "description": " ".join(p["description"]["en"]), "genre": p["discipline"]["en"],
            "creator": {"@id": f"{SITE}/#person"},
        }
        if p.get("year"):
            ld["dateCreated"] = str(p["year"])
        ld = {k: v for k, v in ld.items() if v is not None}
        write(f"work/{p['id']}/index.html", page(
            f"/work/{p['id']}/", f"{p['title']['en']} — HTU. Hao Wei Tu 杜浩瑋", desc, body,
            image=SITE + img_url(p["id"], c["file"]), jsonld=ld, current="work", og_type="article", body_cls="project"))


# ── about ──────────────────────────────────────────────
def about_asset(src, size="full"):
    return ABOUT_IMAGES.get(src, {}).get(size) or "/" + quote(src)


def peek_attribute(gallery):
    return f' data-peek="{esc(about_asset(gallery[0]["src"], "preview"))}"' if gallery else ""


def gallery_html(gallery):
    if not gallery:
        return ""
    pics = "".join(f'<a href="{esc(about_asset(g["src"]))}" target="_blank" rel="noopener"><img src="{esc(about_asset(g["src"]))}" alt="{esc(g["alt"])}" loading="lazy"></a>' for g in gallery)
    return f'<div class="row-pics">{pics}</div>'


def row_html(r):
    title = strip_tags(r["title"]["en"]), strip_tags(r["title"]["zh"])
    t = bi({"en": title[0], "zh": title[1]})
    main = f'<a href="{esc(r["href"])}" rel="noopener" target="_blank">{t}</a>' if r.get("href") else t
    sub = f'<span class="row-sub">{bi(r["sub"], raw=True)}</span>' if r.get("sub") else ""
    res = esc(r.get("result") or "")
    more = ""
    if r.get("items"):
        lis = []
        for it in r["items"]:
            nm = {"en": strip_tags(it["name"]["en"]), "zh": strip_tags(it["name"]["zh"])}
            nm_html = bi(nm)
            if it.get("href"):
                nm_html = f'<a href="{esc(it["href"])}" rel="noopener" target="_blank">{nm_html}</a>'
            fields = f'<span class="num mute">{esc(it["year"])}</span><span>{nm_html}</span><span>{bi(it["result"], raw=True)}</span>'
            if it.get("gallery"):
                lis.append(f'<li class="row-subitem"><details><summary class="row-subitem-line"{peek_attribute(it["gallery"])}>{fields}<span class="row-tog" aria-hidden="true"></span></summary>{gallery_html(it["gallery"])}</details></li>')
            else:
                lis.append(f'<li>{fields}</li>')
        more += f'<ul>{"".join(lis)}</ul>'
    if r.get("gallery"):
        more += gallery_html(r["gallery"])
    if more:
        # titles that are links stay clickable inside the summary
        preview_gallery = r.get("gallery") or next((it["gallery"] for it in r.get("items", []) if it.get("gallery")), [])
        return (f'<li class="row"><details><summary class="row-line"{peek_attribute(preview_gallery)}><span class="row-yr num">{esc(r["year"])}</span>'
                f'<span class="row-main"><b>{main}</b>{sub}</span><span class="row-res">{res}</span><span class="row-tog" aria-hidden="true"></span></summary>'
                f'<div class="row-more">{more}</div></details></li>')
    return (f'<li class="row"><div class="row-line"><span class="row-yr num">{esc(r["year"])}</span>'
            f'<span class="row-main"><b>{main}</b>{sub}</span><span class="row-res">{res}</span><span></span></div></li>')


def press_row(r):
    t = {"en": strip_tags(r["title"]["en"]), "zh": strip_tags(r["title"]["zh"])}
    if r.get("items"):
        items = [{"year": "", "name": it["title"], "href": it["href"], "result": it["pub"]} for it in r["items"]]
        sub = r.get("count")
        return row_html({"year": r["year"], "title": t, "href": None, "sub": sub, "result": "", "items": items, "gallery": r.get("gallery")})
    return row_html({"year": r["year"], "title": t, "href": r.get("href"), "sub": None,
                     "result": strip_tags((r.get("pub") or {}).get("en", "")), "items": [], "gallery": r.get("gallery")})


def build_about():
    b, ed = ABOUT["bio"], ABOUT["editorial"]
    yt = re.search(r"embed/([\w-]+)", b.get("video") or "")
    vid = yt.group(1) if yt else ""
    video = (f'<div class="ab-talk-player"><button class="video-btn" type="button" data-yt="{vid}" '
             f'aria-label="Play: TEDxSwinburne talk by Hao Wei Tu" '
             f'style="background-image:url(\'https://i.ytimg.com/vi/{vid}/hqdefault.jpg\')">'
             f'<span class="ab-play">▶ <span class="en">Watch the talk</span><span class="zh">觀看演講</span></span></button></div>') if vid else ""

    def section_heading(en, zh, note=""):
        return f'<header class="ab-section-heading"><h2>{bi({"en": en, "zh": zh})}</h2>{note}</header>'

    def disclosure(en, zh, body, cls=""):
        return (f'<details class="ab-disclosure {cls}"><summary>{bi({"en": en, "zh": zh})}'
                f'<span class="ab-plus" aria-hidden="true"></span></summary><div class="ab-disclosure-body">{body}</div></details>')

    def record(r):
        href = r.get("href") or next((it.get("href") for it in r.get("items", []) if it.get("href")), None)
        title = bi({lang: strip_tags(r["title"][lang]) for lang in ("en", "zh")})
        title = f'<a href="{esc(href)}" target="_blank" rel="noopener">{title}<span aria-hidden="true"> ↗</span></a>' if href else title
        fields = (f'<span class="num mute">{esc(r["year"])}</span>'
                  f'<span>{title}<span class="ab-record-result">{esc(r.get("result", ""))}</span></span>')
        if r.get("gallery"):
            return (f'<li class="ab-record"><details><summary class="ab-record-line"{peek_attribute(r["gallery"])}>{fields}'
                    f'<span class="row-tog" aria-hidden="true"></span></summary>{gallery_html(r["gallery"])}</details></li>')
        return f'<li class="ab-record"><div class="ab-record-line">{fields}</div></li>'

    selected = [ABOUT["recognition"][r["group"]]["rows"][r["row"]] for r in ed["selected_recognition"]]
    archive = "".join(f'<div class="ab-archive-group"><h3>{bi(g["title"], raw=True)}</h3>'
                      f'<ul class="rows">{"".join(row_html(r) for r in g["rows"])}</ul></div>'
                      for g in ABOUT["recognition"][2:4])
    awards_more = disclosure("Awards & exhibition archive", "更多獎項與展覽", archive)
    service = [r for r in ABOUT["recognition"][4]["rows"] if r.get("result") != "Finalist"]
    service_rows = '<ul class="rows">' + "".join(row_html(r) for r in service[:3]) + '</ul>'
    service_more = disclosure("Earlier teaching, talks & research", "更多教學、演講與研究經歷", '<ul class="rows">' + "".join(row_html(r) for r in service[3:]) + '</ul>')
    all_bio = f'<p>{bi(b["lede"], raw=True)}</p>' + "".join(f'<p>{bi(p, raw=True)}</p>' for p in b["paragraphs"])
    bio_more = disclosure("Full biography", "完整簡歷", all_bio, "ab-full-bio")

    client_links = {"Downtown Grocer": "downtown-grocer", "Fishmonger": "fishmonger", "HNZ Constructions": "hnz-constructions"}
    clients = []
    for c in ABOUT["clients"]:
        name = strip_tags(c["name"])
        title = f'<a href="/work/{client_links[name]}/">{esc(name)} ↗</a>' if name in client_links else esc(name)
        clients.append(f'<li>{title}</li>')

    features = []
    for i in ed["selected_press"]:
        r = ABOUT["press"][i]
        feature_gallery = disclosure("View images", "查看圖片", gallery_html(r.get("gallery"))) if r.get("gallery") else ""
        features.append(f'<article><a class="ab-press-link" href="{esc(r["href"])}" target="_blank" rel="noopener"{peek_attribute(r.get("gallery"))}>'
                        f'<span class="ab-press-meta">{bi(r["pub"])} <span class="num">{esc(r["year"])}</span></span>'
                        f'<span class="ab-press-title">{bi(r["title"], raw=True)}</span><span class="ab-out" aria-hidden="true">↗</span></a>{feature_gallery}</article>')
    press_more = disclosure("More interviews & coverage", "更多專訪與報導", '<ul class="rows">' + "".join(press_row(r) for i, r in enumerate(ABOUT["press"]) if i not in ed["selected_press"]) + '</ul>')
    links = "".join(f'<a href="{esc(l["href"])}" rel="noopener" target="_blank">{esc(l["label"])} <span aria-hidden="true">↗</span></a>'
                    for l in ABOUT["links"] if not l["href"].startswith("mailto:"))

    body = f"""
<div class="page ab-editorial">
<nav class="ab-page-nav" aria-label="About sections"><span class="lbl">About / 關於</span><div>
<a href="#profile">{bi({"en":"Profile", "zh":"簡介"})}</a><a href="#practice">{bi({"en":"Practice", "zh":"實務"})}</a><a href="#recognition">{bi({"en":"Recognition", "zh":"獲獎"})}</a><a href="#press">{bi({"en":"Press", "zh":"報導"})}</a>
</div></nav>
<section class="ab-profile grid" id="profile" aria-labelledby="profile-name">
<aside class="ab-profile-aside"><figure><img src="{esc(about_asset('me.jpg'))}" alt="Portrait of Hao Wei Tu" width="1306" height="1306" fetchpriority="high"><figcaption><span>Melbourne ↔ Taipei</span><a href="mailto:{EMAIL}">{EMAIL} ↗</a></figcaption></figure></aside>
<div class="ab-profile-copy"><h1 id="profile-name">Hao Wei Tu <span lang="zh-Hant">杜浩瑋</span></h1>
<p class="ab-intro">{bi(ed["intro"])}</p>
<div class="ab-practice-copy"><div><h2 class="lbl mute">{bi({"en":"Design practice", "zh":"設計實務"})}</h2><p>{bi(ed["practice"])}</p></div><div><h2 class="lbl mute">{bi({"en":"Research", "zh":"研究"})}</h2><p>{bi(ed["research"])}</p></div></div>
{bio_more}
</div>
</section>

<section class="ab-section grid" id="practice" aria-labelledby="practice-h">
<header class="ab-section-heading"><h2 id="practice-h">{bi({"en":"In practice", "zh":"設計與對話"})}</h2><p class="mute">{bi({"en":"From the studio to the conversation.","zh":"從工作室到交流現場。"})}</p></header>
<div class="ab-section-content">
<div class="ab-talk">{video}<div class="ab-talk-copy"><p class="lbl mute">TEDxSwinburne · 2025</p><h3>Generative AI as a human-centered visualisation tool</h3><p>{bi(ed["talk"])}</p><a class="ab-text-link" href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener">YouTube ↗</a></div></div>
<div class="ab-client-section"><h3>{bi({"en":"Selected clients", "zh":"合作品牌"})}</h3><p class="ab-credit">D&amp;D Creative · Melbourne · 2022–{bi({"en":"present", "zh":"至今"})}</p><ul class="ab-client-list">{"".join(clients)}</ul></div>
</div></section>

<section class="ab-section grid" id="recognition" aria-labelledby="rec-h">
<header class="ab-section-heading"><h2 id="rec-h">{bi({"en":"Selected recognition", "zh":"獲獎選錄"})}</h2><p class="mute">{bi({"en":"Design awards & exhibitions", "zh":"設計獎項與展覽"})}</p></header>
<div class="ab-section-content"><ul class="ab-records">{"".join(record(r) for r in selected)}</ul>{awards_more}</div>
</section>

<section class="ab-section grid" id="exchange">
{section_heading("Teaching & exchange", "教學與交流")}
<div class="ab-section-content">{service_rows}{service_more}</div>
</section>

<section class="ab-section grid" id="press" aria-labelledby="press-h">
<header class="ab-section-heading"><h2 id="press-h">{bi({"en":"In print & online", "zh":"專訪與報導"})}</h2><p class="mute">{bi({"en":"On the work and the thinking behind it.", "zh":"關於作品，以及作品背後的想法。"})}</p></header>
<div class="ab-section-content"><div class="ab-press-features">{"".join(features)}</div>{press_more}</div>
</section>

<section class="ab-section ab-elsewhere grid">
{section_heading("Elsewhere", "其他平台")}
<div class="ab-section-content ab-link-list">{links}</div>
</section>
</div>
"""
    write("about/index.html", page(
        "/about/", "About — HTU. Hao Wei Tu 杜浩瑋",
        "Biography, design practice, research, awards and conversations with Hao Wei Tu, a communication designer working between Melbourne and Taipei.",
        body, current="about", body_cls="about"))


def build_404():
    body = """<section class="lost"><p class="lbl mute">404</p><p class="title">HTU<span style="color:var(--accent)">?</span></p>
<p><span class="en">This page has moved or never existed.</span><span class="zh">這個頁面已經搬走，或從來不存在。</span></p>
<p><a href="/work/"><span class="en">See the work</span><span class="zh">看作品</span></a> · <a href="/"><span class="en">Home</span><span class="zh">首頁</span></a></p></section>"""
    write("404.html", page("/404.html", "Not found — HTU.", "Page not found.", body).replace(
        '<meta name="robots" content="index, follow, max-image-preview:large">', '<meta name="robots" content="noindex">'))


def build_sitemap():
    today = dt.date.today().isoformat()
    urls = ["/", "/work/", "/about/"] + [f"/work/{p['id']}/" for p in PROJECTS]
    items = "\n".join(f"  <url><loc>{SITE}{u}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n')


def build_llms():
    """Keep the Portfolio section of llms.txt in step with the work pages."""
    f = ROOT / "llms.txt"
    if not f.exists():
        return
    text = f.read_text(encoding="utf-8")
    lines = [f"- {p['title']['en']} ({p['discipline']['en']}{', ' + year(p) if year(p) else ''}): {SITE}/work/{p['id']}/"
             for p in PROJECTS]
    section = "## Portfolio\n\n" + "\n".join(lines) + "\n\n"
    if "## Portfolio" in text:
        text = re.sub(r"## Portfolio\n.*?(?=^## )", section, text, flags=re.S | re.M)
    else:
        text = text.replace("## Contact", section + "## Contact", 1)
    f.write_text(text, encoding="utf-8")


def main():
    global CSS_V, JS_V
    CSS_V = int((ROOT / "assets/site.css").stat().st_mtime)
    JS_V = int((ROOT / "assets/site.js").stat().st_mtime)
    missing = [(p["id"], i["file"]) for p in PROJECTS for i in p["images"] if i["file"] not in IMAGES.get(p["id"], {})]
    if missing:
        raise SystemExit(f"run scripts/build_images.py first; no image data for {missing}")
    ids = {p["id"] for p in PROJECTS}
    for d in (ROOT / "work").iterdir() if (ROOT / "work").exists() else []:
        if d.is_dir() and d.name not in ids:
            shutil.rmtree(d)
            print("removed page", d.name)
    build_home()
    build_work()
    build_projects()
    build_about()
    build_404()
    build_sitemap()
    build_llms()
    print(f"built home, work, {len(PROJECTS)} projects, about, 404, sitemap")


if __name__ == "__main__":
    main()
