"""
Dry-run script: parse Chuj transcription files, extract child utterances,
and search for Set A (ergative/possessive) person markers.

Chuj Set A markers (prefixes on verbs = ergative, on nouns = possessive):
  hin- / h-   1SG
  ha-         2SG
  s- / y-     3SG  (y- before vowels)
  ko-         1PL
  he-         2PL
  s-...-heb'  3PL

NOTE: These are from published grammars. Pedro should verify for San Mateo
Ixtatán Chuj specifically. The markers do double duty as ergative on
transitive verbs and possessive on nouns — distinguishing the two requires
syntactic context.
"""

import re
import os
from collections import Counter, defaultdict

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# ── Child metadata (from file headers and inventory) ──────────────────
CHILDREN = {
    'CB': {'name': 'Brendo', 'code': 'B'},
    'CF': {'name': 'Francisco', 'code': 'F', 'age': '1;7.6'},
    'CI': {'name': 'Isabel', 'code': 'I', 'age': '2;0.22'},
    'CM': {'name': 'Mateo', 'code': 'M', 'age': '2;1.26'},
    'CY': {'name': 'Yeseña', 'code': 'Y', 'age': '2;0.22'},
}

# Map filename prefix to child code
def get_child_key(filename):
    """Extract child key (CB, CF, CI, CM, CY) from filename."""
    return filename[:2]

# ── Line-ending normalization ─────────────────────────────────────────
def read_normalized(filepath):
    """Read file, normalize CR/CRLF to LF, handle encoding issues."""
    # Try UTF-8 first, fall back to latin-1
    for enc in ('utf-8', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                text = f.read()
            break
        except UnicodeDecodeError:
            continue
    # Normalize line endings: CRLF → LF, then CR → LF
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    return text.split('\n')

# ── Parse utterances ──────────────────────────────────────────────────
def parse_file(filepath):
    """
    Parse a transcription file into utterances.

    Returns list of dicts:
      {'speaker': str, 'child_production': str, 'adult_form': str, 'spanish': str}
    """
    lines = read_normalized(filepath)
    utterances = []

    i = 0
    # Skip header lines (participant codes, metadata)
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('+') or line == '':
            i += 1
            continue
        # Check if this looks like a participant header line
        if re.match(r'^[A-Z]\(', line) and i < 15:
            i += 1
            continue
        break

    # Parse utterances
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines and context notes
        if not line or line.startswith('+'):
            i += 1
            continue

        # Try to match a speaker utterance: "X text" where X is a single letter
        speaker_match = re.match(r'^([A-Z])\s+(.+)', line)
        if not speaker_match:
            # Could be a continuation or = line or %spa line at top level
            # (some files have messy formatting)
            i += 1
            continue

        speaker = speaker_match.group(1)
        child_production = speaker_match.group(2).strip()
        adult_form = ''
        spanish = ''

        # Look ahead for = and %spa lines
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

# ── Set A marker extraction ──────────────────────────────────────────
SET_A_PATTERNS = [
    ('1SG', r'\bhin'),
    ('2SG', r'\bha'),
    ('3SG_s', r'\bs[a-z]'),  # s- before consonants
    ('3SG_y', r'\by[aeiou]'),  # y- before vowels
    ('1PL', r'\bko'),
    ('2PL', r'\bhe[b\']'),
]

def find_set_a_markers(text):
    """
    Search for potential Set A markers in a Chuj utterance.
    Returns list of (person, matched_word) tuples.

    CAVEAT: This is a rough heuristic. Many false positives.
    Pedro's expertise needed to validate.
    """
    found = []
    words = text.lower().split()
    for word in words:
        # Skip very short words, Spanish loans, etc.
        if len(word) < 2:
            continue
        # Check each pattern
        if re.match(r'^hin', word):
            found.append(('1SG', word))
        elif re.match(r'^ha[a-z]', word) and word not in ('han', 'hay'):
            found.append(('2SG', word))
        elif re.match(r'^s[bcdfghjklmnpqrstvwxyz\']', word) and len(word) > 2:
            found.append(('3SG', word))
        elif re.match(r'^y[aeiou]', word) and len(word) > 2:
            found.append(('3SG', word))
        elif re.match(r'^ko[a-z]', word) and word not in ('kot',):
            found.append(('1PL', word))
    return found

# ── Main ──────────────────────────────────────────────────────────────
if __name__ == '__main__':
    txt_files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith('.txt'))

    print("=" * 70)
    print("CHUJ TRANSCRIPTION DATA — DRY RUN ANALYSIS")
    print("=" * 70)

    # ── Step 1: Format overview ──
    print("\n## FILE OVERVIEW\n")
    print(f"{'File':<20} {'Child':<12} {'Age':<10} {'Lines':<8} {'Utterances':<12} {'Child utts':<10}")
    print("-" * 72)

    all_child_utterances = defaultdict(list)

    for fname in txt_files:
        fpath = os.path.join(DATA_DIR, fname)
        lines = read_normalized(fpath)
        child_key = get_child_key(fname)
        child_info = CHILDREN.get(child_key, {})
        child_speaker = child_info.get('code', '?')
        age = child_info.get('age', '?')

        utterances = parse_file(fpath)
        child_utts = [u for u in utterances if u['speaker'] == child_speaker]

        print(f"{fname:<20} {child_info.get('name','?'):<12} {age:<10} {len(lines):<8} {len(utterances):<12} {len(child_utts):<10}")

        for u in child_utts:
            all_child_utterances[child_key].append(u)

    # ── Step 2: Set A marker extraction ──
    print("\n\n## SET A MARKER COUNTS BY CHILD (from adult-form / '=' line)\n")
    print("NOTE: Searching the corrected adult form, not the child's raw production.")
    print("      This finds where the TARGET form uses a Set A marker.\n")

    for child_key in sorted(all_child_utterances.keys()):
        utts = all_child_utterances[child_key]
        info = CHILDREN[child_key]
        marker_counts = Counter()
        examples = defaultdict(list)

        for u in utts:
            # Search in the adult/corrected form
            text = u['adult_form'] if u['adult_form'] else u['child_production']
            markers = find_set_a_markers(text)
            for person, word in markers:
                marker_counts[person] += 1
                if len(examples[person]) < 3:
                    examples[person].append(f"  {word}  ← child said: {u['child_production'][:40]}")

        print(f"### {info['name']} ({child_key}, age {info.get('age', '?')})")
        print(f"    Total child utterances: {len(utts)}")
        if marker_counts:
            for person in ['1SG', '2SG', '3SG', '1PL', '2PL']:
                if person in marker_counts:
                    print(f"    {person}: {marker_counts[person]}")
                    for ex in examples[person]:
                        print(f"      e.g. {ex}")
        else:
            print("    No Set A markers found")
        print()

    # ── Step 3: Sample child utterances ──
    print("\n## SAMPLE CHILD UTTERANCES (first 5 per child)\n")
    for child_key in sorted(all_child_utterances.keys()):
        info = CHILDREN[child_key]
        utts = all_child_utterances[child_key][:5]
        print(f"### {info['name']} ({child_key})")
        for u in utts:
            print(f"  child: {u['child_production'][:60]}")
            if u['adult_form']:
                print(f"  adult: {u['adult_form'][:60]}")
            if u['spanish']:
                print(f"  spa:   {u['spanish'][:60]}")
            print()
