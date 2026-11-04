#!/usr/bin/env python3
"""Find Amway products named in a clip and pick their cartoon files from the product-cartoons catalog.

usage: find_products.py captions.json [catalog.json] > products-found.json

Matches catalog aliases against the spoken words (spaces removed, lowercase), longest alias first,
no overlaps. Output: [{code, name_th, alias, start_s, end_s, webm, png, photo, ambiguous}] in reel time.
"""
import json
import os
import re
import sys

DEFAULT_CATALOG = "/Volumes/JamesM.2/Claude/Video/product-cartoons/catalog.json"


def norm(s):
    return re.sub(r"[\s\-–()]+", "", s.lower())


def main():
    caps = json.load(open(sys.argv[1]))
    cat = json.load(open(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CATALOG))
    root = cat["root"]
    # spoken text with a time per character
    text, times = "", []
    for item in caps["items"]:
        for w in item.get("words", []):
            t = norm(w["text"])
            n = max(1, len(t))
            for k in range(len(t)):
                a = w["start_s"] + (w["end_s"] - w["start_s"]) * k / n
                times.append((a, w["end_s"]))
            text += t
    cands = []  # (alias_norm, product)
    for p in cat["products"]:
        for a in p["aliases"]:
            na = norm(a)
            if len(na) >= 4 or (len(na) == 3 and na.isascii()):  # EAA
                cands.append((na, a, p))
    cands.sort(key=lambda c: -len(c[0]))
    taken = [False] * len(text)
    hits = []
    for na, a, p in cands:
        for m in re.finditer(re.escape(na), text):
            s, e = m.start(), m.end()
            if any(taken[s:e]):
                continue
            # same alias text shared by several products (e.g. a lipstick line) -> flag it
            same = sorted({q["code"] for nb, _, q in cands if nb == na})
            for k in range(s, e):
                taken[k] = True
            f = p["files"]
            hits.append({"code": p["code"], "name_th": p["name_th"], "alias": a,
                         "start_s": round(times[s][0], 2), "end_s": round(times[e - 1][1], 2),
                         "webm": os.path.join(root, f["webm"]) if f.get("webm") else None,
                         "png": os.path.join(root, f["png"]) if f.get("png") else None,
                         "photo": p["photo"], "ambiguous": same if len(same) > 1 else []})
    hits.sort(key=lambda h: h["start_s"])
    json.dump(hits, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
