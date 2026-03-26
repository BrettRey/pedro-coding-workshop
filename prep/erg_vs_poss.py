"""
Ergative vs. possessive split for Set A markers, using the Spanish
translation tier (%spa) as a heuristic.

Logic:
- If %spa contains a possessive (mi, tu, su, nuestro, etc.) near the
  relevant person, the Set A marker is likely possessive.
- If %spa contains a conjugated verb in the relevant person, the
  Set A marker is likely ergative.
- Many will be ambiguous — that's the point. We measure what we can
  and flag what needs Pedro.
"""

import re
import os
from collections import defaultdict, Counter

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

# Spanish possessive markers by person
POSS_PATTERNS = {
    '1SG': r'\b(mi|mío|mía|mis|míos|mías)\b',
    '2SG': r'\b(tu|tuyo|tuya|tus|tuyos|tuyas)\b',
    '3SG': r'\b(su|suyo|suya|sus|suyos|suyas|de él|de ella)\b',
    '1PL': r'\b(nuestro|nuestra|nuestros|nuestras)\b',
}

# Spanish verbal cues — pronouns or verb forms suggesting a verbal predicate
# These are rough: we look for subject pronouns + verb-like patterns
VERB_PATTERNS = {
    '1SG': r'\b(yo\s+\w+|me\s+\w+|lo\s+\w+é|hago|pongo|llevo|cargo|traigo)\b',
    '2SG': r'\b(tú\s+\w+|te\s+\w+|haces|pones|llevas)\b',
    '3SG': r'\b(él\s+\w+|ella\s+\w+|lo\s+\w+a|la\s+\w+a|hace|pone|lleva|va|fue|se fue|está)\b',
    '1PL': r'\b(nosotros|hacemos|ponemos|vamos|llevamos)\b',
}

# More reliable: Spanish possessive determiners/pronouns are strong
# evidence of nominal possession. Spanish verb phrases (even if we
# can't parse them perfectly) suggest verbal predication.
# But the best signal is simpler: does the Spanish contain "de" + person?


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


def classify_function(person, spanish):
    """
    Use the Spanish translation to guess whether a Set A marker
    is possessive or ergative/verbal.

    Returns: 'poss', 'erg', or 'ambiguous'
    """
    if not spanish:
        return 'no_spa'

    spa_lower = spanish.lower()

    # Check possessive signals
    has_poss = bool(re.search(POSS_PATTERNS.get(person, r'$^'), spa_lower))

    # Check verbal signals — broader: any conjugated-looking verb
    # Simple heuristic: if Spanish has a verb ending (-a, -e, -o, -an, -en)
    # that's not a possessive, lean toward ergative
    has_verb = bool(re.search(VERB_PATTERNS.get(person, r'$^'), spa_lower))

    # Additional possessive cue: "de mi/tu/su/nuestro"
    de_poss = bool(re.search(r'\bde\s+(mi|tu|su|nuestro|nuestra)', spa_lower))

    if has_poss or de_poss:
        if has_verb:
            return 'ambiguous'
        return 'poss'
    elif has_verb:
        return 'erg'
    else:
        return 'ambiguous'


def get_child_key(filename):
    return filename[:2]


if __name__ == '__main__':
    txt_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.txt'))
    persons = ['1SG', '2SG', '3SG', '1PL']
    functions = ['poss', 'erg', 'ambiguous', 'no_spa']

    # Collect: child_key → person → function → [(chuj_word, spanish)]
    results = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    adult_results = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )

    for fname in txt_files:
        fpath = os.path.join(DATA_DIR, fname)
        child_key = get_child_key(fname)
        child_info = CHILDREN.get(child_key, {})
        child_speaker = child_info.get('code', '?')

        utterances = parse_file(fpath)

        for u in utterances:
            text = u['adult_form'] if u['adult_form'] else u['child_production']
            text_clean = re.sub(r'\([^)]*\)', '', text)
            words = text_clean.split()

            for word in words:
                result = classify_marker(word)
                if result is None:
                    continue
                person, clean = result
                func = classify_function(person, u['spanish'])

                entry = (clean, u['spanish'][:60], u['child_production'][:40])
                if u['speaker'] == child_speaker:
                    results[child_key][person][func].append(entry)
                else:
                    adult_results[child_key][person][func].append(entry)

    # ── Print results ─────────────────────────────────────────────────
    print("=" * 80)
    print("SET A MARKERS: ERGATIVE vs. POSSESSIVE (via Spanish translation)")
    print("=" * 80)
    print()
    print("poss = Spanish translation contains possessive (mi, tu, su, ...)")
    print("erg  = Spanish translation contains verbal cue")
    print("amb  = both or neither signal present")
    print("no_spa = no Spanish translation available")

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]
        print(f"\n{'━' * 80}")
        print(f"  {info['name']} ({child_key}, age {info['age']}) — CHILD SPEECH")
        print(f"{'━' * 80}")

        print(f"\n  {'Person':<8} {'Poss':<8} {'Erg':<8} {'Ambig':<8} {'No spa':<8} {'Total':<8}")
        print(f"  {'──────':<8} {'────':<8} {'───':<8} {'─────':<8} {'──────':<8} {'─────':<8}")

        child_poss_total = 0
        child_erg_total = 0

        for p in persons:
            counts = {f: len(results[child_key][p][f]) for f in functions}
            total = sum(counts.values())
            child_poss_total += counts['poss']
            child_erg_total += counts['erg']
            print(f"  {p:<8} {counts['poss']:<8} {counts['erg']:<8} "
                  f"{counts['ambiguous']:<8} {counts['no_spa']:<8} {total:<8}")

        print(f"\n  Total classifiable: {child_poss_total} possessive, "
              f"{child_erg_total} ergative")

        # Show examples
        for func_label, func_key in [('POSSESSIVE', 'poss'), ('ERGATIVE', 'erg')]:
            examples = []
            for p in persons:
                for entry in results[child_key][p][func_key][:3]:
                    examples.append((p, entry))
            if examples:
                print(f"\n  {func_label} examples:")
                for p, (chuj, spa, child_said) in examples[:6]:
                    print(f"    {p:<6} {chuj:<20} spa: {spa}")

    # ── Adult comparison ──────────────────────────────────────────────
    print(f"\n\n{'=' * 80}")
    print("ADULT INPUT: ERGATIVE vs. POSSESSIVE")
    print("=" * 80)

    print(f"\n  {'Child':<12} {'Poss':<8} {'Erg':<8} {'Ambig':<8} {'No spa':<8} "
          f"{'%Poss':<8} {'%Erg':<8}")
    print(f"  {'─────':<12} {'────':<8} {'───':<8} {'─────':<8} {'──────':<8} "
          f"{'─────':<8} {'────':<8}")

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]
        poss = sum(len(adult_results[child_key][p]['poss']) for p in persons)
        erg = sum(len(adult_results[child_key][p]['erg']) for p in persons)
        amb = sum(len(adult_results[child_key][p]['ambiguous']) for p in persons)
        no_spa = sum(len(adult_results[child_key][p]['no_spa']) for p in persons)
        classifiable = poss + erg
        poss_pct = (poss / classifiable * 100) if classifiable > 0 else 0
        erg_pct = (erg / classifiable * 100) if classifiable > 0 else 0
        print(f"  {info['name']:<12} {poss:<8} {erg:<8} {amb:<8} {no_spa:<8} "
              f"{poss_pct:<8.1f} {erg_pct:<8.1f}")

    # ── Child comparison ──────────────────────────────────────────────
    print(f"\n  {'Child':<12} {'Poss':<8} {'Erg':<8} {'Ambig':<8} {'No spa':<8} "
          f"{'%Poss':<8} {'%Erg':<8}")
    print(f"  {'─────':<12} {'────':<8} {'───':<8} {'─────':<8} {'──────':<8} "
          f"{'─────':<8} {'────':<8}")

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]
        poss = sum(len(results[child_key][p]['poss']) for p in persons)
        erg = sum(len(results[child_key][p]['erg']) for p in persons)
        amb = sum(len(results[child_key][p]['ambiguous']) for p in persons)
        no_spa = sum(len(results[child_key][p]['no_spa']) for p in persons)
        classifiable = poss + erg
        poss_pct = (poss / classifiable * 100) if classifiable > 0 else 0
        erg_pct = (erg / classifiable * 100) if classifiable > 0 else 0
        print(f"  {info['name']:<12} {poss:<8} {erg:<8} {amb:<8} {no_spa:<8} "
              f"{poss_pct:<8.1f} {erg_pct:<8.1f}")

    # ── The key question ──────────────────────────────────────────────
    print(f"\n\n{'=' * 80}")
    print("KEY COMPARISON: Ergative proportion in child vs. adult speech")
    print("=" * 80)
    print()
    print("If children avoid ergative marking, their %Erg should be lower")
    print("than adults'. If they just mirror input, proportions should match.")
    print()
    print(f"  {'Child':<12} {'Age':<8} {'Child %Erg':<12} {'Adult %Erg':<12} {'Difference':<12}")
    print(f"  {'─────':<12} {'───':<8} {'──────────':<12} {'──────────':<12} {'──────────':<12}")

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]

        c_poss = sum(len(results[child_key][p]['poss']) for p in persons)
        c_erg = sum(len(results[child_key][p]['erg']) for p in persons)
        c_class = c_poss + c_erg

        a_poss = sum(len(adult_results[child_key][p]['poss']) for p in persons)
        a_erg = sum(len(adult_results[child_key][p]['erg']) for p in persons)
        a_class = a_poss + a_erg

        c_pct = (c_erg / c_class * 100) if c_class > 0 else float('nan')
        a_pct = (a_erg / a_class * 100) if a_class > 0 else float('nan')
        diff = c_pct - a_pct

        print(f"  {info['name']:<12} {info['age']:<8} {c_pct:<12.1f} {a_pct:<12.1f} {diff:<+12.1f}")

    print("""
CAVEATS:
1. The ergative/possessive split is based on SPANISH TRANSLATION heuristics.
   The verb patterns are crude. Many tokens land in 'ambiguous'.
2. 'Ergative' here includes intransitive subjects if the Spanish has a
   verbal cue — Chuj actually uses Set B (absolutive) for intransitives.
   Only transitive agents are true ergative. Distinguishing these requires
   Chuj morphosyntactic analysis, not Spanish translation.
3. The large 'ambiguous' category means these proportions are based on a
   subset of the data. They could shift substantially with manual coding.
4. This is exactly the kind of pilot that justifies Pedro spending an
   afternoon tagging 200 utterances by hand.
""")
