#!/usr/bin/env python3
"""Patch index.html to add gallery panels to all award/press rows that have screenshots."""

from pathlib import Path

HTML = Path("/Users/tuhaowei/Documents/HAOWEITU.INFO/haoweitu.info/index.html")

GTBTN = (
    '<button aria-label="Toggle gallery" class="gallery-toggle" '
    "onclick='this.classList.toggle(\"open\");var p=this.closest(\".award-row,.press-row\").querySelector(\".gallery-panel\");if(p)p.classList.toggle(\"open\");'>"
    '<svg width="10" height="7" viewBox="0 0 10 7" fill="none" aria-hidden="true">'
    '<path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    "</svg></button>"
)
SUBTN = (
    '<button class="sub-gallery-toggle" '
    "onclick='this.classList.toggle(\"open\");var p=this.nextElementSibling;if(p)p.classList.toggle(\"open\");'>"
    '<svg width="10" height="7" viewBox="0 0 10 7" fill="none" aria-hidden="true">'
    '<path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
    "</svg></button>"
)

def gpanel(src, alt):
    return f'<div class="gallery-panel"><img alt="{alt}" loading="lazy" src="gallery/{src}"/></div>'

def gpanel2(src1, alt1, src2, alt2):
    return (f'<div class="gallery-panel">'
            f'<img alt="{alt1}" loading="lazy" src="gallery/{src1}"/>'
            f'<img alt="{alt2}" loading="lazy" src="gallery/{src2}"/>'
            f'</div>')

def spanel(src, alt):
    return f'<div class="sub-gallery-panel"><img alt="{alt}" loading="lazy" src="gallery/{src}"/></div>'

content = HTML.read_text(encoding="utf-8")

# ─── Helper ───────────────────────────────────────────────────────────────────
def replace_once(old, new):
    global content
    if old not in content:
        print(f"  !! NOT FOUND: {old[:60]!r}")
        return False
    count = content.count(old)
    if count > 1:
        print(f"  !! AMBIGUOUS ({count}x): {old[:60]!r}")
        return False
    content = content.replace(old, new, 1)
    print(f"  OK: {old[:60]!r}")
    return True

# ─── 1. TDC 72 ───────────────────────────────────────────────────────────────
replace_once(
    '<h3 class="aw-title"><a class="ul" href="https://enter.tdc.org/finalists/" rel="noopener" target="_blank"><span class="en">NY TDC 72 — Type Directors Club</span><span class="zh">紐約 TDC 字體設計大獎 第 72 屆</span></a></h3>\n<p class="aw-sub"><span class="en">Type Directors Club, New York</span><span class="zh">紐約字體指導俱樂部</span></p>\n</div>\n<div class="aw-result">Winner</div>\n</div>',
    '<h3 class="aw-title"><a class="ul" href="https://enter.tdc.org/finalists/" rel="noopener" target="_blank"><span class="en">NY TDC 72 — Type Directors Club</span><span class="zh">紐約 TDC 字體設計大獎 第 72 屆</span></a></h3>\n<p class="aw-sub"><span class="en">Type Directors Club, New York</span><span class="zh">紐約字體指導俱樂部</span></p>\n</div>\n<div class="aw-result">Winner</div>\n'
    + GTBTN + gpanel("tdc/1.jpg", "NY TDC 72 · Type Directors Club, 2026") + '</div>'
)

# ─── 2. DFA Gold ─────────────────────────────────────────────────────────────
replace_once(
    '<h3 class="aw-title"><a class="ul" href="https://dfaa.dfaawards.com/en/winner/" rel="noopener" target="_blank"><span class="en">Design for Asia Awards — Gold</span><span class="zh">香港 DFA 亞洲最具影響力設計獎 — 金獎</span></a></h3>\n<p class="aw-sub"><span class="en">Hong Kong Design Centre</span><span class="zh">香港設計中心</span></p>\n</div>\n<div class="aw-result">Gold</div>\n</div>',
    '<h3 class="aw-title"><a class="ul" href="https://dfaa.dfaawards.com/en/winner/" rel="noopener" target="_blank"><span class="en">Design for Asia Awards — Gold</span><span class="zh">香港 DFA 亞洲最具影響力設計獎 — 金獎</span></a></h3>\n<p class="aw-sub"><span class="en">Hong Kong Design Centre</span><span class="zh">香港設計中心</span></p>\n</div>\n<div class="aw-result">Gold</div>\n'
    + GTBTN + gpanel("dfa/1.jpg", "Design for Asia Awards Gold · 2022") + '</div>'
)

# ─── 3. D&AD Awards ──────────────────────────────────────────────────────────
replace_once(
    '<h3 class="aw-title"><a class="ul" href="https://www.dandad.org/annual/2022/entry/professional/235740" rel="noopener" target="_blank"><span class="en">D&amp;AD Awards</span><span class="zh">英國 D&amp;AD 設計與廣告大獎</span></a></h3>\n<p class="aw-sub"><span class="en">D&amp;AD, London</span><span class="zh">英國倫敦</span></p>\n</div>\n<div class="aw-result">Shortlist</div>\n</div>',
    '<h3 class="aw-title"><a class="ul" href="https://www.dandad.org/annual/2022/entry/professional/235740" rel="noopener" target="_blank"><span class="en">D&amp;AD Awards</span><span class="zh">英國 D&amp;AD 設計與廣告大獎</span></a></h3>\n<p class="aw-sub"><span class="en">D&amp;AD, London</span><span class="zh">英國倫敦</span></p>\n</div>\n<div class="aw-result">Shortlist</div>\n'
    + GTBTN + gpanel("dad-awards/1.jpg", "D&AD Awards · Shortlist, 2022") + '</div>'
)

# ─── 4. AIGA 365 ─────────────────────────────────────────────────────────────
replace_once(
    '<h3 class="aw-title"><a class="ul" href="https://aiga-365-design-competition.secure-platform.com/a/gallery/rounds/236/details/52825" rel="noopener" target="_blank"><span class="en">AIGA 365 Design Award</span><span class="zh">美國 AIGA 365 設計獎</span></a></h3>\n<p class="aw-sub"><span class="en">American Institute of Graphic Arts</span><span class="zh">美國平面設計協會</span></p>\n</div>\n<div class="aw-result">Winner</div>\n</div>',
    '<h3 class="aw-title"><a class="ul" href="https://aiga-365-design-competition.secure-platform.com/a/gallery/rounds/236/details/52825" rel="noopener" target="_blank"><span class="en">AIGA 365 Design Award</span><span class="zh">美國 AIGA 365 設計獎</span></a></h3>\n<p class="aw-sub"><span class="en">American Institute of Graphic Arts</span><span class="zh">美國平面設計協會</span></p>\n</div>\n<div class="aw-result">Winner</div>\n'
    + GTBTN + gpanel("aiga/1.jpg", "AIGA 365 Design Award · Winner, 2022") + '</div>'
)

# ─── 5. Graphis (2 images) ───────────────────────────────────────────────────
replace_once(
    '<h3 class="aw-title"><span class="en">Graphis Poster Annual</span><span class="zh">美國 Graphis 海報年鑑</span></h3>\n<p class="aw-sub">\n<span class="en">Poster &amp; Advertising — <a class="ul" href="https://graphis.com/entry/a2bf0df3-7a54-4a2f-b9cf-3bfb6aa30d3e" rel="noopener" target="_blank">Entry 1</a> · <a class="ul" href="https://graphis.com/entry/0c178ce8-0fb5-4dae-9c84-e3d5870ba465" rel="noopener" target="_blank">Entry 2</a></span>\n<span class="zh">海報與廣告類 — <a class="ul" href="https://graphis.com/entry/a2bf0df3-7a54-4a2f-b9cf-3bfb6aa30d3e" rel="noopener" target="_blank">作品一</a> · <a class="ul" href="https://graphis.com/entry/0c178ce8-0fb5-4dae-9c84-e3d5870ba465" rel="noopener" target="_blank">作品二</a></span>\n</p>\n</div>\n<div class="aw-result">Platinum</div>\n</div>',
    '<h3 class="aw-title"><span class="en">Graphis Poster Annual</span><span class="zh">美國 Graphis 海報年鑑</span></h3>\n<p class="aw-sub">\n<span class="en">Poster &amp; Advertising — <a class="ul" href="https://graphis.com/entry/a2bf0df3-7a54-4a2f-b9cf-3bfb6aa30d3e" rel="noopener" target="_blank">Entry 1</a> · <a class="ul" href="https://graphis.com/entry/0c178ce8-0fb5-4dae-9c84-e3d5870ba465" rel="noopener" target="_blank">Entry 2</a></span>\n<span class="zh">海報與廣告類 — <a class="ul" href="https://graphis.com/entry/a2bf0df3-7a54-4a2f-b9cf-3bfb6aa30d3e" rel="noopener" target="_blank">作品一</a> · <a class="ul" href="https://graphis.com/entry/0c178ce8-0fb5-4dae-9c84-e3d5870ba465" rel="noopener" target="_blank">作品二</a></span>\n</p>\n</div>\n<div class="aw-result">Platinum</div>\n'
    + GTBTN + gpanel2("graphis/1.jpg", "Graphis Poster Annual · Entry 1, 2023", "graphis/2.jpg", "Graphis Poster Annual · Entry 2, 2023") + '</div>'
)

# ─── 6. SEGD ─────────────────────────────────────────────────────────────────
replace_once(
    '<h3 class="aw-title"><a class="ul" href="https://segd.org/projects/dad-exhibition-in-taiwan/" rel="noopener" target="_blank"><span class="en">SEGD Global Design Awards</span><span class="zh">SEGD 國際設計獎</span></a></h3>\n<p class="aw-sub"><span class="en">Society for Experiential Graphic Design</span><span class="zh">體驗式平面設計協會</span></p>\n</div>\n<div class="aw-result">Finalist</div>\n</div>',
    '<h3 class="aw-title"><a class="ul" href="https://segd.org/projects/dad-exhibition-in-taiwan/" rel="noopener" target="_blank"><span class="en">SEGD Global Design Awards</span><span class="zh">SEGD 國際設計獎</span></a></h3>\n<p class="aw-sub"><span class="en">Society for Experiential Graphic Design</span><span class="zh">體驗式平面設計協會</span></p>\n</div>\n<div class="aw-result">Finalist</div>\n'
    + GTBTN + gpanel("segd/1.jpg", "SEGD Global Design Awards · Finalist, 2022") + '</div>'
)

# ─── 7. AGDA Awards Finalist ─────────────────────────────────────────────────
replace_once(
    '<h3 class="aw-title"><a class="ul" href="https://agda.com.au/awards/results/8488/" rel="noopener" target="_blank"><span class="en">AGDA Awards · Emerging Designer of the Year</span><span class="zh">澳洲設計師協會 年度新銳設計師</span></a></h3>\n<p class="aw-sub"><span class="en">Australian Graphic Design Association</span><span class="zh">澳洲設計師協會</span></p>\n</div>\n<div class="aw-result">Finalist</div>\n</div>',
    '<h3 class="aw-title"><a class="ul" href="https://agda.com.au/awards/results/8488/" rel="noopener" target="_blank"><span class="en">AGDA Awards · Emerging Designer of the Year</span><span class="zh">澳洲設計師協會 年度新銳設計師</span></a></h3>\n<p class="aw-sub"><span class="en">Australian Graphic Design Association</span><span class="zh">澳洲設計師協會</span></p>\n</div>\n<div class="aw-result">Finalist</div>\n'
    + GTBTN + gpanel("agda-awards/1.jpg", "AGDA Awards · Emerging Designer of the Year Finalist, 2025") + '</div>'
)

# ─── 8. ADC Annual Awards sub-rows ───────────────────────────────────────────
replace_once(
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42564/dad-exhibition-in-taiwan-posters/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan · Posters</a></span><span class="sub-res">Silver</span></div>',
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42564/dad-exhibition-in-taiwan-posters/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan · Posters</a></span><span class="sub-res">Silver</span>'
    + SUBTN + spanel("adc/1.jpg", "ADC Annual Awards · D&AD Exhibition in Taiwan Posters · Silver, 2022") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42573/dad-exhibition-in-taiwan/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan</a></span><span class="sub-res">Bronze</span></div>',
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42573/dad-exhibition-in-taiwan/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan</a></span><span class="sub-res">Bronze</span>'
    + SUBTN + spanel("adc/2.jpg", "ADC Annual Awards · D&AD Exhibition in Taiwan · Bronze, 2022") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42571/dad-exhibition-in-taiwan/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan</a></span><span class="sub-res">Bronze</span></div>',
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42571/dad-exhibition-in-taiwan/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan</a></span><span class="sub-res">Bronze</span>'
    + SUBTN + spanel("adc/3.jpg", "ADC Annual Awards · D&AD Exhibition in Taiwan · Bronze, 2022") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42876/dad-exhibition-in-taiwan/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan</a></span><span class="sub-res">Merit</span></div>',
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/adcawards/-award/42876/dad-exhibition-in-taiwan/" rel="noopener" target="_blank">D&amp;AD Exhibition in Taiwan</a></span><span class="sub-res">Merit</span>'
    + SUBTN + spanel("adc/4.jpg", "ADC Annual Awards · D&AD Exhibition in Taiwan · Merit, 2022") + '</div>'
)

# ─── 9. Young Ones sub-rows ──────────────────────────────────────────────────
replace_once(
    '<div class="sub-row"><span class="sub-yr">2021</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/youngones/-award/41255/pork-floss-for-hulk/" rel="noopener" target="_blank">Pork Floss for Hulk</a></span><span class="sub-res">Merit</span></div>',
    '<div class="sub-row"><span class="sub-yr">2021</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/youngones/-award/41255/pork-floss-for-hulk/" rel="noopener" target="_blank">Pork Floss for Hulk</a></span><span class="sub-res">Merit</span>'
    + SUBTN + spanel("young-ones/2.jpg", "The Young Ones ADC · Pork Floss for Hulk · Merit, 2021") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2019</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/youngones/-award/34337/taipei-zoo/" rel="noopener" target="_blank">Taipei Zoo</a></span><span class="sub-res">Merit</span></div>',
    '<div class="sub-row"><span class="sub-yr">2019</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/youngones/-award/34337/taipei-zoo/" rel="noopener" target="_blank">Taipei Zoo</a></span><span class="sub-res">Merit</span>'
    + SUBTN + spanel("young-ones/3.jpg", "The Young Ones ADC · Taipei Zoo · Merit, 2019") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2019</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/youngones/-award/34340/chinese-character-festival/" rel="noopener" target="_blank">Chinese Character Festival</a></span><span class="sub-res">Merit</span></div>',
    '<div class="sub-row"><span class="sub-yr">2019</span><span class="sub-name"><a class="ul" href="https://www.oneclub.org/awards/youngones/-award/34340/chinese-character-festival/" rel="noopener" target="_blank">Chinese Character Festival</a></span><span class="sub-res">Merit</span>'
    + SUBTN + spanel("young-ones/4.jpg", "The Young Ones ADC · Chinese Character Festival · Merit, 2019") + '</div>'
)

# ─── 10. Red Dot sub-rows ────────────────────────────────────────────────────
replace_once(
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/islanders-summer-homework-60227" rel="noopener" target="_blank">Islander\'s Summer Homework</a></span><span class="sub-res">Concept Award</span></div>',
    '<div class="sub-row"><span class="sub-yr">2022</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/islanders-summer-homework-60227" rel="noopener" target="_blank">Islander\'s Summer Homework</a></span><span class="sub-res">Concept Award</span>'
    + SUBTN + spanel("red-dot/1.jpg", "Red Dot Design Award · Islander's Summer Homework · Concept Award, 2022") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2021</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/pork-floss-for-hulk-54701" rel="noopener" target="_blank">Pork Floss for Hulk</a></span><span class="sub-res">Packaging</span></div>',
    '<div class="sub-row"><span class="sub-yr">2021</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/pork-floss-for-hulk-54701" rel="noopener" target="_blank">Pork Floss for Hulk</a></span><span class="sub-res">Packaging</span>'
    + SUBTN + spanel("red-dot/2.jpg", "Red Dot Design Award · Pork Floss for Hulk · Packaging, 2021") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2021</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/rebuild-taiwans-traditional-culture-54798" rel="noopener" target="_blank">Rebuild Taiwan\'s Traditional Culture</a></span><span class="sub-res">Posters</span></div>',
    '<div class="sub-row"><span class="sub-yr">2021</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/rebuild-taiwans-traditional-culture-54798" rel="noopener" target="_blank">Rebuild Taiwan\'s Traditional Culture</a></span><span class="sub-res">Posters</span>'
    + SUBTN + spanel("red-dot/3.jpg", "Red Dot Design Award · Rebuild Taiwan's Traditional Culture · Posters, 2021") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2019</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/power-malt-40825" rel="noopener" target="_blank">Power Malt</a></span><span class="sub-res">Communication</span></div>',
    '<div class="sub-row"><span class="sub-yr">2019</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/power-malt-40825" rel="noopener" target="_blank">Power Malt</a></span><span class="sub-res">Communication</span>'
    + SUBTN + spanel("red-dot/4.jpg", "Red Dot Design Award · Power Malt · Communication, 2019") + '</div>'
)
replace_once(
    '<div class="sub-row"><span class="sub-yr">2018</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/taiwan-international-festival-of-arts-25399" rel="noopener" target="_blank">Taiwan International Festival of Arts</a></span><span class="sub-res">Communication</span></div>',
    '<div class="sub-row"><span class="sub-yr">2018</span><span class="sub-name"><a class="ul" href="https://www.red-dot.org/project/taiwan-international-festival-of-arts-25399" rel="noopener" target="_blank">Taiwan International Festival of Arts</a></span><span class="sub-res">Communication</span>'
    + SUBTN + spanel("red-dot/5.jpg", "Red Dot Design Award · Taiwan International Festival of Arts · Communication, 2018") + '</div>'
)

# ─── 11. Press rows ──────────────────────────────────────────────────────────
# Helper to wrap a press-row ending in a toggle+panel
def add_press_gallery(pub_text, year_text, src, alt):
    """Find press-row by unique pub+headline fragment and append gallery."""
    # The closing pattern for a press-row without gallery is: </div>\n</div>\n<div class="press-row">
    # We need to anchor precisely. Use the url+pub combination as the anchor.
    pass

press_patches = [
    # (unique anchor in the row, gallery src, alt)
    (
        '<a class="ul" href="https://campaignbrief.com/australia-scores-three-finalists-at-shortlist-stage-of-type-directors-club-tdc72-competition/"',
        'press/campaign-brief-2026.jpg', 'Campaign Brief · Australia scores three finalists at NY TDC 72, 2026'
    ),
    (
        '<a class="ul" href="https://www.cna.com.tw/news/ahel/202311270028.aspx"',
        'press/cna-2023.jpg', 'CNA · Taiwan Tech graduate awarded Swinburne PhD scholarship, 2023'
    ),
    (
        '<a class="ul" href="https://www.chinatimes.com/realtimenews/20231127001133-260405"',
        'press/chinatimes-2023.jpg', 'China Times · From Taipei to Melbourne, 2023'
    ),
    (
        '<a class="ul" href="https://www.ettoday.net/news/20231127/2631451.htm"',
        'press/ettoday-2023.jpg', 'ETtoday · Taiwan Tech to Swinburne, 2023'
    ),
    (
        '<a class="ul" href="https://www.ettoday.net/news/20220602/2264174.htm"',
        'press/ettoday-2022.jpg', 'ETtoday · Taiwan + East Asia first: Hao Wei Tu wins Young Ones Portfolio, 2022'
    ),
    (
        '<a class="ul" href="https://www.chinatimes.com/realtimenews/20220602001719-260405"',
        'press/chinatimes-2022.jpg', 'China Times · Taiwan and East Asia first — Hao Wei Tu takes Young Ones Portfolio, 2022'
    ),
    (
        '<a class="ul" href="https://news.ltn.com.tw/news/life/breakingnews/3947322"',
        'press/liberty-2022.jpg', 'Liberty Times · First East Asian designer to win international youth competition, 2022'
    ),
    (
        '<a class="ul" href="https://www.cna.com.tw/news/ahel/202206020056.aspx"',
        'press/cna-2022.jpg', 'CNA · Taiwan first: Hao Wei Tu wins international design competition, 2022'
    ),
    (
        '<a class="ul" href="https://udn.com/news/story/6929/6358754"',
        'press/udn-2022.jpg', 'UDN · Taiwan Tech wins Young Ones Portfolio, 2022'
    ),
    (
        '<a class="ul" href="https://campaignbriefasia.com/2022/02/22/inside-the-dad-pencil-taiwan-tech-hosts-dad-awards-annual-exhibition/"',
        'press/campaign-brief-asia-2022.jpg', 'Campaign Brief Asia · Inside the D&AD Pencil, 2022'
    ),
    (
        '<a class="ul" href="https://www.sohu.com/a/271883618_100105130"',
        'press/sohu-2018.jpg', 'Sohu · Cross-Strait Chinese Character Cultural Creativity Competition, 2018'
    ),
    (
        '<a class="ul" href="http://www.hkcd.com/content_p/2018-12/17/content_67812.html"',
        'press/hkcd-2018.jpg', 'Hong Kong Commercial Daily · LOHAS Chinese Characters, 2018'
    ),
]

# For press rows: the row ends with </div>\n</div>\n (closing pr-head and then press-row)
# Pattern per press row (without gallery):
# <div class="press-row">\n...<a ...ANCHOR...</a>...\n</div>\n<div class="pr-pub">PUB</div>\n</div>
# We need to find the closing of each press-row by the URL anchor and add before last </div>

for anchor, src, alt in press_patches:
    # Find the press-row containing this anchor
    idx = content.find(anchor)
    if idx == -1:
        print(f"  !! PRESS anchor NOT FOUND: {anchor[:60]!r}")
        continue
    # Find the closing </div> of this press-row (3 closing divs after anchor: pr-hl, pr-head, press-row)
    # Press rows without gallery end with: </div>\n</div>\n  (pr-pub close + press-row close)
    # But some already have gallery panels - detect by checking if gallery-panel follows the anchor
    row_end = content.find('</div>\n<div class="press-row">', idx)
    section_end = content.find('</div>\n</section>', idx)
    closing_pos = min(
        (row_end if row_end != -1 else 10**9),
        (section_end if section_end != -1 else 10**9)
    )
    if closing_pos == 10**9:
        print(f"  !! PRESS row end NOT FOUND for: {anchor[:60]!r}")
        continue
    # Check if gallery-toggle already exists in this segment
    segment = content[idx:closing_pos]
    if 'gallery-toggle' in segment or 'gallery-panel' in segment:
        print(f"  SKIP (already has gallery): {anchor[:60]!r}")
        continue
    # Insert gallery before the closing </div> of press-row
    insert_pos = closing_pos  # position of the closing </div>\n
    new_gallery = "\n" + GTBTN + gpanel(src, alt)
    content = content[:insert_pos] + new_gallery + content[insert_pos:]
    print(f"  OK press: {src}")

HTML.write_text(content, encoding="utf-8")
print("\nDone. index.html updated.")
