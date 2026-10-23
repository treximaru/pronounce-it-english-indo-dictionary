#!/usr/bin/env python3
"""
Phase E: add synonyms & antonyms to the dictionary dataset (v2.3).

Sources (both already in the project, all open):
- English Wiktionary via Kaikki (data/kaikki-en.jsonl, CC BY-SA): per-sense
  synonyms/antonyms — primary source, sense-linked to our definitions.
- Open English WordNet via NLTK: fills words Wiktionary leaves empty
  (per field: synonyms and antonyms are filled independently).

Cleaning rules (both sources):
- lowercase; drop the headword itself; drop duplicates;
- keep only items that are themselves headwords in this dictionary
  (kills rare/obsolete junk and multiword phrases);
- WordNet: drop capitalized lemmas (proper nouns);
- caps: synonyms <= 8, antonyms <= 6, order of first appearance kept.

Output: data/kamus_v23.sqlite = kamus_v22.sqlite + columns synonyms/antonyms.
"""
import json
import os
import shutil
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
JSONL_PATH = DATA / "kaikki-en.jsonl"
SRC_DB = DATA / "kamus_v22.sqlite"
OUT_DB = DATA / "kamus_v23.sqlite"

MAX_SYN = 8
MAX_ANT = 6


def clean(items, headword, headwords, cap):
    out = []
    seen = set()
    for it in items:
        if not it:
            continue
        w = it.strip().lower()
        if w == headword or w in seen:
            continue
        if w not in headwords:
            continue
        seen.add(w)
        out.append(w)
        if len(out) >= cap:
            break
    return out


def from_wiktionary(headwords):
    syn = {}
    ant = {}
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            if '"synonyms"' not in line and '"antonyms"' not in line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("lang_code") != "en":
                continue
            w = (e.get("word") or "").strip().lower()
            if w not in headwords:
                continue
            s_list, a_list = [], []
            for s in e.get("senses") or []:
                for x in s.get("synonyms") or []:
                    s_list.append(x.get("word"))
                for x in s.get("antonyms") or []:
                    a_list.append(x.get("word"))
            for x in e.get("synonyms") or []:
                s_list.append(x.get("word"))
            for x in e.get("antonyms") or []:
                a_list.append(x.get("word"))
            if s_list:
                syn.setdefault(w, []).extend(s_list)
            if a_list:
                ant.setdefault(w, []).extend(a_list)
    return syn, ant


def from_wordnet(word, headwords, want_syn, want_ant):
    from nltk.corpus import wordnet as wn

    syns, ants = [], []
    for s in wn.synsets(word):
        for lem in s.lemmas():
            name = lem.name().replace("_", " ")
            if name[:1].isupper():
                continue
            if want_syn:
                syns.append(name)
            if want_ant:
                for a in lem.antonyms():
                    an = a.name().replace("_", " ")
                    if an[:1].isupper():
                        continue
                    ants.append(an)
    out_s = clean(syns, word, headwords, MAX_SYN) if want_syn else []
    out_a = clean(ants, word, headwords, MAX_ANT) if want_ant else []
    return out_s, out_a


def main():
    os.environ.setdefault("NLTK_DATA", "/tmp/kamus_nltk")
    src = sqlite3.connect(SRC_DB)
    words = [r[0] for r in src.execute("SELECT word FROM words")]
    src.close()
    headwords = set(words)
    print(f"headwords: {len(words)}")

    wiki_syn, wiki_ant = from_wiktionary(headwords)
    print(f"wiktionary raw: syn for {len(wiki_syn)} words, ant for {len(wiki_ant)} words")

    shutil.copyfile(SRC_DB, OUT_DB)
    conn = sqlite3.connect(OUT_DB)
    conn.execute("ALTER TABLE words ADD COLUMN synonyms TEXT")
    conn.execute("ALTER TABLE words ADD COLUMN antonyms TEXT")

    n_syn = n_ant = n_wn_syn = n_wn_ant = 0
    for w in words:
        syns = clean(wiki_syn.get(w, []), w, headwords, MAX_SYN)
        ants = clean(wiki_ant.get(w, []), w, headwords, MAX_ANT)
        if not syns or not ants:
            fs, fa = from_wordnet(w, headwords, not syns, not ants)
            if not syns and fs:
                syns = fs
                n_wn_syn += 1
            if not ants and fa:
                ants = fa
                n_wn_ant += 1
        if syns:
            n_syn += 1
        if ants:
            n_ant += 1
        conn.execute(
            "UPDATE words SET synonyms=?, antonyms=? WHERE word=?",
            (", ".join(syns) if syns else None,
             ", ".join(ants) if ants else None, w),
        )
    conn.execute(
        "INSERT OR REPLACE INTO metadata VALUES (?,?)",
        ("source_synonyms_antonyms",
         "Synonyms/antonyms v2.3: English Wiktionary via Kaikki (CC BY-SA) primary; "
         "Open English WordNet (NLTK) fills gaps; cleaned to dictionary headwords only"),
    )
    conn.commit()
    total = len(words)
    print(f"FINAL: synonyms {n_syn}/{total} ({100 * n_syn / total:.1f}%), "
          f"antonyms {n_ant}/{total} ({100 * n_ant / total:.1f}%)")
    print(f"wordnet fills: syn {n_wn_syn}, ant {n_wn_ant}")
    for probe in ("happy", "beautiful", "fast", "education", "computer", "begin"):
        row = conn.execute(
            "SELECT synonyms, antonyms FROM words WHERE word=?", (probe,)).fetchone()
        print(probe, "->", row)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
