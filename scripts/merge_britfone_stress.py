#!/usr/bin/env python3
"""
Phase F: fill syllable + stress gaps with Britfone (dataset v2.4).

Britfone (https://github.com/JoseLlarena/Britfone, MIT) is a British English
(RP) pronunciation dictionary: ~16k entries, top-10k most frequent words,
phoneme-separated IPA with primary/secondary stress marks. We derive from
its phoneme strings the same fields our CMUdict pipeline produced
(syllables as phonetic chunks joined by '·', syllable_count, stress_index
1-based) and fill ONLY rows where syllables are currently NULL — existing
data is never overwritten.

Syllabification: each vowel phoneme is a nucleus; intervocalic consonants
are split so the longest legal English onset starts the next syllable
(same family of rules as the CMU syllabify used for v2). A word-final
l/n/m right after a consonant counts as a syllabic nucleus.

Output: data/kamus_v24.sqlite = kamus_v23.sqlite + Britfone fills.
"""
import csv
import re
import shutil
import sqlite3
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
BRITFONE = DATA / "britfone.main.3.0.1.csv"
SRC_DB = DATA / "kamus_v23.sqlite"
OUT_DB = DATA / "kamus_v24.sqlite"

VOWELS = {
    "aɪ", "aʊ", "eɪ", "i", "iː", "uː", "æ", "ɐ", "ɑː", "ɒ", "ɔɪ", "ɔː",
    "ə", "əʊ", "ɛ", "ɛə", "ɜː", "ɪ", "ɪə", "ʊ", "ʊə",
}
SYLLABIC = {"l", "n", "m"}

# Legal English onsets (longest match wins), phoneme strings concatenated.
ONSETS = {
    "spl", "spr", "str", "skr", "skw", "spj", "stj", "skj",
    "pl", "pr", "pj", "tr", "tw", "kl", "kr", "kj", "kw",
    "bl", "br", "bj", "dr", "dw", "gl", "gr", "gj",
    "fl", "fr", "fj", "θr", "ʃr", "sl", "sm", "sn",
    "sp", "st", "sk", "sf",
    "b", "d", "g", "k", "p", "t", "f", "v", "θ", "ð", "s", "z",
    "ʃ", "ʒ", "tʃ", "dʒ", "m", "n", "l", "r", "ɹ", "w", "j", "h",
}


def parse_britfone():
    """word -> (phoneme list, primary-stress phoneme index)."""
    out = {}
    with BRITFONE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            raw_word, pron = line.split(",", 1)
            word = re.sub(r"\(\d+\)$", "", raw_word).strip().lower()
            if word in out:
                continue  # first pronunciation wins
            if not re.fullmatch(r"[a-z][a-z\-']*", word):
                continue  # skip multiword (_), initials, punctuation forms
            tokens = pron.split()
            phonemes, stress_at = [], None
            for tok in tokens:
                if tok.startswith(("ˈ", "ˌ")):
                    mark, base = tok[0], tok[1:]
                    if mark == "ˈ":
                        stress_at = len(phonemes)
                    phonemes.append(base)
                else:
                    phonemes.append(tok)
            if stress_at is None:
                continue  # monosyllables in Britfone still carry ˈ; be safe
            out[word] = (phonemes, stress_at)
    return out


def syllabify(phonemes, stress_at):
    """Return (chunks, stress_syllable_1based) or None if no nucleus."""
    # find nuclei: vowels, plus syllabic l/n/m after a consonant at word end
    nuclei = []
    for i, p in enumerate(phonemes):
        if p in VOWELS:
            nuclei.append(i)
        elif (p in SYLLABIC and i == len(phonemes) - 1 and i > 0
              and phonemes[i - 1] not in VOWELS):
            nuclei.append(i)
    if not nuclei:
        return None
    starts = [0]
    for n_i in range(1, len(nuclei)):
        prev_nuc, nuc = nuclei[n_i - 1], nuclei[n_i]
        cluster = phonemes[prev_nuc + 1:nuc]
        onset_len = 0
        for L in range(len(cluster), 0, -1):
            if "".join(cluster[len(cluster) - L:]) in ONSETS:
                onset_len = L
                break
        starts.append(nuc - onset_len)
    chunks = []
    stress_syll = None
    for n_i, start in enumerate(starts):
        end = starts[n_i + 1] if n_i + 1 < len(starts) else len(phonemes)
        chunks.append("".join(phonemes[start:end]))
        if start <= stress_at < end:
            stress_syll = n_i + 1  # 1-based
    return chunks, stress_syll


def main():
    brit = parse_britfone()
    print(f"britfone entries parsed: {len(brit)}")

    shutil.copyfile(SRC_DB, OUT_DB)
    conn = sqlite3.connect(OUT_DB)
    missing = [r[0] for r in conn.execute(
        "SELECT word FROM words WHERE syllables IS NULL")]
    print(f"words missing syllables: {len(missing)}")

    filled = 0
    samples = []
    for w in missing:
        if w not in brit:
            continue
        phonemes, stress_at = brit[w]
        res = syllabify(phonemes, stress_at)
        if not res:
            continue
        chunks, stress_syll = res
        if stress_syll is None:
            continue
        conn.execute(
            "UPDATE words SET syllables=?, syllable_count=?, stress_index=? "
            "WHERE word=?",
            ("·".join(chunks), len(chunks), stress_syll, w))
        filled += 1
        if len(samples) < 10 and len(chunks) >= 2:
            samples.append((w, "·".join(chunks), stress_syll))

    conn.execute(
        "INSERT OR REPLACE INTO metadata VALUES (?,?)",
        ("source_syllables_britfone",
         "Syllable/stress gap-fill v2.4: Britfone 3.0.1 (MIT), British RP "
         "phonemes syllabified with legal-onset rules; fills only NULL rows"))
    conn.commit()
    total, has_syl, has_stress = conn.execute(
        "SELECT COUNT(*), COUNT(syllables), COUNT(stress_index) FROM words"
    ).fetchone()
    print(f"filled: {filled}")
    print(f"FINAL coverage: syllables {has_syl}/{total} "
          f"({100 * has_syl / total:.1f}%), stress {has_stress}/{total} "
          f"({100 * has_stress / total:.1f}%)")
    for s in samples:
        print("sample:", s)
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
