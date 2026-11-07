
"""
Lightweight NLP inference helpers.

Used by the Astra API for text cleaning and entity extraction.
Training functionality remains in nlp.py.
"""

import re


STOPWORDS = set("""a an the of to in on at and or for with from by was were is are be been
being this that these those it its as into near over under during his her their them they
he she who whom which not no had has have will would could should complainant accused
person persons unknown unidentified reported registered stated alleged found rs""".split())


def clean_text(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"[^a-z\s]", " ", s)
    tokens = [t for t in s.split() if len(t) > 2 and t not in STOPWORDS]
    return " ".join(tokens)


ENTITY_PATTERNS = {
    "weapon": r"\b(knife|machete|iron rod|wooden club|sickle|pistol|bottle|chopper|stick|firearm)\b",
    "vehicle": r"\b(motorcycle|scooter|car|autorickshaw|auto|van|suv|moped|two-wheeler|bike)\b",
    "stolen_item": r"\b(gold ornaments|gold chain|mangalsutra|mobile phone|laptop|cash|silver articles|documents|jewellery|electronic goods)\b",
    "contraband": r"\b(ganja|mdma|arrack|brown sugar|gutka|whitener|liquor)\b",
    "amount": r"rs\s?[\d,]+",
}


def extract_entities(text: str) -> dict:
    t = str(text).lower()
    out = {}

    for label, pat in ENTITY_PATTERNS.items():
        found = sorted(set(m.group(0).strip() for m in re.finditer(pat, t)))

        if found:
            out[label] = found

    return out
