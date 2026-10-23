#!/usr/bin/env python3
"""
Stage 2 enrichment: Kaikki/Wiktionary -> kamus_v2.sqlite.

Inputs (all open sources):
  - data/kaikki-en.jsonl  (wiktextract dump of English Wiktionary, via kaikki.org; CC BY-SA)
  - data/kamus_prototype.sqlite (stage 1: wordfreq + WordNet + CMUdict)
  - NLTK cmudict (syllable/stress for expanded words), zips archived in data/corpora_zips/
  - wordfreq (ranking for expansion ordering)

Phase A streams the 3.4 GB JSONL into a disk staging DB (RAM stays flat):
  data/kaikki_staging.sqlite, table kaikki(word, pos, ipa_uk, ipa_us, definition, example, gloss_id, is_form)
Phase B merges: prototype words get ipa_uk/gloss_id filled; new headwords are
added ranked by wordfreq until --target-total rows. Nothing is fabricated:
missing values stay NULL.

Output: data/kamus_v2.sqlite (same schema as prototype) + data/dataset_v2_stats.json
"""
import argparse
import json
import re
import sqlite3
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
JSONL_PATH = DATA / "kaikki-en.jsonl"
STAGING_PATH = DATA / "kaikki_staging.sqlite"
PROTO_PATH = DATA / "kamus_prototype.sqlite"
V2_PATH = DATA / "kamus_v2.sqlite"
STATS_PATH = DATA / "dataset_v2_stats.json"

sys.path.insert(0, str(BASE / "scripts"))
from build_dataset import analyze_pronunciation  # noqa: E402  (reuse ARPAbet->IPA)

WORD_RE = re.compile(r"^[a-z][a-z' \-]*$")
UK_TAG_HINTS = ("uk", "received", "british", "england", "rp")
US_TAG_HINTS = ("us", "general-american", "american", "ga")
POS_NORM = {"adj": "adjective", "adv": "adverb", "intj": "interjection",
            "prep": "preposition", "conj": "conjunction", "pron": "pronoun",
            "det": "determiner", "num": "numeral"}


def clean_ipa(ipa):
    if not ipa:
        return None
    ipa = ipa.strip().strip("/[]").strip()
    return ipa or None


def _tag_class(tags):
    """Classify a sound's tag list as 'uk', 'us', 'old', or None (token-based,
    so e.g. 'Australia' never matches 'us')."""
    for t in (tags or []):
        tl = str(t).lower()
        if "received" in tl or tl in ("uk", "british", "rp", "england") or tl.startswith("uk-"):
            return "uk"
        if "general-american" in tl or tl in ("us", "american", "ga") or tl.startswith("us-"):
            return "us"
        if tl in ("obsolete", "archaic", "dated", "rare"):
            return "old"
    return None


def classify_ipa(sounds):
    """Return (ipa_uk, ipa_us, ipa_other). ipa_other = first untagged broad
    transcription (many Wiktionary headwords, e.g. 'pronunciation', carry no
    region tag at all; it is kept separate and must NOT be relabelled UK/US)."""
    uk = us = other = other_narrow = None
    for s in sounds or []:
        raw = (s.get("ipa") or "").strip()
        ipa = clean_ipa(raw)
        if not ipa:
            continue
        cls = _tag_class(s.get("tags"))
        if cls == "uk" and uk is None:
            uk = ipa
        elif cls == "us" and us is None:
            us = ipa
        elif cls is None:
            if raw.startswith("["):
                if other_narrow is None:
                    other_narrow = ipa
            elif other is None:
                other = ipa
    return uk, us, other or other_narrow


def first_gloss_and_example(senses):
    definition = example = None
    for s in senses or []:
        if definition is None:
            glosses = s.get("glosses") or []
            if glosses:
                definition = glosses[0].strip() or None
        if example is None:
            for ex in s.get("examples") or []:
                text = (ex.get("text") or "").strip()
                if text:
                    example = text
                    break
        if definition and example:
            break
    return definition, example


def first_id_translation(entry):
    pools = list(entry.get("translations") or [])
    for s in entry.get("senses") or []:
        pools.extend(s.get("translations") or [])
    for t in pools:
        if t.get("lang_code") == "id":
            w = (t.get("word") or "").strip()
            if w:
                return w
    return None


def is_form_entry(entry):
    senses = entry.get("senses") or []
    if not senses:
        return True
    return all("form_of" in s for s in senses)


# ---------------- Phase A: stream JSONL -> staging ----------------

def phase_a():
    if STAGING_PATH.exists():
        print(f"staging already exists ({STAGING_PATH.stat().st_size} bytes) - skipping phase A")
        return
    conn = sqlite3.connect(STAGING_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE kaikki (
            word TEXT NOT NULL,
            pos TEXT,
            ipa_uk TEXT,
            ipa_us TEXT,
            ipa_other TEXT,
            definition TEXT,
            example TEXT,
            gloss_id TEXT,
            is_form INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (word, pos)
        )
    """)
    batch = []
    n_lines = n_en = 0
    with JSONL_PATH.open(encoding="utf-8") as f:
        for line in f:
            n_lines += 1
            if n_lines % 200_000 == 0:
                print(f"  phase A: {n_lines} lines, {n_en} entries kept", flush=True)
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("lang_code") != "en":
                continue
            word = (entry.get("word") or "").strip().lower()
            if not WORD_RE.fullmatch(word) or (len(word) < 2 and word not in ("a", "i")):
                continue
            pos = POS_NORM.get(entry.get("pos") or "", entry.get("pos"))
            ipa_uk, ipa_us, ipa_other = classify_ipa(entry.get("sounds"))
            definition, example = first_gloss_and_example(entry.get("senses"))
            gloss_id = first_id_translation(entry)
            form = 1 if is_form_entry(entry) else 0
            n_en += 1
            batch.append((word, pos, ipa_uk, ipa_us, ipa_other, definition, example, gloss_id, form))
            if len(batch) >= 5000:
                _flush(cur, batch)
                batch = []
                conn.commit()
    if batch:
        _flush(cur, batch)
    conn.commit()
    total = cur.execute("SELECT COUNT(*) FROM kaikki").fetchone()[0]
    with_uk = cur.execute("SELECT COUNT(*) FROM kaikki WHERE ipa_uk IS NOT NULL").fetchone()[0]
    print(f"phase A done: {n_lines} lines, {n_en} entries -> {total} staged rows, {with_uk} with ipa_uk")
    conn.close()


def _flush(cur, batch):
    cur.executemany(
        "INSERT OR IGNORE INTO kaikki (word,pos,ipa_uk,ipa_us,ipa_other,definition,example,gloss_id,is_form)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        batch,
    )
    # fill NULLs from later entries for the same (word,pos)
    for row in batch:
        cur.execute(
            "UPDATE kaikki SET"
            " ipa_uk=COALESCE(ipa_uk,?), ipa_us=COALESCE(ipa_us,?), ipa_other=COALESCE(ipa_other,?),"
            " definition=COALESCE(definition,?), example=COALESCE(example,?),"
            " gloss_id=COALESCE(gloss_id,?) WHERE word=? AND pos=?",
            (row[2], row[3], row[4], row[5], row[6], row[7], row[0], row[1]),
        )


# ---------------- Phase B: merge -> kamus_v2 ----------------

def load_cmu():
    nltk_dir = Path("/tmp/kamus_nltk")
    corpus_dir = nltk_dir / "corpora" / "cmudict"
    if not corpus_dir.exists():
        zips = DATA / "corpora_zips"
        nltk_dir.mkdir(parents=True, exist_ok=True)
        for z in zips.glob("*.zip"):
            with zipfile.ZipFile(z) as zf:
                zf.extractall(nltk_dir / "corpora")
    import nltk
    nltk.data.path.append(str(nltk_dir))
    from nltk.corpus import cmudict
    return cmudict.dict()


def phase_b(target_total):
    from wordfreq import top_n_list
    rank_of = {w: i + 1 for i, w in enumerate(top_n_list("en", 300_000))}

    staging = sqlite3.connect(STAGING_PATH)
    staging.row_factory = sqlite3.Row
    proto = sqlite3.connect(PROTO_PATH)
    proto.row_factory = sqlite3.Row
    cmu = load_cmu()

    def staging_merged(word):
        """Merge all (word,*) staging rows: first non-NULL per field wins."""
        merged = {"pos": None, "ipa_uk": None, "ipa_us": None, "ipa_other": None,
                  "definition": None, "example": None, "gloss_id": None}
        for r in staging.execute(
                "SELECT * FROM kaikki WHERE word=? ORDER BY is_form, (ipa_uk IS NULL)",
                (word,)):
            for k in merged:
                if merged[k] is None and r[k]:
                    merged[k] = r[k]
        return merged

    rows = []
    proto_words = set()
    for pr in proto.execute("SELECT * FROM words ORDER BY freq_rank"):
        w = dict(pr)
        proto_words.add(w["word"])
        st = staging_merged(w["word"])
        if not w["ipa_uk"]:
            w["ipa_uk"] = st["ipa_uk"]
        if not w["ipa_us"]:
            w["ipa_us"] = st["ipa_us"]
        w["ipa_other"] = st["ipa_other"]
        if not w["gloss_id"]:
            w["gloss_id"] = st["gloss_id"]
        rows.append(w)

    # expansion candidates: real headwords with a definition; IPA buckets are
    # merged across the word's POS rows, then words with no IPA at all are dropped
    cand = staging.execute(
        "SELECT * FROM kaikki WHERE is_form=0 AND definition IS NOT NULL").fetchall()
    best_by_word = {}
    for c in cand:
        w = c["word"]
        if w in proto_words:
            continue
        g = best_by_word.get(w)
        if g is None:
            g = {"word": w, "pos": c["pos"], "definition": c["definition"],
                 "example": c["example"], "gloss_id": c["gloss_id"],
                 "ipa_uk": None, "ipa_us": None, "ipa_other": None}
            best_by_word[w] = g
        for k in ("ipa_uk", "ipa_us", "ipa_other", "example", "gloss_id"):
            if g[k] is None and c[k]:
                g[k] = c[k]
    best_by_word = {w: g for w, g in best_by_word.items()
                    if g["ipa_uk"] or g["ipa_us"] or g["ipa_other"]}
    ordered = sorted(
        best_by_word.values(),
        key=lambda c: (rank_of.get(c["word"], 10**9), c["word"]),
    )
    room = max(0, target_total - len(rows))
    added = 0
    for c in ordered:
        if added >= room:
            break
        pron = None
        entries = cmu.get(c["word"])
        if entries:
            pron = analyze_pronunciation(entries[0])
        rows.append({
            "word": c["word"],
            "pos": c["pos"],
            "definition_en": c["definition"],
            "example": c["example"],
            "ipa_us": c["ipa_us"] or (pron["ipa"] if pron else None),
            "ipa_uk": c["ipa_uk"],
            "ipa_other": c["ipa_other"],
            "syllables": pron["syllables"] if pron else None,
            "syllable_count": pron["syllable_count"] if pron else None,
            "stress_index": pron["stress_index"] if pron else None,
            "freq_rank": rank_of.get(c["word"]),
            "gloss_id": c["gloss_id"],
        })
        added += 1
    print(f"phase B: {len(rows)} total rows ({len(proto_words)} prototype + {added} new)")

    if V2_PATH.exists():
        V2_PATH.unlink()
    out = sqlite3.connect(V2_PATH)
    cur = out.cursor()
    cur.execute("""
        CREATE TABLE words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            pos TEXT,
            definition_en TEXT,
            example TEXT,
            ipa_us TEXT,
            ipa_uk TEXT,
            ipa_other TEXT,
            syllables TEXT,
            syllable_count INTEGER,
            stress_index INTEGER,
            freq_rank INTEGER,
            gloss_id TEXT
        )
    """)
    cur.executemany(
        "INSERT INTO words (word,pos,definition_en,example,ipa_us,ipa_uk,ipa_other,syllables,syllable_count,stress_index,freq_rank,gloss_id)"
        " VALUES (:word,:pos,:definition_en,:example,:ipa_us,:ipa_uk,:ipa_other,:syllables,:syllable_count,:stress_index,:freq_rank,:gloss_id)",
        rows,
    )
    cur.execute("CREATE VIRTUAL TABLE words_fts USING fts5(word, definition_en, content='words', content_rowid='id')")
    cur.execute("INSERT INTO words_fts(words_fts) VALUES('rebuild')")
    cur.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
    cur.executemany("INSERT INTO metadata VALUES (?,?)", [
        ("stage", "v2 - Kaikki/Wiktionary enrichment"),
        ("source_ipa_uk", "Kaikki.org wiktextract dump of English Wiktionary (CC BY-SA), sounds tagged UK/RP"),
        ("source_ipa_other", "Wiktionary broad transcription without a region tag (Kaikki/wiktextract); shown unlabelled, never relabelled UK/US"),
        ("source_definition_base", "NLTK WordNet (prototype 1000)"),
        ("source_definition_expansion", "Wiktionary glosses via Kaikki/wiktextract (CC BY-SA)"),
        ("source_pronunciation_us", "NLTK cmudict (CMU Pronouncing Dictionary), ARPAbet->IPA; Wiktionary US-tagged sounds as fallback"),
        ("source_gloss_id", "Wiktionary translations (lang_code=id) via Kaikki/wiktextract; NULL where none"),
        ("source_frequency", "wordfreq"),
        ("row_count", str(len(rows))),
    ])
    out.commit()

    total = len(rows)
    stats = {
        "total_rows": total,
        "prototype_rows": len(proto_words),
        "new_rows": added,
        "with_ipa_uk": sum(1 for r in rows if r["ipa_uk"]),
        "with_ipa_uk_pct": round(100 * sum(1 for r in rows if r["ipa_uk"]) / total, 1),
        "with_ipa_us": sum(1 for r in rows if r["ipa_us"]),
        "with_ipa_other": sum(1 for r in rows if r.get("ipa_other")),
        "with_any_ipa": sum(1 for r in rows if r["ipa_uk"] or r["ipa_us"] or r.get("ipa_other")),
        "with_any_ipa_pct": round(100 * sum(1 for r in rows if r["ipa_uk"] or r["ipa_us"] or r.get("ipa_other")) / total, 1),
        "with_syllables": sum(1 for r in rows if r["syllables"]),
        "with_example": sum(1 for r in rows if r["example"]),
        "with_gloss_id": sum(1 for r in rows if r["gloss_id"]),
        "with_gloss_id_pct": round(100 * sum(1 for r in rows if r["gloss_id"]) / total, 1),
    }
    STATS_PATH.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    for probe in ("education", "pronunciation", "computer", "beautiful", "vowel"):
        cur.execute("SELECT word,pos,ipa_uk,ipa_us,ipa_other,gloss_id FROM words WHERE word=?", (probe,))
        print(probe, "->", cur.fetchone())
    out.close()
    staging.close()
    proto.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-total", type=int, default=120_000)
    ap.add_argument("--phase", choices=("a", "b", "ab"), default="ab")
    args = ap.parse_args()
    if "a" in args.phase:
        phase_a()
    if "b" in args.phase:
        phase_b(args.target_total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
