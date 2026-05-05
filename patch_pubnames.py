#!/usr/bin/env python3
"""Add bilingual spans to all pr-pub names that are currently plain text."""
from pathlib import Path

HTML = Path("/Users/tuhaowei/Documents/HAOWEITU.INFO/haoweitu.info/index.html")
content = HTML.read_text(encoding="utf-8")

def fix_pub(old_text, en, zh):
    old = f'<div class="pr-pub">{old_text}</div>'
    new_en_zh = en if en == zh else f'<span class="en">{en}</span><span class="zh">{zh}</span>'
    new = f'<div class="pr-pub">{new_en_zh}</div>'
    n = content.count(old)
    if n == 0:
        print(f"  !! NOT FOUND: {old_text!r}")
        return
    return old, new, n

changes = [
    # English-only pubs (same in both modes)
    ("Campaign Brief",        "Campaign Brief",                 "Campaign Brief"),
    ("Swinburne",             "Swinburne",                      "Swinburne"),
    ("Campaign Brief Asia",   "Campaign Brief Asia",            "Campaign Brief Asia"),
    ("BizCommunity",          "BizCommunity",                   "BizCommunity"),
    ("ETtoday",               "ETtoday",                        "ETtoday"),
    ("MSN 新聞",              "MSN",                            "MSN 新聞"),
    ("Yahoo 新聞",            "Yahoo News",                     "Yahoo 新聞"),
    # Bilingual pubs
    ("CNA",                   "CNA",                            "中央社"),
    ("China Times",           "China Times",                    "中國時報"),
    ("Liberty Times",         "Liberty Times",                  "自由時報"),
    ("NOWnews 今日新聞",       "NOWnews",                        "今日新聞"),
    ("工商時報",              "Commercial Times",               "工商時報"),
    ("UDN 聯合新聞網",         "UDN",                            "聯合新聞網"),
    ("新頭條 TheHubNews",      "The Hub News",                   "新頭條"),
    ("中華日報",              "China Daily News",               "中華日報"),
    ("波新聞",                "Bo News",                        "波新聞"),
    ("策略風知識新聞網",       "Strategic Style",                "策略風知識新聞網"),
    ("CNA 中央社（平台）",     "CNA Platform",                   "中央社（訊息平台）"),
    ("蕃新聞 Yam",            "Yam News",                       "蕃新聞"),
    ("NTUST 台科大",           "NTUST",                          "台灣科技大學"),
    ("RTI 中央廣播電臺",       "Radio Taiwan International",     "中央廣播電臺"),
]

for args in changes:
    old_text, en, zh = args
    old = f'<div class="pr-pub">{old_text}</div>'
    if old not in content:
        print(f"  !! NOT FOUND: {old_text!r}")
        continue
    pub_inner = en if en == zh else f'<span class="en">{en}</span><span class="zh">{zh}</span>'
    new = f'<div class="pr-pub">{pub_inner}</div>'
    content = content.replace(old, new)
    print(f"  OK: {old_text!r} → en={en!r} zh={zh!r}")

HTML.write_text(content, encoding="utf-8")
print("\nDone.")
