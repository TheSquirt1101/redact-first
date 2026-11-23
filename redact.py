#!/usr/bin/env python3
"""
redact-first - de-identify personal data before you paste it into any AI.

One file, no dependencies beyond the Python standard library. It never sends
anything anywhere. The mapping between real values and their codes is written to
a local file next to your input and nothing else sees it.

Usage:
    python redact.py scan   <file> [<file> ...]      # just tell me what's in here
    python redact.py encode <file> [--names list.txt]  # make a safe-to-paste copy
    python redact.py decode <file>                     # swap the codes back to real values

Typical flow:
    1. python redact.py encode class.txt --names names.txt
         -> writes class.redacted.txt  (paste THIS into the AI)
         -> writes class.map.json       (stays on your machine; never paste this)
    2. Paste class.redacted.txt into ChatGPT / Claude / Gemini, get a reply.
    3. Save the reply as reply.txt, then:
         python redact.py decode reply.txt --map class.map.json
         -> writes reply.decoded.txt with the real names put back.

This is a tool, not legal advice, and it does not make you compliant with POPIA
or any other law. See SCOPE.md.
"""
import argparse
import json
import os
import re
import sys

# --- Detectors -------------------------------------------------------------
# Order matters: names first (most specific to a supplied list), then the
# structured identifiers.

EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
# South African mobile/landline: +27 or a leading 0, then 9 digits, with
# optional spaces or dashes in between (082 123 4567, 0821234567, +27 82 123 4567).
PHONE_RE = re.compile(r"(?<![\w+])(?:\+27|0)(?:[\s-]?\d){9}(?!\d)")
# Any run of 13 digits is a *candidate* SA ID number; we validate with Luhn
# before treating it as one, to avoid grabbing ordinary long numbers.
ID_CANDIDATE_RE = re.compile(r"(?<!\d)\d{13}(?!\d)")


def luhn_ok(number: str) -> bool:
    """SA ID numbers carry a Luhn check digit. Use it to cut false positives."""
    digits = [int(c) for c in number]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def load_names(path: str) -> list:
    """A newline-separated list of names/words to treat as personal. Blank lines
    and lines starting with # are ignored. Longest first, so 'Mary Jane' is
    matched before 'Mary'."""
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as fh:
        names = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    return sorted(set(names), key=len, reverse=True)


def find_all(text: str, names: list):
    """Return a list of (start, end, kind, value) hits, de-overlapped, left to right."""
    hits = []

    if names:
        names_re = re.compile(
            r"\b(" + "|".join(re.escape(n) for n in names) + r")\b", re.IGNORECASE
        )
        for m in names_re.finditer(text):
            hits.append((m.start(), m.end(), "NAME", m.group(0)))

    for m in EMAIL_RE.finditer(text):
        hits.append((m.start(), m.end(), "EMAIL", m.group(0)))

    for m in ID_CANDIDATE_RE.finditer(text):
        if luhn_ok(m.group(0)):
            hits.append((m.start(), m.end(), "ID", m.group(0)))

    for m in PHONE_RE.finditer(text):
        hits.append((m.start(), m.end(), "PHONE", m.group(0)))

    # Sort and drop overlaps (first/longest match wins).
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    chosen = []
    last_end = -1
    for h in hits:
        if h[0] >= last_end:
            chosen.append(h)
            last_end = h[1]
    return chosen


# --- Commands --------------------------------------------------------------

def cmd_scan(args):
    total = 0
    names = load_names(args.names)
    for path in args.files:
        text = _read(path)
        hits = find_all(text, names)
        total += len(hits)
        counts = {}
        for _, _, kind, _v in hits:
            counts[kind] = counts.get(kind, 0) + 1
        print(f"\n{path}")
        if not hits:
            print("  nothing that looks like personal data. (Still check it yourself.)")
            continue
        summary = ", ".join(f"{v} {k.lower()}{'s' if v > 1 else ''}" for k, v in counts.items())
        print(f"  found: {summary}")
        if args.show:
            for _, _, kind, value in hits:
                print(f"    {kind:6} {value}")
        else:
            print("  (run with --show to list them; they stay on your screen only)")
    if total:
        print(f"\nDo not paste these files into an AI as-is. Run 'encode' first.")
    return 0


def cmd_encode(args):
    names = load_names(args.names)
    for path in args.files:
        text = _read(path)
        hits = find_all(text, names)

        value_to_code = {}
        counters = {}
        # Assign codes in document order (left to right) so [NAME_01] is the
        # first name that appears, which reads naturally.
        for start, end, kind, value in sorted(hits, key=lambda h: h[0]):
            key = (kind, value.lower() if kind == "NAME" else value)
            if key not in value_to_code:
                counters[kind] = counters.get(kind, 0) + 1
                value_to_code[key] = f"[{kind}_{counters[kind]:02d}]"
        # Replace right to left so earlier offsets stay valid.
        out = text
        for start, end, kind, value in sorted(hits, key=lambda h: h[0], reverse=True):
            key = (kind, value.lower() if kind == "NAME" else value)
            out = out[:start] + value_to_code[key] + out[end:]

        # Map is code -> real value, for decoding later. Preserve the original
        # casing of the first occurrence (the keys above are lowercased for names).
        mapping = {}
        for (kind, lowered), code in value_to_code.items():
            # find first original occurrence to preserve casing
            orig = next((v for s, e, k, v in hits
                         if k == kind and (v.lower() if kind == "NAME" else v) == lowered), lowered)
            mapping[code] = orig

        base = _strip_ext(path)
        red_path = base + ".redacted.txt"
        map_path = base + ".map.json"
        _write(red_path, out)
        _write(map_path, json.dumps(mapping, ensure_ascii=False, indent=2))
        print(f"{path}")
        print(f"  -> {red_path}   (safe to paste)")
        print(f"  -> {map_path}   (KEEP LOCAL - never paste this)")
        print(f"  replaced {len(mapping)} unique value(s)")
    return 0


def cmd_decode(args):
    map_path = args.map or (_strip_ext(args.files[0]) + ".map.json")
    if not os.path.exists(map_path):
        print(f"Can't find the mapping file: {map_path}", file=sys.stderr)
        print("Pass the right one with --map path/to/your.map.json", file=sys.stderr)
        return 1
    with open(map_path, "r", encoding="utf-8") as fh:
        mapping = json.load(fh)
    for path in args.files:
        text = _read(path)
        # Replace longer codes first (not strictly needed with [XX_NN] form).
        for code in sorted(mapping, key=len, reverse=True):
            text = text.replace(code, mapping[code])
        out_path = _strip_ext(path) + ".decoded.txt"
        _write(out_path, text)
        print(f"{path} -> {out_path}")
    return 0


# --- IO helpers ------------------------------------------------------------

def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _strip_ext(path):
    root, _ = os.path.splitext(path)
    return root


def main(argv=None):
    p = argparse.ArgumentParser(
        prog="redact.py",
        description="De-identify personal data before pasting it into any AI.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="report personal data found, change nothing")
    s.add_argument("files", nargs="+")
    s.add_argument("--names", help="file of names/words to treat as personal")
    s.add_argument("--show", action="store_true", help="list the actual matches on screen")
    s.set_defaults(func=cmd_scan)

    e = sub.add_parser("encode", help="write a safe-to-paste copy + a local mapping")
    e.add_argument("files", nargs="+")
    e.add_argument("--names", help="file of names/words to treat as personal")
    e.set_defaults(func=cmd_encode)

    d = sub.add_parser("decode", help="swap the codes in an AI reply back to real values")
    d.add_argument("files", nargs="+")
    d.add_argument("--map", help="the .map.json written by encode")
    d.set_defaults(func=cmd_decode)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
