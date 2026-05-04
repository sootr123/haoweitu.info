#!/usr/bin/env python3
"""
Screenshot all award/press pages and save to gallery folders.
Run: python3 screenshot.py
"""
import os, time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image
import io

BASE = Path("/Users/tuhaowei/Documents/HAOWEITU.INFO/haoweitu.info/gallery")

SHOTS = [
    # (url, save_path, wait_extra_ms)

    # ── Award pages (main rows) ──
    ("https://enter.tdc.org/finalists/", "tdc/1.jpg", 3000),
    ("https://dfaa.dfaawards.com/en/winner/", "dfa/1.jpg", 4000),
    ("https://www.dandad.org/annual/2022/entry/professional/235740", "dad-awards/1.jpg", 4000),
    ("https://aiga-365-design-competition.secure-platform.com/a/gallery/rounds/236/details/52825", "aiga/1.jpg", 4000),
    ("https://graphis.com/entry/a2bf0df3-7a54-4a2f-b9cf-3bfb6aa30d3e", "graphis/1.jpg", 3000),
    ("https://graphis.com/entry/0c178ce8-0fb5-4dae-9c84-e3d5870ba465", "graphis/2.jpg", 3000),
    ("https://segd.org/projects/dad-exhibition-in-taiwan/", "segd/1.jpg", 3000),
    ("https://agda.com.au/awards/results/8488/", "agda-awards/1.jpg", 3000),

    # ── ADC Annual Awards sub-rows ──
    ("https://www.oneclub.org/awards/adcawards/-award/42564/dad-exhibition-in-taiwan-posters/", "adc/1.jpg", 4000),
    ("https://www.oneclub.org/awards/adcawards/-award/42573/dad-exhibition-in-taiwan/", "adc/2.jpg", 4000),
    ("https://www.oneclub.org/awards/adcawards/-award/42571/dad-exhibition-in-taiwan/", "adc/3.jpg", 4000),
    ("https://www.oneclub.org/awards/adcawards/-award/42876/dad-exhibition-in-taiwan/", "adc/4.jpg", 4000),

    # ── Young Ones sub-rows ──
    ("https://www.oneclub.org/awards/youngones/-award/41255/pork-floss-for-hulk/", "young-ones/2.jpg", 4000),
    ("https://www.oneclub.org/awards/youngones/-award/34337/taipei-zoo/", "young-ones/3.jpg", 4000),
    ("https://www.oneclub.org/awards/youngones/-award/34340/chinese-character-festival/", "young-ones/4.jpg", 4000),

    # ── Red Dot sub-rows ──
    ("https://www.red-dot.org/project/islanders-summer-homework-60227", "red-dot/1.jpg", 3000),
    ("https://www.red-dot.org/project/pork-floss-for-hulk-54701", "red-dot/2.jpg", 3000),
    ("https://www.red-dot.org/project/rebuild-taiwans-traditional-culture-54798", "red-dot/3.jpg", 3000),
    ("https://www.red-dot.org/project/power-malt-40825", "red-dot/4.jpg", 3000),
    ("https://www.red-dot.org/project/taiwan-international-festival-of-arts-25399", "red-dot/5.jpg", 3000),

    # ── Press pages ──
    ("https://campaignbrief.com/australia-scores-three-finalists-at-shortlist-stage-of-type-directors-club-tdc72-competition/", "press/campaign-brief-2026.jpg", 3000),
    ("https://www.swinburne.edu.au/news/2025/11/Hao-Wei-Tu/", "press/swinburne-2025.jpg", 3000),
    ("https://www.cna.com.tw/news/ahel/202311270028.aspx", "press/cna-2023.jpg", 3000),
    ("https://www.chinatimes.com/realtimenews/20231127001133-260405", "press/chinatimes-2023.jpg", 3000),
    ("https://www.ettoday.net/news/20231127/2631451.htm", "press/ettoday-2023.jpg", 3000),
    ("https://www.ettoday.net/news/20220602/2264174.htm", "press/ettoday-2022.jpg", 3000),
    ("https://www.chinatimes.com/realtimenews/20220602001719-260405", "press/chinatimes-2022.jpg", 3000),
    ("https://news.ltn.com.tw/news/life/breakingnews/3947322", "press/liberty-2022.jpg", 3000),
    ("https://www.cna.com.tw/news/ahel/202206020056.aspx", "press/cna-2022.jpg", 3000),
    ("https://udn.com/news/story/6929/6358754", "press/udn-2022.jpg", 3000),
    ("https://campaignbriefasia.com/2022/02/22/inside-the-dad-pencil-taiwan-tech-hosts-dad-awards-annual-exhibition/", "press/campaign-brief-asia-2022.jpg", 3000),
    ("https://www.sohu.com/a/271883618_100105130", "press/sohu-2018.jpg", 3000),
    ("http://www.hkcd.com/content_p/2018-12/17/content_67812.html", "press/hkcd-2018.jpg", 3000),
    ("https://www.chinatimes.com/newspapers/20181029000220-260301?chdtv", "press/chinatimes-2018.jpg", 3000),
]

def resize_and_save(img_bytes: bytes, dest: Path, max_width=1200, quality=82):
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=quality, optimize=True)
    print(f"  Saved {dest} ({dest.stat().st_size//1024}KB)")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="en-US",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = ctx.new_page()
        # Dismiss cookie banners / popups by accepting everything
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)

        for url, rel_path, wait_ms in SHOTS:
            dest = BASE / rel_path
            if dest.exists():
                print(f"  SKIP (exists): {rel_path}")
                continue
            print(f"→ {rel_path}  {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=20000)
                page.wait_for_timeout(wait_ms)
                # Try to close cookie banners
                for sel in ["[id*='cookie'] button", "[class*='cookie'] button", "[id*='consent'] button", ".accept-btn", "#accept-cookies"]:
                    try:
                        btn = page.query_selector(sel)
                        if btn and btn.is_visible():
                            btn.click()
                            page.wait_for_timeout(400)
                            break
                    except:
                        pass
                img_bytes = page.screenshot(type="jpeg", quality=85, clip={"x":0,"y":0,"width":1400,"height":900})
                resize_and_save(img_bytes, dest)
            except Exception as e:
                print(f"  ERROR: {e}")

        browser.close()

if __name__ == "__main__":
    run()
