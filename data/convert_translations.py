"""Convert QuranEnc translation CSVs (data/raw/) to data/translations/{en,ur,hi}.json.

Output shape: {"meta": {...}, "1:1": "...", "1:2": "...", ...}

- meta holds the full "Translation Info" header (raw text + parsed fields).
- The leading verse number (e.g. "1. ") and footnote markers (e.g. "[1]") are
  removed; footnotes are not carried over. No other text is changed.

Usage: python data/convert_translations.py
"""

import csv
import json
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
OUT_DIR = DATA_DIR / "translations"

SOURCES = {
    "en": "english_hilali_khan_v1.1.2-csv.1.csv",
    "ur": "urdu_junagarhi_v1.1.3-csv.1.csv",
    "hi": "hindi_omari_v1.1.5-csv.1.csv",
}

EXPECTED_AYAT = 6236
EXPECTED_COLUMNS = ["id", "sura", "aya", "translation", "footnotes"]

# One or more footnote markers ("[1]", "[1][2]", "[6], [7]"), with the space
# before them (if any).
FOOTNOTE_RE = re.compile(r"( ?)(\[\d+\](?:,? ?\[\d+\])*)")
# After these, a space before the marker is dropped too ("word [1]." -> "word.").
CLOSING = set(" ,.;:!?)]،؛۔")


def strip_footnote_markers(text):
    def repl(m):
        nxt = text[m.end():m.end() + 1]
        if m.group(1) and (nxt == "" or nxt in CLOSING):
            return ""
        return m.group(1)

    return FOOTNOTE_RE.sub(repl, text)


def strip_aya_number(text, aya):
    prefix = f"{aya}. "
    return text[len(prefix):] if text.startswith(prefix) else text


def parse_header(header):
    meta = {"header": header}
    keys = {
        "Language": "language",
        "Translation ID": "translation_id",
        "Source": "source",
        "URL": "url",
        "Last update": "last_update",
        "Check for updates": "check_for_updates",
    }
    for line in header.splitlines():
        line = line.lstrip("#").strip()
        if not line or set(line) == {"-"} or line == "Translation Info:":
            continue
        key, sep, value = line.partition(": ")
        if sep and key in keys:
            meta[keys[key]] = value.strip()
        elif "PLEASE" in line:
            meta["notice"] = line
        else:
            meta["title"] = line
    return meta


def convert(lang, filename):
    src = RAW_DIR / filename
    with open(src, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))

    header, columns, body = rows[0], rows[1], rows[2:]
    assert header[0].startswith("Translation Info:"), f"{src}: missing header"
    assert columns == EXPECTED_COLUMNS, f"{src}: unexpected columns {columns}"

    meta = parse_header(header[0])
    meta["source_file"] = filename
    out = {"meta": meta}

    for row in body:
        _, sura, aya, translation, _footnotes = row
        key = f"{int(sura)}:{int(aya)}"
        assert key not in out, f"{src}: duplicate {key}"
        text = strip_footnote_markers(strip_aya_number(translation, aya))
        assert text and text == text.strip(), f"{src}: bad text at {key}"
        assert not re.search(r"\[\d+\]", text), f"{src}: marker left at {key}"
        out[key] = text

    count = len(out) - 1
    assert count == EXPECTED_AYAT, f"{src}: {count} ayat, expected {EXPECTED_AYAT}"

    OUT_DIR.mkdir(exist_ok=True)
    dest = OUT_DIR / f"{lang}.json"
    with open(dest, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"{dest.relative_to(DATA_DIR.parent)}: {count} ayat")


def main():
    for lang, filename in SOURCES.items():
        convert(lang, filename)


if __name__ == "__main__":
    sys.exit(main())
