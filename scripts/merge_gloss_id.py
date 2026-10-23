#!/usr/bin/env python3
"""
Phase C: boost Indonesian glosses from Indonesian Wiktionary (id.wiktionary).

Streams data/kaikki-id.jsonl (wiktextract dump of Indonesian Wiktionary via
kaikki.org, CC BY-SA), takes English headwords (lang_code='en') whose first
sense gloss is Indonesian, and fills words.gloss_id in a COPY of the v2 DB
where it is still NULL. Existing glosses (from English Wiktionary
translations) are kept. Output: data/kamus_v21.sqlite.
"""
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
JSONL_PATH = DATA / "kaikki-id.jsonl"
SRC_DB = DATA / "kamus_v2.sqlite"
OUT_DB = DATA / "kamus_v21.sqlite"

WORD_RE = re.compile(r"^[a-z][a-z' \-]*$")


def trim_gloss(text, limit=240):
    text = " ".join((text or "").split()).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut or None


def main():
    glosses = {}
    n_lines = 0
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            n_lines += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("lang_code") != "en":
                continue
            word = (entry.get("word") or "").strip().lower()
            if not WORD_RE.fullmatch(word) or (len(word) < 2 and word not in ("a", "i")):
                continue
            if word in glosses:
                continue
            senses = entry.get("senses") or []
            if senses and all("form_of" in s for s in senses):
                continue
            gloss = None
            for s in senses:
                gs = s.get("glosses") or []
                if gs:
                    gloss = trim_gloss(gs[0])
                    break
            if gloss:
                glosses[word] = gloss
    print(f"parsed {n_lines} lines -> {len(glosses)} English headwords with Indonesian gloss")

    shutil.copyfile(SRC_DB, OUT_DB)
    conn = sqlite3.connect(OUT_DB)
    before = conn.execute("SELECT COUNT(*) FROM words WHERE gloss_id IS NOT NULL").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    filled = 0
    for word, gloss in glosses.items():
        cur = conn.execute(
            "UPDATE words SET gloss_id=? WHERE word=? AND gloss_id IS NULL",
            (gloss, word),
        )
        filled += cur.rowcount
    conn.execute(
        "INSERT OR REPLACE INTO metadata VALUES (?,?)",
        ("source_gloss_id_extra",
         "Indonesian Wiktionary (id.wiktionary) via Kaikki/wiktextract, CC BY-SA - fills gloss_id gaps in v2.1"),
    )
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM words WHERE gloss_id IS NOT NULL").fetchone()[0]
    print(f"gloss_id coverage: {before} -> {after} of {total} "
          f"({100 * before / total:.1f}% -> {100 * after / total:.1f}%), newly filled {filled}")
    for probe in ("education", "computer", "pronunciation", "beautiful", "water", "teacher", "student", "school"):
        row = conn.execute("SELECT gloss_id FROM words WHERE word=?", (probe,)).fetchone()
        print(probe, "->", row)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
