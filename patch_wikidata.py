#!/usr/bin/env python3
"""
Patch Wikidata Q139601784 (Hao Wei Tu).

Setup (one-time):
    pip3 install wikibaseintegrator

Then:
  1. Go to https://www.wikidata.org/wiki/Special:BotPasswords
  2. Create a bot password — tick "Edit existing pages" + "Create, edit, and move pages"
  3. Run:
       WD_USER='YourWikiUsername@BotName' WD_PASS='the-bot-password' python3 patch_wikidata.py
"""
import os, sys

try:
    from wikibaseintegrator import WikibaseIntegrator, wbi_login
    from wikibaseintegrator.datatypes import Item, Time, ExternalID
    from wikibaseintegrator.models import Qualifiers
    from wikibaseintegrator import wbi_config
except ImportError:
    sys.exit("Run first:  pip3 install wikibaseintegrator")

WD_USER = os.environ.get("WD_USER", "")
WD_PASS = os.environ.get("WD_PASS", "")

if not WD_USER or not WD_PASS:
    sys.exit(
        "Usage:\n"
        "  WD_USER='YourUsername@BotName' WD_PASS='bot-password' python3 patch_wikidata.py"
    )

wbi_config.config['USER_AGENT'] = 'HaoWeiTuBot/1.0 (https://haoweitu.info)'
wbi_config.config['MEDIAWIKI_API_URL'] = 'https://www.wikidata.org/w/api.php'

print("Logging in…")
login_instance = wbi_login.Login(user=WD_USER, password=WD_PASS)
wbi = WikibaseIntegrator(login=login_instance)

print("Loading Q139601784…")
item = wbi.item.get('Q139601784')

# ── helpers ───────────────────────────────────────────────────────────────────

def year_q(y: int) -> Qualifiers:
    q = Qualifiers()
    q.add(Time(time=f'+{y}-00-00T00:00:00Z', precision=9, prop_nr='P585'))
    return q

def existing(prop: str) -> set:
    ids = set()
    for c in (item.claims.get(prop) or []):
        try:
            v = c.mainsnak.datavalue['value']
            ids.add(v['id'] if isinstance(v, dict) and 'id' in v else v)
        except (KeyError, TypeError, AttributeError):
            pass
    return ids

# ── P166  Awards received ─────────────────────────────────────────────────────

have = existing('P166')

awards = [
    ('Q7755030',  2022),   # The One Club — Young Ones Portfolio Award
    ('Q1561995',  2026),   # Type Directors Club — TDC 72
    ('Q24831678', 2020),   # Golden Pin Design Award
]

print("\nAwards (P166):")
for q, year in awards:
    if q in have:
        print(f"  ~ {q} ({year}) already present")
        continue
    item.claims.add(Item(value=q, prop_nr='P166', qualifiers=year_q(year)))
    print(f"  + {q} ({year})")

# ── External IDs ──────────────────────────────────────────────────────────────

ext_ids = [
    ('P2003', 'haoweitu.info'),                # Instagram username
    ('P4023', 'otonami-du'),                   # Behance username
    # P356 (DOI) must NOT go on a Person item — constraint violation
]

print("\nExternal IDs:")
for pid, val in ext_ids:
    if val in existing(pid):
        print(f"  ~ {pid} {val!r} already present")
        continue
    item.claims.add(ExternalID(value=val, prop_nr=pid))
    print(f"  + {pid} = {val!r}")

# ── Remove DOI (P356) via direct API — constraint violation on Person items ───
import requests as _req

print("\nRemoving P356 (DOI) — not valid on a Person item…")
_s = _req.Session()
_s.headers['User-Agent'] = wbi_config.config['USER_AGENT']

# login token
_lt = _s.get('https://www.wikidata.org/w/api.php',
              params={'action':'query','meta':'tokens','type':'login','format':'json'}
             ).json()['query']['tokens']['logintoken']
_s.post('https://www.wikidata.org/w/api.php',
        data={'action':'login','lgname':WD_USER,'lgpassword':WD_PASS,
              'lgtoken':_lt,'format':'json'})

# csrf token
_csrf = _s.get('https://www.wikidata.org/w/api.php',
               params={'action':'query','meta':'tokens','format':'json'}
              ).json()['query']['tokens']['csrftoken']

# get P356 claim GUIDs
_claims_r = _s.get('https://www.wikidata.org/w/api.php',
                   params={'action':'wbgetclaims','entity':'Q139601784',
                           'property':'P356','format':'json'}).json()
_guids = [c['id'] for c in _claims_r.get('claims',{}).get('P356',[])]

if _guids:
    _r = _s.post('https://www.wikidata.org/w/api.php',
                 data={'action':'wbremoveclaims','claim':'|'.join(_guids),
                       'token':_csrf,'summary':'Remove P356 DOI — constraint violation on Person item',
                       'format':'json'}).json()
    if _r.get('success'):
        print(f"  - P356 removed ({len(_guids)} claim(s))")
    else:
        print(f"  !! Error: {_r}")
else:
    print("  ~ P356 not found (already removed?)")

# ── Write ─────────────────────────────────────────────────────────────────────

print("\nWriting to Wikidata…")
item.write(
    summary='Add awards (Young Ones Portfolio, TDC 72, Golden Pin) + Instagram, Behance, DOI'
)
print("Done → https://www.wikidata.org/wiki/Q139601784")
