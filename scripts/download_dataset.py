"""
Fetch customer support tickets from HuggingFace REST API and save to data/hf_tickets.json.
Requires no special libraries beyond the standard library.
"""
import json, urllib.request, urllib.error, os, sys

BASE = "https://datasets-server.huggingface.co/rows"
DATASET = "Tobi-Bueck%2Fcustomer-support-tickets"
CONFIG = "default"
SPLIT = "train"
LENGTH = 100   # rows per page

def fetch_page(offset):
    url = f"{BASE}?dataset={DATASET}&config={CONFIG}&split={SPLIT}&offset={offset}&length={LENGTH}"
    req = urllib.request.Request(url, headers={"User-Agent": "python-urllib/3"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} on offset {offset}: {e.reason}", file=sys.stderr)
        return None

# Discover total rows
print("Fetching metadata...", flush=True)
first = fetch_page(0)
if first is None:
    print("ERROR: Could not fetch dataset. Check internet connectivity.")
    sys.exit(1)

total = first.get("num_rows_total", 0)
print(f"Total rows: {total}", flush=True)

all_records = []
offset = 0
while offset < min(total, 2000):   # cap at 2000 rows for speed
    page = fetch_page(offset)
    if page is None:
        break
    rows = [r["row"] for r in page.get("rows", [])]
    en_rows = [r for r in rows if r.get("language") == "en"]
    all_records.extend(en_rows)
    print(f"Fetched offset {offset}: {len(rows)} rows, {len(en_rows)} English", flush=True)
    offset += LENGTH

os.makedirs("data", exist_ok=True)
out = "data/hf_tickets.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(all_records, f, indent=2, ensure_ascii=False)

print(f"\nSaved {len(all_records)} English tickets to {out}", flush=True)
