"""One-off: add pos_all column to kamus_v26.sqlite from Kaikki staging data.

The words.pos column holds only WordNet's FIRST synset pos (e.g. "run"->noun),
while Kaikki (Wiktionary) has every part of speech per word. This fills
pos_all with the full list, canonically ordered, e.g. "verb,noun,adjective".
"""
import sqlite3

KAMUS = "/home/hatch/workspace/projects/kamus-pronunciation/data/kamus_v26.sqlite"
KAIKKI = "/home/hatch/workspace/projects/kamus-pronunciation/data/kaikki_staging.sqlite"

ORDER = ["verb", "noun", "adjective", "adverb", "pronoun", "preposition",
         "conjunction", "interjection", "determiner", "article", "numeral",
         "particle", "contraction", "proper noun", "phrase", "proverb"]
ORDER_IDX = {p: i for i, p in enumerate(ORDER)}


def canon(pos_list):
    out = []
    for p in pos_list:
        p = "proper noun" if p == "name" else p
        if p not in out:
            out.append(p)
    out.sort(key=lambda p: (ORDER_IDX.get(p, 99), p))
    return ",".join(out)


def main():
    kk = sqlite3.connect("file:%s?mode=ro" % KAIKKI, uri=True)
    # lemma pos first
    lemma = {}
    for w, pp in kk.execute(
            "SELECT word, GROUP_CONCAT(DISTINCT pos) FROM kaikki "
            "WHERE is_form=0 GROUP BY word"):
        lemma[w] = pp.split(",")
    # fallback: inflected-form rows
    form = {}
    for w, pp in kk.execute(
            "SELECT word, GROUP_CONCAT(DISTINCT pos) FROM kaikki "
            "WHERE is_form=1 GROUP BY word"):
        form[w] = pp.split(",")
    kk.close()

    db = sqlite3.connect(KAMUS)
    words = [r[0] for r in db.execute("SELECT word, pos FROM words")]
    print("words in kamus:", len(words))

    try:
        db.execute("ALTER TABLE words ADD COLUMN pos_all TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise
        print("pos_all already exists, will overwrite")

    n_lemma = n_form = n_fallback = 0
    rows = []
    # need old pos for fallback; re-read with pos
    for w, old_pos in db.execute("SELECT word, pos FROM words"):
        pl = lemma.get(w)
        if pl:
            n_lemma += 1
        else:
            pl = form.get(w)
            if pl:
                n_form += 1
            else:
                pl = [old_pos] if old_pos else []
                n_fallback += 1
        rows.append((canon(pl), w))
    db.executemany("UPDATE words SET pos_all=? WHERE word=?", rows)
    db.commit()

    # spot checks
    for w in ["run", "go", "went", "beautiful", "computer"]:
        r = db.execute("SELECT pos, pos_all FROM words WHERE word=?",
                       (w,)).fetchone()
        print(f"{w:10s} pos={r[0]!r:12s} pos_all={r[1]!r}")
    print(f"lemma={n_lemma} form_fallback={n_form} old_pos_fallback={n_fallback}")
    db.close()


if __name__ == "__main__":
    main()
