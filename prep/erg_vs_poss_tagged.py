"""
Produce a row-by-row tagged TSV using the Spanish-translation regex
heuristics, matching the format of child_tokens_classified.tsv.
"""

import re
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
IN_FILE = os.path.join(os.path.dirname(__file__), 'child_tokens.tsv')
OUT_FILE = os.path.join(os.path.dirname(__file__), 'child_tokens_regex.tsv')

POSS_PATTERNS = {
    '1SG': r'\b(mi|mío|mía|mis|míos|mías)\b',
    '2SG': r'\b(tu|tuyo|tuya|tus|tuyos|tuyas)\b',
    '3SG': r'\b(su|suyo|suya|sus|suyos|suyas|de él|de ella)\b',
    '1PL': r'\b(nuestro|nuestra|nuestros|nuestras)\b',
}

VERB_PATTERNS = {
    '1SG': r'\b(yo\s+\w+|me\s+\w+|lo\s+\w+é|hago|pongo|llevo|cargo|traigo)\b',
    '2SG': r'\b(tú\s+\w+|te\s+\w+|haces|pones|llevas)\b',
    '3SG': r'\b(él\s+\w+|ella\s+\w+|lo\s+\w+a|la\s+\w+a|hace|pone|lleva|va|fue|se fue|está)\b',
    '1PL': r'\b(nosotros|hacemos|ponemos|vamos|llevamos)\b',
}


def classify(person, spanish):
    if not spanish or spanish.strip() == '( )':
        return 'no_spa', 'no Spanish translation available'

    spa = spanish.lower()

    has_poss = bool(re.search(POSS_PATTERNS.get(person, r'$^'), spa))
    de_poss = bool(re.search(r'\bde\s+(mi|tu|su|nuestro|nuestra)', spa))
    has_verb = bool(re.search(VERB_PATTERNS.get(person, r'$^'), spa))

    if has_poss or de_poss:
        if has_verb:
            return 'ambiguous', f'poss signal ({has_poss or de_poss}) + verb signal'
        match = re.search(POSS_PATTERNS.get(person, r'$^'), spa)
        de_match = re.search(r'\bde\s+(mi|tu|su|nuestro|nuestra)', spa)
        trigger = (match.group() if match else de_match.group() if de_match else '?')
        return 'poss', f'Spanish contains possessive: "{trigger}"'
    elif has_verb:
        match = re.search(VERB_PATTERNS.get(person, r'$^'), spa)
        trigger = match.group() if match else '?'
        return 'erg', f'Spanish contains verbal cue: "{trigger}"'
    else:
        return 'ambiguous', 'no possessive or verbal signal detected'


if __name__ == '__main__':
    with open(IN_FILE) as f:
        lines = f.readlines()

    header = lines[0].strip()
    rows = [l.strip().split('\t') for l in lines[1:]]

    with open(OUT_FILE, 'w') as f:
        f.write(header + '\tfunction\tnotes\n')
        for row in rows:
            person = row[4]
            spanish = row[7] if len(row) > 7 else ''
            func, notes = classify(person, spanish)
            f.write('\t'.join(row) + f'\t{func}\t{notes}\n')

    # Summary
    from collections import Counter
    funcs = Counter()
    child_funcs = {}
    for row in rows:
        person = row[4]
        spanish = row[7] if len(row) > 7 else ''
        child = row[1]
        func, _ = classify(person, spanish)
        funcs[func] += 1
        if child not in child_funcs:
            child_funcs[child] = Counter()
        child_funcs[child][func] += 1

    print(f"Wrote {len(rows)} tagged rows to {OUT_FILE}")
    print(f"\nOverall: {dict(funcs)}")
    print(f"\nBy child:")
    for child in sorted(child_funcs):
        print(f"  {child}: {dict(child_funcs[child])}")
