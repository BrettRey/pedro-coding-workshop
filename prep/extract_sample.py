"""
Extract Set A marker tokens with full context for LLM classification.
Outputs a TSV that can be fed to an LLM for ergative/possessive/other tagging.
"""

import re
import os
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
OUT_FILE = os.path.join(os.path.dirname(__file__), 'set_a_tokens.tsv')

CHILDREN = {
    'CB': {'name': 'Brendo', 'code': 'B', 'age': '?'},
    'CF': {'name': 'Francisco', 'code': 'F', 'age': '1;7.6'},
    'CI': {'name': 'Isabel', 'code': 'I', 'age': '2;0.22'},
    'CM': {'name': 'Mateo', 'code': 'M', 'age': '2;1.26'},
    'CY': {'name': 'Yeseña', 'code': 'Y', 'age': '2;0.22'},
}

SPANISH_STOPS = {
    'yo', 'ya', 'hay', 'han', 'has', 'ha', 'haya', 'son', 'si', 'sí',
    'se', 'su', 'sus', 'sin', 'ser', 'sea', 'solo', 'sobre',
    'como', 'con', 'cosa', 'cosas', 'haber', 'hacer', 'hasta', 'hacia',
    'seguro', 'siempre', 'señor', 'señora', 'ye', 'yes',
}
CHUJ_STOPS = {'han', 'hann', 'hannn', 'hi', "hi'", "hi'i", "hi'i'"}
ALL_STOPS = SPANISH_STOPS | CHUJ_STOPS


def read_normalized(filepath):
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text.split('\n')


def parse_file(filepath):
    lines = read_normalized(filepath)
    utterances = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('+') or line == '':
            i += 1
            continue
        if re.match(r'^[A-Z]\(', line) and i < 15:
            i += 1
            continue
        break
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('+'):
            i += 1
            continue
        speaker_match = re.match(r'^([A-Z])\s+(.+)', line)
        if not speaker_match:
            i += 1
            continue
        speaker = speaker_match.group(1)
        child_production = speaker_match.group(2).strip()
        adult_form = ''
        spanish = ''
        j = i + 1
        while j < len(lines):
            next_line = lines[j].strip()
            if next_line.startswith('= ') or next_line.startswith('='):
                adult_form = re.sub(r'^=\s*', '', next_line).strip()
                j += 1
            elif next_line.startswith('%spa') or next_line.startswith('%span'):
                spanish = re.sub(r'^%spa[n]?\s*', '', next_line).strip()
                j += 1
            else:
                break
        utterances.append({
            'speaker': speaker,
            'child_production': child_production,
            'adult_form': adult_form,
            'spanish': spanish,
        })
        i = j if j > i + 1 else i + 1
    return utterances


def classify_marker(word):
    clean = re.sub(r'[.,;:!?¿¡]', '', word).strip("'").lower()
    if len(clean) < 3 or clean in ALL_STOPS:
        return None
    if re.match(r'^hin', clean) and len(clean) > 3:
        return ('1SG', clean)
    if re.match(r'^ha[a-z]', clean) and len(clean) > 3:
        return ('2SG', clean)
    if re.match(r'^s[bcdfghjklmnñpqrstvwxyz\']', clean) and len(clean) > 3:
        return ('3SG', clean)
    if re.match(r"^y[aeiou'']", clean) and len(clean) > 3:
        return ('3SG', clean)
    if re.match(r'^ko[a-z]', clean) and len(clean) > 3:
        return ('1PL', clean)
    return None


if __name__ == '__main__':
    txt_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.txt'))
    rows = []

    for fname in txt_files:
        fpath = os.path.join(DATA_DIR, fname)
        child_key = fname[:2]
        child_info = CHILDREN.get(child_key, {})
        child_speaker = child_info.get('code', '?')

        utterances = parse_file(fpath)

        for u in utterances:
            text = u['adult_form'] if u['adult_form'] else u['child_production']
            text_clean = re.sub(r'\([^)]*\)', '', text)

            for word in text_clean.split():
                result = classify_marker(word)
                if result is None:
                    continue
                person, clean = result
                role = 'child' if u['speaker'] == child_speaker else 'adult'

                rows.append({
                    'file': fname,
                    'child': child_info.get('name', '?'),
                    'age': child_info.get('age', '?'),
                    'role': role,
                    'person': person,
                    'token': clean,
                    'chuj_full': u['adult_form'][:80] if u['adult_form'] else u['child_production'][:80],
                    'spanish': u['spanish'][:80],
                })

    # Write TSV
    with open(OUT_FILE, 'w') as f:
        headers = ['file', 'child', 'age', 'role', 'person', 'token',
                   'chuj_full', 'spanish']
        f.write('\t'.join(headers) + '\n')
        for row in rows:
            f.write('\t'.join(row[h] for h in headers) + '\n')

    print(f"Wrote {len(rows)} tokens to {OUT_FILE}")

    # Summary
    child_rows = [r for r in rows if r['role'] == 'child']
    adult_rows = [r for r in rows if r['role'] == 'adult']
    print(f"  Child tokens: {len(child_rows)}")
    print(f"  Adult tokens: {len(adult_rows)}")
