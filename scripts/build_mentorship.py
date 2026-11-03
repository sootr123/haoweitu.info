"""Build the unlisted D&AD New Blood mentorship call at /dad-mentorship-2027/.

Content lives in content/mentorship.json. The page is noindex and left out of
the sitemap and navigation, so only people with the link find it. The main site
builder calls build(page); this file can also run on its own.
"""
import html
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
EMAIL = "haowei@haoweitu.info"
INSTAGRAM = "https://www.instagram.com/haoweitu.info/"


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


def section(key, label, inner):
    return f"""
<section class="mt-section" aria-labelledby="mt-{key}">
  <h2 id="mt-{key}">{bi(label)}</h2>
  <div class="mt-section-body">{inner}</div>
</section>"""


def numbered(items):
    rows = "".join(
        f'<li><span class="mt-num num">{n:02d}</span><div>'
        + (f'<h3>{bi(item["title"])}</h3><p>{bi(item["text"])}</p>' if "title" in item else f"<p>{bi(item)}</p>")
        + "</div></li>"
        for n, item in enumerate(items, 1))
    return f'<ol class="mt-list">{rows}</ol>'


def build(page_func):
    c = json.loads((ROOT / "content/mentorship.json").read_text(encoding="utf-8"))
    mailto = f'mailto:{EMAIL}?subject={quote(c["subject"])}'
    title = bi(c["title"]).replace("2027 Mentorship", "2027<br>Mentorship").replace("2027 輔導", "2027<br>輔導")
    timeline = "".join(
        f'<li><span class="mt-date num">{bi(t["date"])}</span><p>{bi(t["text"])}</p></li>' for t in c["timeline"])
    apply = f"""{numbered(c["materials"])}
<div class="mt-send">
  <p>{bi({"en": "Email all three to", "zh": "將以上三項寄到"})}</p>
  <a class="mt-email" href="{mailto}">{EMAIL}</a>
  <p>{bi({"en": "with the subject line", "zh": "信件主旨請寫"})}</p>
  <p class="mt-subject num">{esc(c["subject"])}</p>
</div>"""
    contact = f"""<p>{bi({"en": "Questions are welcome by email or Instagram message.", "zh": "有任何問題，歡迎來信或透過 Instagram 私訊詢問。"})}</p>
<div class="mt-links"><a href="mailto:{EMAIL}">{EMAIL}<span aria-hidden="true">↗</span></a><a href="{INSTAGRAM}" rel="noopener" target="_blank">Instagram @haoweitu.info<span aria-hidden="true">↗</span></a></div>"""

    body = f"""
<section class="mt-intro" aria-labelledby="mt-heading">
  <div class="mt-kicker"><span>{bi({"en": "Mentorship by HTU.", "zh": "HTU. 設計輔導"})}</span><span>{bi({"en": "Online / Mandarin, English materials", "zh": "線上 / 中文授課・英文資料"})}</span></div>
  <div class="mt-heading-row">
    <h1 id="mt-heading">{title}</h1>
    <div class="mt-intro-copy">
      <p>{bi(c["summary"])}</p>
      <p class="mt-deadline">{bi({"en": "Apply by 30 November 2026", "zh": "報名截止：2026 年 11 月 30 日"})}</p>
      <div class="mt-actions"><a class="mt-button" href="{mailto}">{bi({"en": "Apply by email", "zh": "Email 報名"})}<span aria-hidden="true">→</span></a><a class="mt-text-link" href="{esc(c["briefs"])}" rel="noopener" target="_blank">{bi({"en": "See the 2027 briefs", "zh": "查看 2027 競賽題目"})}<span aria-hidden="true">↗</span></a></div>
    </div>
  </div>
</section>
<div class="mt-body">
{section("provide", {"en": "What you get", "zh": "計畫內容"}, numbered(c["provide"]))}
{section("eligibility", {"en": "Who can apply", "zh": "申請資格"}, numbered(c["eligibility"]))}
{section("apply", {"en": "How to apply", "zh": "報名方式"}, apply)}
{section("timeline", {"en": "Timeline", "zh": "時程"}, f'<ol class="mt-timeline">{timeline}</ol>')}
{section("contact", {"en": "Questions", "zh": "聯絡我們"}, contact)}
<p class="mt-note">{bi(c["note"])}</p>
</div>"""

    output = page_func(
        c["path"],
        f'{c["title"]["en"]} — HTU.',
        c["summary"]["en"],
        body,
        body_cls="mentorship-page",
    )
    css_version = int((ROOT / "assets/mentorship.css").stat().st_mtime)
    output = output.replace(
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        '<meta name="robots" content="noindex, nofollow">',
    )
    output = output.replace("</head>", f'<link rel="stylesheet" href="/assets/mentorship.css?v={css_version}">\n</head>')
    destination = ROOT / c["path"].strip("/") / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    import build_site

    build_site.CSS_V = int((ROOT / "assets/site.css").stat().st_mtime)
    build_site.JS_V = int((ROOT / "assets/site.js").stat().st_mtime)
    build(build_site.page)
    print("built mentorship page")
