#!/usr/bin/env python3
"""Build kamus_v25.sqlite from kamus_v24.sqlite (COPY, v24 untouched).

Two fixes, both measured, both reversible (v24 stays on disk):
1. Function-word definitions: the dataset stores ONE WordNet sense per word,
   and for function words that sense is often a different word entirely
   ('was' -> Washington, 'at' -> astatine, 'does' -> Dept. of Energy).
   FUNC_FIXES replaces pos + definition with the common sense.
2. Archaic examples: Wiktionary's first example is sometimes a historical
   quotation (e.g. 'and' -> a c. 1430 cookbook). An example is archaic if
   its Kaikki ref carries a year < 1700, or its text has Middle English
   markers (thorn/eth letters, thou/thy/hath/doth). Archaic examples are
   replaced by the first example for the same word (same pos preferred)
   whose ref year is >= 1700 or unknown and whose text is not archaic.
   If no replacement exists, the original is kept (a mismatched sense
   would be worse than an old quote).

Also applies FUNC_FIXES to wordlist/wordlist_gloss_prioritas.csv so the
manual translation work is not misled either.

Outputs: data/kamus_v25.sqlite, scripts/v25_report.txt.
"""
import csv
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
EN_DUMP = DATA / "kaikki-en.jsonl"
SRC_DB = DATA / "kamus_v24.sqlite"
OUT_DB = DATA / "kamus_v25.sqlite"
WORDLIST = BASE / "wordlist" / "wordlist_gloss_prioritas.csv"
REPORT = Path(__file__).resolve().parent / "v25_report.txt"
# NOTE: /tmp on this VM is a 512 MB tmpfs — large intermediates must NOT
# go there (a 433 MB grep dump filled it and killed this script once).
# All temp files go to a disk-backed dir under ~/workspace/tmp instead.
WORK = Path.home() / "workspace" / "tmp" / "v25"

YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
ARCHAIC_TEXT_RE = re.compile(
    r"[þð]|\b(thou|thy|thine|hath|doth|saith|ye)\b", re.IGNORECASE
)
YEAR_CUTOFF = 1700

FUNC_FIXES = {
    'a': ('determiner', 'Used before a singular noun to refer to one thing or person, not a particular one.'),
    'an': ('determiner', 'Used before a singular noun beginning with a vowel sound, to refer to one thing or person.'),
    'are': ('verb', 'Present tense of be (plural, and second person singular).'),
    'as': ('conjunction', 'Used to compare things, or to say that something happens at the same time.'),
    'at': ('preposition', 'Expressing location, time, or direction.'),
    'be': ('verb', 'To exist; used with other verbs to form tenses and the passive voice.'),
    'can': ('verb', 'To be able to; used to express ability or permission.'),
    'do': ('verb', 'To perform an action; used with other verbs to form questions and negatives.'),
    'does': ('verb', 'Third-person singular present of do.'),
    'did': ('verb', 'Past tense of do.'),
    'doing': ('verb', 'Present participle of do.'),
    'have': ('verb', 'To possess or own; used with other verbs to form perfect tenses.'),
    'has': ('verb', 'Third-person singular present of have.'),
    'had': ('verb', 'Past tense of have.'),
    'having': ('verb', 'Present participle of have.'),
    'he': ('pronoun', 'Used to refer to a man or boy previously mentioned.'),
    'i': ('pronoun', 'Used by a speaker to refer to himself or herself.'),
    'in': ('preposition', 'Expressing location inside something, or during a period of time.'),
    'it': ('pronoun', 'Used to refer to a thing, animal, or situation previously mentioned.'),
    'its': ('determiner', 'Belonging to it.'),
    'may': ('verb', 'Used to express possibility or permission.'),
    'me': ('pronoun', 'Used by a speaker to refer to himself or herself as the object of a verb or preposition.'),
    'might': ('verb', 'Used to express possibility; past tense of may.'),
    'must': ('verb', 'Used to say that something is necessary or very likely.'),
    'no': ('determiner', 'Not any; used to refuse or deny.'),
    'of': ('preposition', 'Expressing a relationship between things, such as possession or origin.'),
    'on': ('preposition', 'Supported by and in contact with; about a subject.'),
    'or': ('conjunction', 'Used to connect alternatives.'),
    'over': ('preposition', 'Above and across; more than.'),
    'so': ('conjunction', 'Therefore; as a result.'),
    'us': ('pronoun', 'Used by a speaker to refer to himself or herself and others as the object of a verb or preposition.'),
    'was': ('verb', 'Past tense of be (first and third person singular).'),
    'while': ('conjunction', 'During the time that; whereas.'),
    'who': ('pronoun', 'What person or people; used to introduce a clause about a person.'),
    'will': ('verb', 'Used to express the future, or willingness.'),
    'am': ('verb', 'First-person singular present of be.'),
    'is': ('verb', 'Third-person singular present of be.'),
    'were': ('verb', 'Past tense of be.'),
    'been': ('verb', 'Past participle of be.'),
    'made': ('verb', 'Past tense of make.'),
    'got': ('verb', 'Past tense of get.'),
    'should': ('verb', 'Used to say what is right or expected, or what should happen.'),
    'about': ('preposition', 'On the subject of; approximately.'),
    'above': ('preposition', 'Higher than; more than.'),
    'after': ('preposition', 'Following in time; behind in place.'),
    'before': ('preposition', 'Earlier than; in front of.'),
    'below': ('preposition', 'Lower than.'),
    'between': ('preposition', 'In the space or time separating two things.'),
    'through': ('preposition', 'From one end to the other; by means of.'),
    'under': ('preposition', 'Below; less than.'),
    'with': ('preposition', 'Accompanied by; using.'),
    'within': ('preposition', 'Inside; within the limits of.'),
    'without': ('preposition', 'Not having; in the absence of.'),
    'for': ('preposition', 'Intended for; because of; during.'),
    'by': ('preposition', 'Near; through the action of; before a time.'),
    'but': ('conjunction', 'Used to introduce something contrasting with what was just said.'),
}


def ref_year(ref):
    if not ref:
        return None
    m = YEAR_RE.search(ref)
    return int(m.group(1)) if m else None


def is_archaic_text(text):
    return bool(ARCHAIC_TEXT_RE.search(text or ""))


def grep_prefilter(pattern_file, out_file):
    with open(out_file, "w", encoding="utf-8") as out:
        subprocess.run(
            ["grep", "-F", "-f", str(pattern_file), str(EN_DUMP)],
            stdout=out, check=False,
        )


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    log = []
    shutil.copyfile(SRC_DB, OUT_DB)
    conn = sqlite3.connect(OUT_DB)
    cur = conn.cursor()

    # ---- 1. function-word definition fixes ----
    fixed = []
    for word, (pos, definition) in FUNC_FIXES.items():
        cur.execute(
            "UPDATE words SET pos=?, definition_en=? WHERE word=?",
            (pos, definition, word),
        )
        if cur.rowcount:
            fixed.append(word)
    conn.commit()
    log.append(f"definition fixes applied: {len(fixed)} words")
    log.append("fixed words: " + ", ".join(fixed))

    # ---- 2a. find archaic examples (grep prefilter + parse) ----
    rows = cur.execute(
        "SELECT word, pos, example FROM words "
        "WHERE example IS NOT NULL AND example <> ''"
    ).fetchall()
    db_examples = {ex: (w, p) for w, p, ex in rows}
    print(f"DB examples: {len(db_examples)}")
    pat = WORK / "v25_ex_patterns.txt"
    with pat.open("w", encoding="utf-8") as f:
        for ex in db_examples:
            f.write(ex[:80].replace("\n", " ") + "\n")
    matched = WORK / "v25_ex_matched.jsonl"
    grep_prefilter(pat, matched)
    text_year = {}
    with matched.open(encoding="utf-8") as f:
        for line in f:
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if e.get("lang_code") != "en":
                continue
            for s in e.get("senses") or []:
                for ex in s.get("examples") or []:
                    t = ex.get("text") or ""
                    if t in db_examples:
                        y = ref_year(ex.get("ref"))
                        if t not in text_year or (
                            y is not None
                            and (text_year[t] is None or y < text_year[t])
                        ):
                            text_year[t] = y
    archaic = {}  # word -> (pos, old_example, reason)
    for w, p, ex in rows:
        y = text_year.get(ex)
        if (y is not None and y < YEAR_CUTOFF) or is_archaic_text(ex):
            archaic[w] = (p, ex, f"ref year {y}" if y else "archaic markers")
    log.append(f"examples checked: {len(rows)}, archaic found: {len(archaic)}")
    print(f"archaic examples: {len(archaic)}")

    # ---- 2b. replacement candidates for archaic words ----
    replaced = []
    still = []
    if archaic:
        pat2 = WORK / "v25_word_patterns.txt"
        with pat2.open("w", encoding="utf-8") as f:
            for w in archaic:
                f.write(f'"word": "{w}"\n')
        matched2 = WORK / "v25_word_matched.jsonl"
        grep_prefilter(pat2, matched2)
        candidates = {}  # word -> [(text, year, pos)]
        with matched2.open(encoding="utf-8") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("lang_code") != "en":
                    continue
                w = (e.get("word") or "").strip().lower()
                if w not in archaic:
                    continue
                for s in e.get("senses") or []:
                    for ex in s.get("examples") or []:
                        t = ex.get("text") or ""
                        if t:
                            candidates.setdefault(w, []).append(
                                (t, ref_year(ex.get("ref")), e.get("pos"))
                            )
        for w, (pos, old, reason) in archaic.items():
            cands = candidates.get(w, [])
            pick = None
            for prefer_pos in (pos, None):
                for t, y, p in cands:
                    if t == old or is_archaic_text(t):
                        continue
                    if y is not None and y < YEAR_CUTOFF:
                        continue
                    if prefer_pos is not None and p != prefer_pos:
                        continue
                    pick = t
                    break
                if pick:
                    break
            if pick:
                cur.execute(
                    "UPDATE words SET example=? WHERE word=?", (pick, w)
                )
                replaced.append((w, old, pick, reason))
            else:
                still.append((w, old, reason))
        conn.commit()
    log.append(f"examples replaced: {len(replaced)}, still archaic: {len(still)}")
    for w, old, new, reason in replaced:
        log.append(f"  REPLACED {w} [{reason}]: {old[:60]!r} -> {new[:60]!r}")
    for w, old, reason in still:
        log.append(f"  STILL {w} [{reason}]: {old[:60]!r}")

    # ---- 3. same definition fixes in the wordlist CSV ----
    wl_fixed = 0
    if WORDLIST.exists():
        rows = list(csv.DictReader(WORDLIST.open(encoding="utf-8")))
        for r in rows:
            if r["word"] in FUNC_FIXES:
                pos, definition = FUNC_FIXES[r["word"]]
                r["pos"] = pos
                r["definition_en"] = definition
                wl_fixed += 1
        with WORDLIST.open("w", encoding="utf-8", newline="") as f:
            wr = csv.DictWriter(
                f, fieldnames=["freq_rank", "word", "pos", "definition_en", "gloss_id"]
            )
            wr.writeheader()
            wr.writerows(rows)
    log.append(f"wordlist rows fixed: {wl_fixed}")

    total = cur.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    with_gloss = cur.execute(
        "SELECT COUNT(*) FROM words WHERE gloss_id IS NOT NULL AND gloss_id <> ''"
    ).fetchone()[0]
    with_ex = cur.execute(
        "SELECT COUNT(*) FROM words WHERE example IS NOT NULL AND example <> ''"
    ).fetchone()[0]
    log.append(f"v25 totals: words={total}, with_gloss={with_gloss}, with_example={with_ex}")
    conn.close()
    REPORT.write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    print("REPORT:", REPORT)


if __name__ == "__main__":
    sys.exit(main())
