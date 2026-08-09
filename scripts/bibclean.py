#!/usr/bin/env python3
"""Clean/dedupe/sort a BibTeX file. Fields: --dedupe, --sort, --normalize."""
import argparse
import re
import sys


def parse_bib(path):
    text = open(path, encoding="utf-8").read()
    entries = re.findall(r"@(\w+)\{([^,]*),(.*?)\n\}", text, re.S)
    result = []
    for typ, key, body in entries:
        fields = re.findall(r"(\w+)\s*=\s*\{(.*?)\}", body, re.S)
        result.append({"type": typ, "key": key.strip(), "fields": dict(fields)})
    return result


def normalize(text):
    # collapse whitespace, protect braces
    return re.sub(r"\s+", " ", text).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bib")
    ap.add_argument("--dedupe", action="store_true", help="按 DOI/title 去重")
    ap.add_argument("--sort", action="store_true", help="按键名排序")
    ap.add_argument("--out")
    a = ap.parse_args()

    entries = parse_bib(a.bib)
    if a.dedupe:
        seen, unique = set(), []
        for e in entries:
            doi = e["fields"].get("doi", "")
            title = normalize(e["fields"].get("title", "")).lower()
            sig = doi or title
            if sig and sig not in seen:
                seen.add(sig)
                unique.append(e)
        entries = unique
    if a.sort:
        entries.sort(key=lambda e: e["key"].lower())

    out_lines = []
    for e in entries:
        body = ",\n  ".join(f"{k} = {{{v.strip()}}}" for k, v in e["fields"].items())
        out_lines.append(f"@{e['type']}{{{e['key']},\n  {body}\n}}")
    out = "\n\n".join(out_lines) + "\n"
    dst = a.out or a.bib
    with open(dst, "w") as f:
        f.write(out)
    print(f"{len(entries)} 条已写入 {dst}")


if __name__ == "__main__":
    main()
