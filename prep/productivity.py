"""
Type-token analysis for Set A markers: how many distinct roots
does each marker attach to?

High tokens but few types = formulaic (rote-learned chunks).
Many types = productive morphological knowledge.
"""

import re
import os
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

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
    'como', 'con', 'cosa', 'cosas',
    'haber', 'hacer', 'hasta', 'hacia',
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


def extract_stem(word, person):
    """
    Strip the Set A prefix to get the stem/root.
    Returns the stem, or None if the word is too short after stripping.
    """
    clean = re.sub(r'[.,;:!?¿¡]', '', word).strip("'").lower()
    if person == '1SG':
        stem = re.sub(r'^hin', '', clean)
    elif person == '2SG':
        stem = re.sub(r'^ha', '', clean)
    elif person == '3SG':
        # s- or y- prefix
        if clean.startswith('y'):
            stem = clean[1:]
        else:
            stem = clean[1:]  # strip s-
    elif person == '1PL':
        stem = re.sub(r'^ko', '', clean)
    else:
        return None

    # Stem should be at least 2 characters to be meaningful
    if len(stem) < 2:
        return None
    return stem


def classify_marker(word):
    """Classify a word as containing a Set A marker. Returns (person, word) or None."""
    clean = re.sub(r'[.,;:!?¿¡]', '', word).strip("'").lower()
    if len(clean) < 2 or clean in ALL_STOPS:
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


def get_child_key(filename):
    return filename[:2]


if __name__ == '__main__':
    txt_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.txt'))
    persons = ['1SG', '2SG', '3SG', '1PL']

    # For each child: collect (person → {stem: [full_words]})
    child_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    adult_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for fname in txt_files:
        fpath = os.path.join(DATA_DIR, fname)
        child_key = get_child_key(fname)
        child_info = CHILDREN.get(child_key, {})
        child_speaker = child_info.get('code', '?')

        utterances = parse_file(fpath)

        for u in utterances:
            text = u['adult_form'] if u['adult_form'] else u['child_production']
            text = re.sub(r'\([^)]*\)', '', text)
            words = text.split()

            for word in words:
                result = classify_marker(word)
                if result is None:
                    continue
                person, clean = result
                stem = extract_stem(clean, person)
                if stem is None:
                    continue

                if u['speaker'] == child_speaker:
                    child_data[child_key][person][stem].append(clean)
                else:
                    adult_data[child_key][person][stem].append(clean)

    # ── Print type-token analysis ─────────────────────────────────────
    print("=" * 80)
    print("SET A MARKER PRODUCTIVITY: TYPE-TOKEN ANALYSIS")
    print("=" * 80)
    print()
    print("Types = distinct stems a marker attaches to")
    print("Tokens = total occurrences")
    print("TTR = type-token ratio (higher = more productive, lower = more formulaic)")

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]
        print(f"\n{'━' * 80}")
        print(f"  {info['name']} ({child_key}, age {info['age']})")
        print(f"{'━' * 80}")

        print(f"\n  CHILD SPEECH:")
        print(f"  {'Person':<8} {'Types':<8} {'Tokens':<8} {'TTR':<8} {'Stems (with frequency)'}")
        print(f"  {'──────':<8} {'─────':<8} {'──────':<8} {'───':<8} {'─────────────────────'}")

        for p in persons:
            stems = child_data[child_key][p]
            if not stems:
                print(f"  {p:<8} {'—':<8} {'—':<8} {'—':<8}")
                continue
            types = len(stems)
            tokens = sum(len(v) for v in stems.values())
            ttr = types / tokens if tokens > 0 else 0

            # Sort stems by frequency
            sorted_stems = sorted(stems.items(), key=lambda x: -len(x[1]))
            stem_display = ', '.join(
                f"{s}({len(ws)})" for s, ws in sorted_stems[:8]
            )
            if len(sorted_stems) > 8:
                stem_display += f', ... +{len(sorted_stems) - 8} more'

            print(f"  {p:<8} {types:<8} {tokens:<8} {ttr:<8.2f} {stem_display}")

        print(f"\n  ADULT INPUT:")
        print(f"  {'Person':<8} {'Types':<8} {'Tokens':<8} {'TTR':<8}")
        print(f"  {'──────':<8} {'─────':<8} {'──────':<8} {'───':<8}")

        for p in persons:
            stems = adult_data[child_key][p]
            if not stems:
                print(f"  {p:<8} {'—':<8} {'—':<8} {'—':<8}")
                continue
            types = len(stems)
            tokens = sum(len(v) for v in stems.values())
            ttr = types / tokens if tokens > 0 else 0
            print(f"  {p:<8} {types:<8} {tokens:<8} {ttr:<8.2f}")

    # ── Cross-child comparison ────────────────────────────────────────
    print(f"\n\n{'=' * 80}")
    print("CROSS-CHILD SUMMARY")
    print("=" * 80)
    print()
    print(f"  {'Child':<12} {'Age':<8}", end='')
    for p in persons:
        print(f" {p + ' ty':<7} {p + ' tk':<7}", end='')
    print(f" {'Total ty':<10} {'Total tk':<10}")
    print(f"  {'─────':<12} {'───':<8}", end='')
    for _ in persons:
        print(f" {'─────':<7} {'─────':<7}", end='')
    print(f" {'────────':<10} {'────────':<10}")

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]
        total_types = 0
        total_tokens = 0
        print(f"  {info['name']:<12} {info['age']:<8}", end='')
        for p in persons:
            stems = child_data[child_key][p]
            types = len(stems)
            tokens = sum(len(v) for v in stems.values())
            total_types += types
            total_tokens += tokens
            print(f" {types:<7} {tokens:<7}", end='')
        print(f" {total_types:<10} {total_tokens:<10}")

    # ── Most frequent stems per child ─────────────────────────────────
    print(f"\n\n{'=' * 80}")
    print("TOP 10 MOST FREQUENT SET A STEMS PER CHILD")
    print("(stem = word with prefix stripped)")
    print("=" * 80)

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]
        # Flatten all stems across persons
        all_stems = []
        for p in persons:
            for stem, words in child_data[child_key][p].items():
                all_stems.append((p, stem, words[0], len(words)))

        all_stems.sort(key=lambda x: -x[3])
        print(f"\n  {info['name']} ({child_key}, age {info['age']}):")

        if not all_stems:
            print("    (no data)")
            continue

        for p, stem, example, count in all_stems[:10]:
            print(f"    {count:>4}x  {p:<6}  stem: {stem:<15}  e.g. {example}")
