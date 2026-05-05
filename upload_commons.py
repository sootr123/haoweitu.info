#!/usr/bin/env python3
"""
Upload Horizental.jpg to Wikimedia Commons, then set P18 on Wikidata Q139601784.

Usage:
    WD_USER='B10510145@CLAUDE' WD_PASS='...' python3 upload_commons.py

Requirements: pip3 install requests wikibaseintegrator
"""
import os, sys
from pathlib import Path
import requests

WD_USER = os.environ.get("WD_USER", "")
WD_PASS = os.environ.get("WD_PASS", "")

if not WD_USER or not WD_PASS:
    sys.exit("Usage: WD_USER='...' WD_PASS='...' python3 upload_commons.py")

IMG_PATH    = Path(__file__).parent / "Horizental.jpg"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WD_API      = "https://www.wikidata.org/w/api.php"
FILENAME    = "Hao Wei Tu 杜浩瑋 TEDxSwinburne 2025.jpg"
UA          = "HaoWeiTuBot/1.0 (https://haoweitu.info)"

PAGE_TEXT = """\
== {{{{int:filedesc}}}} ==
{{{{Information
|description = {{{{en|1=Hao Wei Tu (杜浩瑋), Taiwanese communication designer and PhD candidate, speaking at TEDxSwinburne, Melbourne, 2025.}}}}
               {{{{zh|1=杜浩瑋，臺灣傳達設計師、斯威本大學博士候選人，於 2025 年 TEDxSwinburne 墨爾本演講。}}}}
|date        = 2025
|source      = {{{{own}}}}
|author      = [[User:B10510145|Hao Wei Tu (杜浩瑋)]]
}}}}

== {{{{int:license-header}}}} ==
{{{{self|cc-by-sa-4.0}}}}

[[Category:Hao Wei Tu]]
[[Category:TEDxSwinburne]]
[[Category:Taiwanese graphic designers]]
[[Category:People from Taichung]]
""".format()  # keeps the double braces as single

# ── helpers ───────────────────────────────────────────────────────────────────

def make_session(api_url: str) -> tuple[requests.Session, str]:
    s = requests.Session()
    s.headers["User-Agent"] = UA

    # login token
    lt = s.get(api_url, params={"action": "query", "meta": "tokens",
                                 "type": "login", "format": "json"}).json()
    lt = lt["query"]["tokens"]["logintoken"]

    # login
    r = s.post(api_url, data={"action": "login", "lgname": WD_USER,
                               "lgpassword": WD_PASS, "lgtoken": lt,
                               "format": "json"}).json()
    if r["login"]["result"] != "Success":
        print(f"  !! Login failed: {r['login']}")
        sys.exit(1)
    print(f"  Logged in as {r['login']['lgusername']} on {api_url.split('/')[2]}")

    # csrf token
    csrf = s.get(api_url, params={"action": "query", "meta": "tokens",
                                   "format": "json"}).json()
    csrf = csrf["query"]["tokens"]["csrftoken"]

    return s, csrf

# ── 1. Upload to Commons ──────────────────────────────────────────────────────

print("\n── Step 1: Upload to Wikimedia Commons ─────────────────────────────────")
cs, csrf_c = make_session(COMMONS_API)

with open(IMG_PATH, "rb") as f:
    img_bytes = f.read()

r = cs.post(COMMONS_API, data={
    "action":          "upload",
    "filename":        FILENAME,
    "text":            PAGE_TEXT,
    "comment":         "Upload portrait of Hao Wei Tu (杜浩瑋) for Wikidata P18",
    "token":           csrf_c,
    "format":          "json",
    "ignorewarnings":  "1",
}, files={"file": (FILENAME, img_bytes, "image/jpeg")})

upload_result = r.json()

if "error" in upload_result:
    err = upload_result["error"]
    if err.get("code") == "permissiondenied":
        print("\n!! Permission denied — the bot password lacks 'Upload new files'.")
        print("   Fix:")
        print("   1. Go to https://www.wikidata.org/wiki/Special:BotPasswords")
        print("   2. Click your 'CLAUDE' bot → Edit")
        print("   3. Also tick 'Upload new files'")
        print("   4. Save, copy new password, run this script again.")
    else:
        print(f"!! Upload error: {err}")
    sys.exit(1)

upload = upload_result.get("upload", {})
status = upload.get("result", "?")
commons_name = upload.get("filename", FILENAME)
print(f"  Upload result: {status}")
print(f"  File: https://commons.wikimedia.org/wiki/File:{commons_name.replace(' ', '_')}")

# ── 2. Set P18 on Wikidata ────────────────────────────────────────────────────

print("\n── Step 2: Set P18 on Wikidata ─────────────────────────────────────────")

try:
    from wikibaseintegrator import WikibaseIntegrator, wbi_login
    from wikibaseintegrator.datatypes import CommonsMedia
    from wikibaseintegrator import wbi_config

    wbi_config.config["USER_AGENT"] = UA
    wbi_config.config["MEDIAWIKI_API_URL"] = WD_API

    login_instance = wbi_login.Login(user=WD_USER, password=WD_PASS)
    wbi = WikibaseIntegrator(login=login_instance)
    item = wbi.item.get("Q139601784")

    # Check if P18 already set
    existing_p18 = item.claims.get("P18")
    if existing_p18:
        print(f"  ~ P18 already set: {[c.mainsnak.datavalue['value'] for c in existing_p18]}")
    else:
        item.claims.add(CommonsMedia(value=commons_name, prop_nr="P18"))
        item.write(summary="Add P18 portrait photo (TEDxSwinburne 2025)")
        print(f"  + P18 set to '{commons_name}'")

except ImportError:
    print("  wikibaseintegrator not installed — set P18 manually:")
    print(f"  Property P18, value: {commons_name}")

print("\nDone.")
print(f"Wikidata: https://www.wikidata.org/wiki/Q139601784")
print(f"Commons:  https://commons.wikimedia.org/wiki/File:{commons_name.replace(' ', '_')}")
