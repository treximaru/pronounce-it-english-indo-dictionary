#!/usr/bin/env python3
"""
Build prototype dictionary dataset: 1,000 most frequent English words.
Sources (all open):
  - wordfreq: frequency ranking (top_n_word_list 'en', 1500)
  - NLTK WordNet: POS, English definition, example sentence
  - NLTK cmudict: ARPAbet phonemes -> syllable count, stress, IPA (US)
ipa_uk is left NULL for later Kaikki/Wiktionary enrichment (not fabricated).
Output: data/kamus_prototype.sqlite + data/dataset_stats.json
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "kamus_prototype.sqlite"
STATS_PATH = BASE / "data" / "dataset_stats.json"

TARGET = 1000
POOL = 1500

# ---------- ARPAbet -> IPA mapping (standard) ----------
VOWELS = {
    "AA": "ɑ", "AE": "æ", "AH": None,  # AH special: ʌ stressed / ə unstressed
    "AO": "ɔ", "AW": "aʊ", "AY": "aɪ", "EH": "ɛ", "ER": None,  # ɝ / ɚ
    "EY": "eɪ", "IH": "ɪ", "IY": "i", "OW": "oʊ", "OY": "ɔɪ",
    "UH": "ʊ", "UW": "u",
}
CONSONANTS = {
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f", "G": "ɡ",
    "HH": "h", "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n",
    "NG": "ŋ", "P": "p", "R": "r", "S": "s", "SH": "ʃ", "T": "t",
    "TH": "θ", "V": "v", "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}
POS_MAP = {"n": "noun", "v": "verb", "a": "adjective", "s": "adjective", "r": "adverb"}


def split_phoneme(ph):
    m = re.match(r"^([A-Z]+)([012])?$", ph)
    return m.group(1), (m.group(2) or "")


def phoneme_ipa(base, stress):
    if base in CONSONANTS:
        return CONSONANTS[base]
    if base == "AH":
        return "ʌ" if stress in ("1", "2") else "ə"
    if base == "ER":
        return "ɝ" if stress in ("1", "2") else "ɚ"
    return VOWELS.get(base, base.lower())


def analyze_pronunciation(phones):
    """phones: list like ['EH1','JH','AH0',...]. Returns dict or None."""
    parsed = [split_phoneme(p) for p in phones]
    vowel_idx = [i for i, (b, _) in enumerate(parsed) if b in VOWELS]
    if not vowel_idx:
        return None
    # syllable boundaries (onset maximization, coda keeps 1 consonant if cluster >=2)
    bounds = []
    for k in range(1, len(vowel_idx)):
        prev_v, this_v = vowel_idx[k - 1], vowel_idx[k]
        cluster = this_v - prev_v - 1
        if cluster == 0:
            bounds.append(this_v)
        elif cluster == 1:
            bounds.append(this_v - 1)
        else:
            bounds.append(prev_v + 2)
    syll_phonemes = []
    start = 0
    for b in bounds + [len(parsed)]:
        syll_phonemes.append(parsed[start:b])
        start = b
    # IPA per syllable
    syll_ipa = ["".join(phoneme_ipa(b, s) for b, s in syl) for syl in syll_phonemes]
    # full IPA with stress marks
    ipa_parts = []
    stress_index = None
    secondary_index = None
    for si, syl in enumerate(syll_phonemes):
        txt = "".join(phoneme_ipa(b, s) for b, s in syl)
        vstress = next((s for b, s in syl if b in VOWELS), "")
        if vstress == "1":
            stress_index = si + 1
            txt = "ˈ" + txt
        elif vstress == "2":
            if secondary_index is None:
                secondary_index = si + 1
            txt = "ˌ" + txt
        ipa_parts.append(txt)
    if stress_index is None:
        stress_index = secondary_index if secondary_index is not None else (1 if len(syll_phonemes) == 1 else None)
    return {
        "ipa": "".join(ipa_parts),
        "syllables": "·".join(syll_ipa),
        "syllable_count": len(syll_phonemes),
        "stress_index": stress_index,
    }


def main():
    import nltk
    for cand in (BASE / "data" / "nltk_data", Path("/tmp/kamus_nltk")):
        if cand.exists():
            nltk.data.path.append(str(cand))
    from nltk.corpus import cmudict, wordnet as wn
    try:
        from wordfreq import top_n_word_list
    except ImportError:  # wordfreq >= 3.x renamed the function
        from wordfreq import top_n_list as top_n_word_list

    pool = top_n_word_list("en", POOL)
    cmu = cmudict.dict()

    rows = []
    skipped_no_wordnet = 0
    for rank, word in enumerate(pool, start=1):
        if len(rows) >= TARGET:
            break
        w = word.lower().strip()
        if not re.fullmatch(r"[a-z][a-z\-']*", w) or "-" in w or "'" in w:
            continue
        if len(w) < 2 and w not in ("a", "i"):
            continue
        synsets = wn.synsets(w)
        if not synsets:
            skipped_no_wordnet += 1
            continue
        syn = synsets[0]
        definition = syn.definition()
        example = None
        for s in synsets:
            ex = s.examples()
            if ex:
                example = ex[0]
                break
        pron = None
        entries = cmu.get(w)
        if entries:
            pron = analyze_pronunciation(entries[0])
        rows.append({
            "word": w,
            "pos": POS_MAP.get(syn.pos(), syn.pos()),
            "definition_en": definition,
            "example": example,
            "ipa_us": pron["ipa"] if pron else None,
            "ipa_uk": None,
            "syllables": pron["syllables"] if pron else None,
            "syllable_count": pron["syllable_count"] if pron else None,
            "stress_index": pron["stress_index"] if pron else None,
            "freq_rank": rank,
            "gloss_id": None,
        })

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE words (
            id INTEGER PRIMARY KEY,
            word TEXT NOT NULL UNIQUE,
            pos TEXT,
            definition_en TEXT,
            example TEXT,
            ipa_us TEXT,
            ipa_uk TEXT,
            syllables TEXT,
            syllable_count INTEGER,
            stress_index INTEGER,
            freq_rank INTEGER,
            gloss_id TEXT
        )
    """)
    cur.executemany(
        "INSERT INTO words (word,pos,definition_en,example,ipa_us,ipa_uk,syllables,syllable_count,stress_index,freq_rank,gloss_id)"
        " VALUES (:word,:pos,:definition_en,:example,:ipa_us,:ipa_uk,:syllables,:syllable_count,:stress_index,:freq_rank,:gloss_id)",
        rows,
    )
    cur.execute("CREATE VIRTUAL TABLE words_fts USING fts5(word, definition_en, content='words', content_rowid='id')")
    cur.execute("INSERT INTO words_fts(words_fts) VALUES('rebuild')")
    cur.execute("""
        CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)
    """)
    cur.executemany("INSERT INTO metadata VALUES (?,?)", [
        ("source_frequency", "wordfreq top_n_word_list('en', 1500)"),
        ("source_definition", "NLTK WordNet (Open English WordNet via NLTK)"),
        ("source_pronunciation", "NLTK cmudict (CMU Pronouncing Dictionary), ARPAbet->IPA"),
        ("ipa_uk_note", "NULL in prototype; Kaikki/Wiktionary enrichment in next stage"),
        ("row_count", str(len(rows))),
    ])
    conn.commit()

    total = len(rows)
    stats = {
        "total_rows": total,
        "pool_size": POOL,
        "skipped_no_wordnet_in_pool_scan": skipped_no_wordnet,
        "with_example": sum(1 for r in rows if r["example"]),
        "with_example_pct": round(100 * sum(1 for r in rows if r["example"]) / total, 1) if total else 0,
        "with_syllables": sum(1 for r in rows if r["syllables"]),
        "with_syllables_pct": round(100 * sum(1 for r in rows if r["syllables"]) / total, 1) if total else 0,
        "with_stress": sum(1 for r in rows if r["stress_index"]),
        "with_ipa_us": sum(1 for r in rows if r["ipa_us"]),
        "with_ipa_uk": 0,
    }
    STATS_PATH.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    for probe in ("education", "pronunciation", "beautiful", "important", "computer"):
        cur.execute("SELECT word,pos,definition_en,example,ipa_us,syllables,syllable_count,stress_index,freq_rank FROM words WHERE word=?", (probe,))
        print(probe, "->", cur.fetchone())
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
