#!/usr/bin/env python3
"""
Phase D: fill gloss_id gaps from WordNet Bahasa (Indonesian WordNet).

Source: Open Multilingual Wordnet omw-1.4, file omw-1.4/msa/wn-data-ind.tab
(WordNet Bahasa, http://wn-msa.sourceforge.net/, MIT license), archived at
data/corpora_zips/omw-1.4.zip. English synsets via NLTK WordNet.

Matching rule (quality-filtered):
- iterate wn.synsets(word); keep synsets whose lemma list contains the exact
  word (case-sensitive) -- this drops abbreviation/proper-noun junk senses
  ('was' -> Washington, 'at' -> astatine);
- the FIRST such synset that has Indonesian lemmas wins;
- gloss = up to 3 Indonesian lemmas joined with ', '.

Only fills rows where gloss_id IS NULL; existing Wiktionary glosses stay.
Needs NLTK_DATA with wordnet corpus extracted (see build_dataset.py notes).
Output: data/kamus_v22.sqlite (copy of kamus_v21.sqlite + fills).
"""
import os
import shutil
import sqlite3
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
SRC_DB = DATA / "kamus_v21.sqlite"
OUT_DB = DATA / "kamus_v22.sqlite"
OMW_ZIP = DATA / "corpora_zips" / "omw-1.4.zip"
TAB_MEMBER = "omw-1.4/msa/wn-data-ind.tab"


def load_ind_lemmas():
    ind = {}
    with zipfile.ZipFile(OMW_ZIP) as z, z.open(TAB_MEMBER) as f:
        for raw in f:
            line = raw.decode("utf-8")
            if line.startswith("#"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3 and p[1] == "ind:lemma":
                ind.setdefault(p[0], []).append(p[2].replace("_", " "))
    return ind


def main():
    os.environ.setdefault("NLTK_DATA", "/tmp/kamus_nltk")
    from nltk.corpus import wordnet as wn

    ind = load_ind_lemmas()
    print(f"WordNet Bahasa synsets with lemmas: {len(ind)}")

    shutil.copyfile(SRC_DB, OUT_DB)
    conn = sqlite3.connect(OUT_DB)
    before = conn.execute(
        "SELECT COUNT(*) FROM words WHERE gloss_id IS NOT NULL").fetchone()[0]
    total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    missing = [r[0] for r in conn.execute(
        "SELECT word FROM words WHERE gloss_id IS NULL")]

    filled = 0
    for word in missing:
        gloss = None
        for s in wn.synsets(word):
            if word not in [lem.name() for lem in s.lemmas()]:
                continue
            lemmas = ind.get(f"{s.offset():08d}-{s.pos()}")
            if lemmas:
                gloss = ", ".join(lemmas[:3])
                break
        if gloss:
            conn.execute("UPDATE words SET gloss_id=? WHERE word=?",
                         (gloss, word))
            filled += 1
    conn.execute(
        "INSERT OR REPLACE INTO metadata VALUES (?,?)",
        ("source_gloss_wordnet_bahasa",
         "WordNet Bahasa (Open Multilingual Wordnet, wn-data-ind.tab) - MIT - "
         "fills gloss_id gaps in v2.2 with exact-lemma synset matching"),
    )
    conn.commit()
    after = conn.execute(
        "SELECT COUNT(*) FROM words WHERE gloss_id IS NOT NULL").fetchone()[0]
    print(f"gloss_id coverage: {before} -> {after} of {total} "
          f"({100 * before / total:.1f}% -> {100 * after / total:.1f}%), "
          f"newly filled {filled}")
    for probe in ("just", "up", "make", "democracy", "freedom", "government"):
        row = conn.execute("SELECT gloss_id FROM words WHERE word=?",
                           (probe,)).fetchone()
        print(probe, "->", row)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
