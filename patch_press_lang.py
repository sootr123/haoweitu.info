#!/usr/bin/env python3
"""
Fix press section language consistency:
  - English articles: both <span class="en"> and <span class="zh"> use English headline
  - Chinese articles: both spans use Chinese headline; pub names in Chinese
"""
from pathlib import Path
import re

HTML = Path("/Users/tuhaowei/Documents/HAOWEITU.INFO/haoweitu.info/index.html")
content = HTML.read_text(encoding="utf-8")

def fix(url_frag, new_en, new_zh, new_pub):
    """Replace headline spans and pub name for the press-row containing url_frag."""
    global content
    # Find the press-row block containing this URL fragment
    pattern = re.compile(
        r'(<div class="press-row">.*?href="[^"]*' + re.escape(url_frag) + r'[^"]*"[^>]*>)'
        r'(<span class="en">)(.*?)(</span>)(<span class="zh">)(.*?)(</span>)'
        r'(</a></p></div>\n<div class="pr-pub">)(.*?)(</div>)',
        re.DOTALL
    )
    def replacer(m):
        return (m.group(1) +
                '<span class="en">' + new_en + '</span>' +
                '<span class="zh">' + new_zh + '</span>' +
                '</a></p></div>\n<div class="pr-pub">' + new_pub + '</div>')
    new_content, n = pattern.subn(replacer, content)
    if n == 0:
        print(f"  !! NOT FOUND: {url_frag}")
    else:
        content = new_content
        print(f"  OK: {url_frag[:55]}")

# ── English articles: zh span → English ───────────────────────────────────

fix("campaignbrief.com/australia-scores",
    "Australia scores three finalists at NY TDC 72",
    "Australia scores three finalists at NY TDC 72",
    "Campaign Brief")

fix("swinburne.edu.au/news/2025",
    "Hao Wei Tu — PhD Researcher Profile",
    "Hao Wei Tu — PhD Researcher Profile",
    "Swinburne")

fix("campaignbriefasia.com/2022",
    "Inside the D&amp;AD Pencil — Taiwan Tech hosts the Annual Exhibition",
    "Inside the D&amp;AD Pencil — Taiwan Tech hosts the Annual Exhibition",
    "Campaign Brief Asia")

fix("bizcommunity.com",
    "Young Ones Student Awards 2022 — All Winners",
    "Young Ones Student Awards 2022 — All Winners",
    "BizCommunity")

# ── Chinese articles: en span → Chinese; fix pub names ───────────────────

# 2023
fix("cna.com.tw/news/ahel/202311270028",
    "台科大畢業生獲斯威本博士獎學金",
    "台科大畢業生獲斯威本博士獎學金",
    "中央社")

fix("chinatimes.com/realtimenews/20231127001133",
    "從台北到墨爾本：設計畢業生的研究之路",
    "從台北到墨爾本：設計畢業生的研究之路",
    "中國時報")

fix("ettoday.net/news/20231127",
    "從台科大到斯威本：設計研究者的海外之路",
    "從台科大到斯威本：設計研究者的海外之路",
    "ETtoday")

fix("nownews.com",
    "台科大杜浩瑋獲澳洲400萬元獎學金",
    "台科大杜浩瑋獲澳洲400萬元獎學金",
    "今日新聞")

fix("ctee.com.tw",
    "台科大設計系杜浩瑋獲斯威本博士獎學金赴澳",
    "台科大設計系杜浩瑋獲斯威本博士獎學金赴澳",
    "工商時報")

fix("udn.com/news/story/6928",
    "台科大杜浩瑋獲400萬博士獎學金，赴澳洲讀傳達設計",
    "台科大杜浩瑋獲400萬博士獎學金，赴澳洲讀傳達設計",
    "聯合新聞網")

fix("thehubnews.net",
    "臺科大設計所杜浩瑋獲全額獎學金，三年共四百萬赴澳洲深造",
    "臺科大設計所杜浩瑋獲全額獎學金，三年共四百萬赴澳洲深造",
    "新頭條")

fix("cdns.com.tw",
    "申請澳洲讀博，他獲獎學金400萬",
    "申請澳洲讀博，他獲獎學金400萬",
    "中華日報")

fix("bo6s.com.tw",
    "台科大杜浩瑋獲澳洲斯威本大學博士全額獎學金",
    "台科大杜浩瑋獲澳洲斯威本大學博士全額獎學金",
    "波新聞")

fix("strategicstyle.org",
    "英雄出少年，臺科杜浩瑋創新傳達發光",
    "英雄出少年，臺科杜浩瑋創新傳達發光",
    "策略風知識新聞網")

fix("cna.com.tw/postwrite",
    "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金",
    "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金",
    "中央社（訊息平台）")

fix("yam.com",
    "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金",
    "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金",
    "蕃新聞")

fix("pse.is/5dy5xz",
    "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金",
    "從平面設計到傳達設計，臺科大設計系杜浩瑋獲澳洲創新設計博士全額獎學金",
    "MSN 新聞")

fix("pse.is/5cvtj2",
    "臺科大杜浩瑋獲澳洲設計博士全額獎學金，3年400萬元",
    "臺科大杜浩瑋獲澳洲設計博士全額獎學金，3年400萬元",
    "Yahoo 新聞")

fix("ntust.edu.tw/p/404-1000-119519",
    "從平面設計到傳達設計，臺科大設計系同學杜浩瑋獲澳洲創新設計博士全額獎學金",
    "從平面設計到傳達設計，臺科大設計系同學杜浩瑋獲澳洲創新設計博士全額獎學金",
    "台灣科技大學")

# 2022
fix("ettoday.net/news/20220602",
    "台灣＋東亞首例！台科大杜浩瑋奪國際設計競賽青年作品集大獎",
    "台灣＋東亞首例！台科大杜浩瑋奪國際設計競賽青年作品集大獎",
    "ETtoday")

fix("chinatimes.com/realtimenews/20220602",
    "台灣及東亞首位！台科大杜浩瑋獲國際設計青年大獎",
    "台灣及東亞首位！台科大杜浩瑋獲國際設計青年大獎",
    "中國時報")

fix("news.ltn.com.tw",
    "東亞第一人！台科大生杜浩瑋奪國際青年創意競賽大獎",
    "東亞第一人！台科大生杜浩瑋奪國際青年創意競賽大獎",
    "自由時報")

fix("cna.com.tw/news/ahel/202206020056",
    "台灣首位獲獎！台科大杜浩瑋獲國際設計競賽大獎",
    "台灣首位獲獎！台科大杜浩瑋獲國際設計競賽大獎",
    "中央社")

fix("rti.org.tw",
    "國際個人青年作品集大獎，台科大生獲獎創東亞第一人",
    "國際個人青年作品集大獎，台科大生獲獎創東亞第一人",
    "中央廣播電臺")

fix("ntust.edu.tw/p/404-1000-102376",
    "臺科大杜浩瑋獲國際設計競賽青年作品集大獎媒體報導",
    "臺科大杜浩瑋獲國際設計競賽青年作品集大獎媒體報導",
    "台灣科技大學")

# 2018 — also fix bilingual pub name spans → plain Chinese
fix("chinatimes.com/newspapers/20181029",
    "漢字文創作品展 彰顯文化自信",
    "漢字文創作品展 彰顯文化自信",
    "中國時報")

fix("sohu.com",
    "兩岸漢字文化創意競賽獲獎作品展",
    "兩岸漢字文化創意競賽獲獎作品展",
    "搜狐")

fix("hkcd.com",
    "樂活漢字 · 魅力文化 — 兩岸創意競賽獲獎作品展",
    "樂活漢字 · 魅力文化 — 兩岸創意競賽獲獎作品展",
    "香港商報")

HTML.write_text(content, encoding="utf-8")
print("\nDone.")
