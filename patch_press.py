#!/usr/bin/env python3
"""Patch press section: remove dead UDN 2022, add all new valid links."""
from pathlib import Path

HTML = Path("/Users/tuhaowei/Documents/HAOWEITU.INFO/haoweitu.info/index.html")
content = HTML.read_text(encoding="utf-8")

def pr(year, href, en, zh, pub):
    return (
        f'<div class="press-row">\n'
        f'<div class="pr-year">{year}</div>\n'
        f'<div class="pr-head"><p class="pr-hl"><a class="ul" href="{href}" rel="noopener" target="_blank">'
        f'<span class="en">{en}</span><span class="zh">{zh}</span></a></p></div>\n'
        f'<div class="pr-pub">{pub}</div>\n'
        f'</div>\n'
    )

# ── 1. Remove dead UDN 2022 entry ──────────────────────────────────────────
dead_udn = (
    '<div class="press-row">\n'
    '<div class="pr-year">2022</div>\n'
    '<div class="pr-head"><p class="pr-hl"><a class="ul" href="https://udn.com/news/story/6929/6358754" rel="noopener" target="_blank">'
    '<span class="en">International Creative Competition: Taiwan Tech wins Young Ones Portfolio</span>'
    '<span class="zh">國際創意競賽 台科大生獲青年作品集大獎</span></a></p></div>\n'
    '<div class="pr-pub">UDN</div>\n'
    '</div>\n'
)
if dead_udn in content:
    content = content.replace(dead_udn, "", 1)
    print("Removed dead UDN 2022 entry")
else:
    print("!! UDN 2022 entry not found")

# ── 2. New 2023 entries — insert after ETtoday 2023 closing </div> ─────────
new_2023 = (
    pr("2023", "https://www.nownews.com/news/6309332",
       "Taiwan Tech student wins A$400,000 scholarship to study in Australia",
       "台科大杜浩瑋獲澳洲400萬元獎學金", "NOWnews 今日新聞") +
    pr("2023", "https://www.ctee.com.tw/news/20231127700540-431401",
       "Taiwan Tech graduate wins Swinburne PhD scholarship in Australia",
       "台科大設計系杜浩瑋獲斯威本博士獎學金赴澳", "工商時報") +
    pr("2023", "https://udn.com/news/story/6928/7600964",
       "Taiwan Tech's Hao Wei Tu wins A$400,000 PhD scholarship to study communication design",
       "台科大杜浩瑋獲400萬博士獎學金，赴澳洲讀傳達設計", "UDN 聯合新聞網") +
    pr("2023", "https://www.thehubnews.net/archives/313959",
       "Taiwan Tech design student wins full A$400,000 scholarship to study in Australia",
       "臺科大設計所杜浩瑋獲全額獎學金，三年共四百萬赴澳洲深造", "新頭條 TheHubNews") +
    pr("2023", "https://www.cdns.com.tw/articles/915090",
       "He won a A$400,000 PhD scholarship to study in Australia",
       "申請澳洲讀博，他獲獎學金400萬", "中華日報") +
    pr("2023", "https://www.bo6s.com.tw/news_detail.php?NewsID=74366",
       "Taiwan Tech graduate wins full PhD scholarship at Swinburne University",
       "台科大杜浩瑋獲澳洲斯威本大學博士全額獎學金", "波新聞") +
    pr("2023", "https://strategicstyle.org/scstyle-8368/20004/",
       "Young talent — Hao Wei Tu of Taiwan Tech leads in communication design innovation",
       "英雄出少年，臺科杜浩瑋創新傳達發光", "策略風知識新聞網") +
    pr("2023", "https://www.cna.com.tw/postwrite/chi/358003",
       "From graphic to communication design — Taiwan Tech student wins full Swinburne PhD scholarship",
       "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金", "CNA 中央社（平台）") +
    pr("2023", "https://n.yam.com/Article/20231127764476",
       "From graphic to communication design — Taiwan Tech student wins full Swinburne PhD scholarship",
       "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金", "蕃新聞 Yam") +
    pr("2023", "https://pse.is/5dy5xz",
       "From graphic to communication design — Taiwan Tech student wins Swinburne PhD scholarship",
       "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金", "MSN 新聞") +
    pr("2023", "https://pse.is/5cvtj2",
       "Taiwan Tech student wins full A$400,000 PhD scholarship in design — 3 years in Australia",
       "臺科大杜浩瑋獲澳洲設計博士全額獎學金，3年400萬元", "Yahoo 新聞") +
    pr("2023", "https://www.ntust.edu.tw/p/404-1000-119519.php?Lang=zh-tw",
       "From graphic to communication design — Taiwan Tech student wins full Swinburne PhD scholarship",
       "從平面設計到傳達設計，臺科大設計系同學杜浩瑋獲澳洲創新設計博士全額獎學金", "NTUST 台科大")
)

anchor_after_ettoday_2023 = (
    '<div class="pr-pub">ETtoday</div>\n'
    '</div>\n'
    '<div class="press-row">\n'
    '<div class="pr-year">2022</div>\n'
    '<div class="pr-head"><p class="pr-hl"><a class="ul" href="https://www.ettoday.net/news/20220602/2264174.htm"'
)
replacement_2023 = (
    '<div class="pr-pub">ETtoday</div>\n'
    '</div>\n' +
    new_2023 +
    '<div class="press-row">\n'
    '<div class="pr-year">2022</div>\n'
    '<div class="pr-head"><p class="pr-hl"><a class="ul" href="https://www.ettoday.net/news/20220602/2264174.htm"'
)
if anchor_after_ettoday_2023 in content:
    content = content.replace(anchor_after_ettoday_2023, replacement_2023, 1)
    print("Inserted 12 new 2023 entries")
else:
    print("!! 2023 insertion anchor not found")

# ── 3. New 2022 entries — insert after Campaign Brief Asia, before 2018 ────
new_2022 = (
    pr("2022", "https://www.rti.org.tw/news/view/id/2134694",
       "Taiwan Tech student — first in East Asia to win international Young Ones Portfolio",
       "國際個人青年作品集大獎，台科大生獲獎創東亞第一人", "RTI 中央廣播電臺") +
    pr("2022", "https://www.ntust.edu.tw/p/404-1000-102376.php?Lang=zh-tw",
       "Media coverage — Hao Wei Tu wins international design award",
       "臺科大杜浩瑋獲國際設計競賽青年作品集大獎媒體報導", "NTUST 台科大") +
    pr("2022", "https://www.bizcommunity.com/Article/196/736/227894.html",
       "Young Ones Student Awards 2022 — All Winners",
       "Young Ones 學生獎 2022 全部得獎者", "BizCommunity")
)

anchor_after_cbasia = (
    '<div class="pr-pub">Campaign Brief Asia</div>\n'
    '</div>\n'
    '<div class="press-row">\n'
    '<div class="pr-year">2018</div>'
)
replacement_2022 = (
    '<div class="pr-pub">Campaign Brief Asia</div>\n'
    '</div>\n' +
    new_2022 +
    '<div class="press-row">\n'
    '<div class="pr-year">2018</div>'
)
if anchor_after_cbasia in content:
    content = content.replace(anchor_after_cbasia, replacement_2022, 1)
    print("Inserted 3 new 2022 entries")
else:
    print("!! 2022 insertion anchor not found")

HTML.write_text(content, encoding="utf-8")
print("Done.")
