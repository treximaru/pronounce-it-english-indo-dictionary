"""One-off: rebuild pos_all using Wiktionary sense counts.

Problem: pos_all listed every attested pos, including ultra-rare ones
("in" as verb = 2 archaic senses "to enclose/to harvest"; "in" as proper
noun = chemical symbol). For a learner's dictionary that's noise.

Fix: count senses per (word, pos) from the raw wiktextract JSONL and keep a
pos only if it has >=3 senses or is among the word's top-2 pos by sense
count. Order by sense count (most common first).
"""
import json
import sqlite3

KAMUS = "/home/hatch/workspace/projects/kamus-pronunciation/data/kamus_v26.sqlite"
JSONL = "/home/hatch/workspace/projects/kamus-pronunciation/data/kaikki-en.jsonl"

POS_NORM = {"adj": "adjective", "adv": "adverb", "intj": "interjection",
            "prep": "preposition", "conj": "conjunction", "pron": "pronoun",
            "det": "determiner", "num": "numeral"}

ORDER = ["verb", "noun", "adjective", "adverb", "pronoun", "preposition",
         "conjunction", "interjection", "determiner", "article", "numeral",
         "particle", "contraction", "proper noun", "phrase", "proverb"]
ORDER_IDX = {p: i for i, p in enumerate(ORDER)}


def main():
    db = sqlite3.connect(KAMUS)
    words = {r[0] for r in db.execute("SELECT word FROM words")}
    print("words:", len(words))

    counts = {}  # (word, pos) -> sense count
    n_lines = 0
    with open(JSONL, encoding="utf-8") as f:
        for line in f:
            n_lines += 1
            # cheap prefilter before json parsing
            if '"word": "' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            w = (d.get("word") or "").lower()
            if w not in words:
                continue
            pos = POS_NORM.get(d.get("pos") or "", d.get("pos") or "")
            if not pos:
                continue
            if pos == "name":
                pos = "proper noun"
            key = (w, pos)
            counts[key] = counts.get(key, 0) + len(d.get("senses") or [])
    print("lines scanned:", n_lines, "| (word,pos) pairs:", len(counts))

    # per-word ranking
    by_word = {}
    for (w, pos), n in counts.items():
        by_word.setdefault(w, []).append((pos, n))

    rows = []
    n_kept_all = 0
    for w in words:
        lst = by_word.get(w)
        if not lst:
            continue  # keep existing pos_all
        lst.sort(key=lambda kv: (-kv[1], ORDER_IDX.get(kv[0], 99)))
        keep = [pos for i, (pos, n) in enumerate(lst)
                if n >= 3 or i < 2]
        if len(keep) == len(lst):
            n_kept_all += 1
        rows.append((",".join(keep), w))
    db.executemany("UPDATE words SET pos_all=? WHERE word=?", rows)
    db.commit()

    for w in ["in", "run", "go", "beautiful", "set"]:
        r = db.execute("SELECT pos_all FROM words WHERE word=?",
                       (w,)).fetchone()
        print(f"{w:10s} -> {r[0]}")
    print(f"updated {len(rows)} words, {n_kept_all} unchanged (all pos kept)")
    db.close()


if __name__ == "__main__":
    main()
