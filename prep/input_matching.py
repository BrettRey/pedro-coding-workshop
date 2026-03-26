"""
Input-matching analysis: Do children's Set A marker distributions
mirror adult input, or are there systematic gaps?

Extracts Set A markers from both child and adult tiers,
computes proportions, and compares.
"""

import re
import os
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ── Child metadata ────────────────────────────────────────────────────
CHILDREN = {
    'CB': {'name': 'Brendo', 'code': 'B', 'age': '?'},
    'CF': {'name': 'Francisco', 'code': 'F', 'age': '1;7.6'},
    'CI': {'name': 'Isabel', 'code': 'I', 'age': '2;0.22'},
    'CM': {'name': 'Mateo', 'code': 'M', 'age': '2;1.26'},
    'CY': {'name': 'Yeseña', 'code': 'Y', 'age': '2;0.22'},
}

# Spanish stoplist — words that look like Set A prefixes but aren't
SPANISH_STOPS = {
    'yo', 'ya', 'hay', 'han', 'has', 'ha', 'haya', 'son', 'si', 'sí',
    'se', 'su', 'sus', 'sin', 'ser', 'sea', 'solo', 'sobre',
    'como', 'con', 'cosa', 'cosas',
    'haber', 'hacer', 'hasta', 'hacia',
    'seguro', 'siempre', 'señor', 'señora',
    'ye', 'yes',
    'ko', # unlikely as standalone Spanish but filter anyway
}

# Common Chuj function words / particles that aren't Set A markers
CHUJ_STOPS = {
    'han',    # discourse particle "pues"
    'hann',   # onomatopoeia
    'hannn',  # onomatopoeia
    'hi',     # "sí"
    "hi'",    # "sí"
    "hi'i",   # "sí"
    "hi'i'",  # "sí"
}

ALL_STOPS = SPANISH_STOPS | CHUJ_STOPS


def read_normalized(filepath):
    """Read file with encoding/line-ending normalization."""
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
    """
    Parse transcription file into utterances.
    Returns list of dicts with speaker, child_production, adult_form, spanish.
    """
    lines = read_normalized(filepath)
    utterances = []
    i = 0

    # Skip header
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


def find_set_a(text):
    """
    Find Set A marker tokens in a Chuj utterance.
    Returns list of (person, word) tuples.

    Uses the corrected/adult form for reliability.
    Filters Spanish and Chuj function words.
    """
    found = []
    # Remove parenthetical content
    text = re.sub(r'\([^)]*\)', '', text)
    words = text.lower().strip().split()

    for word in words:
        # Clean punctuation
        clean = re.sub(r'[.,;:!?¿¡]', '', word).strip("'")
        if len(clean) < 2 or clean in ALL_STOPS:
            continue

        if re.match(r'^hin', clean):
            found.append(('1SG', clean))
        elif re.match(r'^ha[a-z]', clean):
            found.append(('2SG', clean))
        elif re.match(r'^s[bcdfghjklmnñpqrstvwxyz\']', clean) and len(clean) > 2:
            found.append(('3SG', clean))
        elif re.match(r"^y[aeiou'']", clean) and len(clean) > 2:
            found.append(('3SG', clean))
        elif re.match(r'^ko[a-z]', clean) and len(clean) > 2:
            found.append(('1PL', clean))

    return found


def get_child_key(filename):
    return filename[:2]


if __name__ == '__main__':
    txt_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.txt'))

    # ── Collect data by child ─────────────────────────────────────────
    # For each child: markers in child speech vs. markers in adult speech
    child_markers = defaultdict(lambda: Counter())  # child's own Set A use
    adult_markers = defaultdict(lambda: Counter())  # adults speaking around child
    child_utt_counts = Counter()
    adult_utt_counts = Counter()

    # Also track by file for Mateo's longitudinal comparison
    mateo_by_session = {}

    for fname in txt_files:
        fpath = os.path.join(DATA_DIR, fname)
        child_key = get_child_key(fname)
        child_info = CHILDREN.get(child_key, {})
        child_speaker = child_info.get('code', '?')

        utterances = parse_file(fpath)

        session_child = Counter()
        session_adult = Counter()

        for u in utterances:
            # Use adult form if available, else child production
            text = u['adult_form'] if u['adult_form'] else u['child_production']
            markers = find_set_a(text)

            if u['speaker'] == child_speaker:
                child_utt_counts[child_key] += 1
                for person, _ in markers:
                    child_markers[child_key][person] += 1
                    session_child[person] += 1
            else:
                adult_utt_counts[child_key] += 1
                for person, _ in markers:
                    adult_markers[child_key][person] += 1
                    session_adult[person] += 1

        if child_key == 'CM':
            mateo_by_session[fname] = {
                'child': dict(session_child),
                'adult': dict(session_adult),
            }

    # ── Print results ─────────────────────────────────────────────────
    persons = ['1SG', '2SG', '3SG', '1PL']

    print("=" * 80)
    print("SET A MARKER DISTRIBUTIONS: CHILD vs. ADULT INPUT")
    print("=" * 80)

    for child_key in sorted(CHILDREN.keys()):
        info = CHILDREN[child_key]
        c_total = sum(child_markers[child_key][p] for p in persons)
        a_total = sum(adult_markers[child_key][p] for p in persons)

        print(f"\n{'─' * 80}")
        print(f"{info['name']} ({child_key}, age {info['age']})")
        print(f"  Utterances: child={child_utt_counts[child_key]}, adult={adult_utt_counts[child_key]}")
        print(f"  Total Set A tokens: child={c_total}, adult={a_total}")
        print()

        if c_total == 0 and a_total == 0:
            print("  (insufficient data)")
            continue

        print(f"  {'Person':<8} {'Child':<10} {'Child %':<10} {'Adult':<10} {'Adult %':<10} {'Ratio c/a':<10}")
        print(f"  {'──────':<8} {'─────':<10} {'───────':<10} {'─────':<10} {'───────':<10} {'─────────':<10}")

        for p in persons:
            cc = child_markers[child_key][p]
            ac = adult_markers[child_key][p]
            c_pct = (cc / c_total * 100) if c_total > 0 else 0
            a_pct = (ac / a_total * 100) if a_total > 0 else 0
            ratio = (c_pct / a_pct) if a_pct > 0 else float('inf') if c_pct > 0 else 0
            print(f"  {p:<8} {cc:<10} {c_pct:<10.1f} {ac:<10} {a_pct:<10.1f} {ratio:<10.2f}")

    # ── Mateo longitudinal ────────────────────────────────────────────
    print(f"\n\n{'=' * 80}")
    print("MATEO LONGITUDINAL: Set A markers across 4 sessions")
    print("=" * 80)

    dates = {
        'CM080711.txt': 'Jul 8',
        'CM260711.txt': 'Jul 26',
        'CM090811.txt': 'Aug 9',
        'CM230811.txt': 'Aug 23',
    }

    print(f"\n  {'Session':<18} ", end='')
    for p in persons:
        print(f"{'Child ' + p:<12}", end='')
    print(f"  {'Total':<8}")
    print(f"  {'───────':<18} ", end='')
    for _ in persons:
        print(f"{'────────':<12}", end='')
    print(f"  {'─────':<8}")

    for fname in sorted(mateo_by_session.keys()):
        date_label = dates.get(fname, fname)
        data = mateo_by_session[fname]
        child_data = data['child']
        total = sum(child_data.get(p, 0) for p in persons)
        print(f"  {date_label:<18} ", end='')
        for p in persons:
            print(f"{child_data.get(p, 0):<12}", end='')
        print(f"  {total:<8}")

    print()
    print(f"  {'Session':<18} ", end='')
    for p in persons:
        print(f"{'Adult ' + p:<12}", end='')
    print(f"  {'Total':<8}")
    print(f"  {'───────':<18} ", end='')
    for _ in persons:
        print(f"{'────────':<12}", end='')
    print(f"  {'─────':<8}")

    for fname in sorted(mateo_by_session.keys()):
        date_label = dates.get(fname, fname)
        data = mateo_by_session[fname]
        adult_data = data['adult']
        total = sum(adult_data.get(p, 0) for p in persons)
        print(f"  {date_label:<18} ", end='')
        for p in persons:
            print(f"{adult_data.get(p, 0):<12}", end='')
        print(f"  {total:<8}")

    # ── Summary interpretation ────────────────────────────────────────
    print(f"\n\n{'=' * 80}")
    print("PRELIMINARY OBSERVATIONS (needs Pedro's validation)")
    print("=" * 80)
    print("""
1. CAVEAT: These counts conflate ergative (verbal) and possessive (nominal)
   uses of Set A markers. Distinguishing them requires knowing which words
   are verbs vs. nouns — needs Pedro's expertise or a morphological parser.

2. CAVEAT: False positives remain despite the stoplist. Any word starting
   with s+consonant, ha+consonant, hin-, ko+consonant, or y+vowel gets
   counted. Many of these are not actually Set A prefixes.

3. The interesting comparison is the PROPORTION of each person in child
   vs. adult speech. If children mirror input, proportions should be similar.
   Systematic under-representation of 3SG (especially on transitive verbs)
   would support a complexity-driven acquisition story.

4. Gelman would note: with N=5 children and noisy extraction, any
   child-level comparison needs heavy shrinkage (partial pooling). The
   raw proportions here are descriptive only — don't over-interpret
   individual children's ratios.
""")
