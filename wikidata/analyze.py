"""
Qualitative analysis of Wikidata punning entities.

Reads QIDs from query.csv, fetches P31/P279 and labels via Wikidata API,
finds the shared class (where P31 == P279), and produces:
  - enriched.csv       : one row per (item, shared_class) with labels
  - summary.txt        : top shared classes + domain breakdown
"""

import csv
import json
import time
import requests
from collections import Counter, defaultdict
from pathlib import Path


INPUT_CSV   = Path(__file__).parent / "query-clean.csv"
ENRICHED    = Path(__file__).parent / "enriched.csv"
SUMMARY     = Path(__file__).parent / "summary-clean2.txt"

API_URL     = "https://www.wikidata.org/w/api.php"
HEADERS     = {"User-Agent": "punning-yago-analysis/1.0 (research project; margherita.necchi@gmail.com)"}
BATCH_SIZE  = 50          # max entities per API call
MAX_ITEMS   = None        # set to None to process all 10000
SLEEP_SEC   = 0.5         # polite pause between batches

# classes treated as Wikidata modeling noise, excluded from output
NOISE_CLASSES = {
    "Q7187",   # gene — systematic artifact of Wikidata gene ontology
    "Q427087", # non-coding RNA — same bioinformatics modeling artifact
}

# ── helpers ───────────────────────────────────────────────────────────────────

def qid(uri: str) -> str:
    """Extract QID from full URI or bare QID."""
    return uri.split("/")[-1]


def fetch_batch(qids: list[str]) -> dict:
    """Call wbgetentities for a batch of QIDs, return parsed entities dict."""
    params = {
        "action":  "wbgetentities",
        "ids":     "|".join(qids),
        "props":   "labels|claims",
        "languages": "en",
        "format":  "json",
    }
    for attempt in range(3):
        try:
            r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
            r.raise_for_status()
            return r.json().get("entities", {})
        except Exception as e:
            print(f"  [retry {attempt+1}] {e}")
            time.sleep(2 ** attempt)
    return {}


def get_label(entity: dict) -> str:
    return entity.get("labels", {}).get("en", {}).get("value", "")


def get_values(entity: dict, prop: str) -> list[str]:
    """Return list of QIDs for a given property."""
    claims = entity.get("claims", {}).get(prop, [])
    result = []
    for c in claims:
        try:
            val = c["mainsnak"]["datavalue"]["value"]["id"]
            result.append(val)
        except (KeyError, TypeError):
            pass
    return result


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    # 1. read QIDs
    raw = []
    with open(INPUT_CSV) as f:
        for row in csv.DictReader(f):
            raw.append(qid(row["item"]))

    items = raw[:MAX_ITEMS] if MAX_ITEMS else raw
    print(f"Processing {len(items)} items in batches of {BATCH_SIZE}...")

    rows           = []                    # (item_qid, item_label, shared_qid, shared_label)
    label_cache    = {}                    # qid -> label (avoids re-fetching class labels)
    shared_counter = Counter()
    examples       = defaultdict(list)    # shared_class -> [(qid, label), ...]
    EXAMPLES_N     = 3

    batches = [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

    for idx, batch in enumerate(batches):
        print(f"  batch {idx+1}/{len(batches)} ...", end=" ", flush=True)
        entities = fetch_batch(batch)

        for q in batch:
            ent = entities.get(q, {})
            label = get_label(ent)
            p31   = set(get_values(ent, "P31"))
            p279  = set(get_values(ent, "P279"))
            shared = (p31 & p279) - NOISE_CLASSES

            for s in shared:
                rows.append({
                    "item":         q,
                    "item_label":   label,
                    "shared_class": s,
                    "shared_label": "",   # filled below
                })
                shared_counter[s] += 1
                if len(examples[s]) < EXAMPLES_N and label:
                    examples[s].append((q, label))

        print("ok")
        time.sleep(SLEEP_SEC)

    # 2. fetch labels for shared classes in batches
    print("Fetching labels for shared classes...")
    class_qids = list(shared_counter.keys())
    for i in range(0, len(class_qids), BATCH_SIZE):
        batch = class_qids[i:i+BATCH_SIZE]
        entities = fetch_batch(batch)
        for q in batch:
            label_cache[q] = get_label(entities.get(q, {}))
        time.sleep(SLEEP_SEC)

    # fill shared_label
    for row in rows:
        row["shared_label"] = label_cache.get(row["shared_class"], "")

    # 3. write enriched CSV
    with open(ENRICHED, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["item","item_label","shared_class","shared_label"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Enriched CSV → {ENRICHED}")

    # 4. write summary
    top_n = 30
    lines = []
    lines.append("=" * 60)
    lines.append(f"PUNNING ANALYSIS — {len(items)} items processed")
    lines.append(f"Total (item, shared_class) pairs : {len(rows)}")
    lines.append(f"Distinct shared classes          : {len(shared_counter)}")
    lines.append(f"Items with ≥1 shared class       : {len(set(r['item'] for r in rows))}")
    lines.append("")
    lines.append(f"TOP {top_n} SHARED CLASSES")
    lines.append("-" * 60)
    for q, count in shared_counter.most_common(top_n):
        lbl = label_cache.get(q, q)
        lines.append(f"  {count:5d}  {lbl:40s}  ({q})")
        for ex_qid, ex_label in examples.get(q, []):
            lines.append(f"           → {ex_label} ({ex_qid})")

    lines.append("")
    lines.append("NOISE / EXCLUDED")
    lines.append("-" * 60)
    noise_items = len(items) - len(set(r["item"] for r in rows))
    lines.append(f"  {noise_items} items excluded (shared class in NOISE_CLASSES or no overlap after API fetch)")
    for nq in NOISE_CLASSES:
        lines.append(f"  - {nq} (filtered as noise)")

    summary_text = "\n".join(lines)
    with open(SUMMARY, "w") as f:
        f.write(summary_text)
    print(f"Summary      → {SUMMARY}")
    print()
    print(summary_text)


if __name__ == "__main__":
    main()
