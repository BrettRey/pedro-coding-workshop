"""
Parse Chuj child transcriptions: extract child utterances,
group lexical items by category with context of use.
"""
import re
import os
from collections import defaultdict, Counter

# Which speaker letter is the target child in each file
CHILD_CODES = {
    'CB120711.txt': 'B',
    'CF110711_1.txt': 'F',
    'CI120711.txt': 'I',
    'CI260711.txt': 'I',
    'CM080711.txt': 'M',
    'CM090811.txt': 'M',
    'CM230811.txt': 'M',
    'CM260711.txt': 'M',
    'CY120711.txt': 'Y',
    'CY260711.txt': 'Y',
}

CHILD_NAMES = {
    'B': 'Brendo', 'F': 'Francisco', 'I': 'Isabel',
    'M': 'Mateo', 'Y': 'Yeseña',
}

def parse_file(filepath):
    """Parse a transcription file into utterance triplets."""
    fname = os.path.basename(filepath)
    child_code = CHILD_CODES.get(fname)
    if not child_code:
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    utterances = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Check if this is a child utterance line
        if line.startswith(child_code + ' ') and not line.startswith('+'):
            raw = line[2:].strip()  # child's actual production
            corrected = ''
            spanish = ''
            # Look for = line and %spa line
            j = i + 1
            while j < len(lines) and j <= i + 3:
                nxt = lines[j].strip()
                if nxt.startswith('= '):
                    corrected = nxt[2:].strip()
                elif nxt.startswith('%spa ') or nxt.startswith('%span '):
                    spanish = re.sub(r'^%spa[n]?\s+', '', nxt).strip()
                    break
                elif nxt.startswith('+') or (len(nxt) > 0 and nxt[0].isupper() and ' ' in nxt):
                    break  # next utterance or context line
                j += 1
            utterances.append({
                'child': CHILD_NAMES[child_code],
                'raw': raw,
                'corrected': corrected,
                'spanish': spanish,
                'file': fname,
            })
        i += 1
    return utterances

# Parse all files
all_utterances = []
for fname in sorted(CHILD_CODES.keys()):
    path = os.path.join('.', fname)
    if os.path.exists(path):
        utts = parse_file(path)
        all_utterances.append((fname, utts))

# Build a word-level inventory from corrected forms, with context
word_data = defaultdict(lambda: {'children': Counter(), 'contexts': [], 'count': 0})

for fname, utts in all_utterances:
    for u in utts:
        form = u['corrected'] if u['corrected'] else u['raw']
        if form == '( )' or not form:
            continue
        # Tokenize: split on spaces, strip punctuation
        tokens = re.findall(r"[a-záéíóúñü'`]+", form.lower())
        for tok in tokens:
            word_data[tok]['children'][u['child']] += 1
            word_data[tok]['count'] += 1
            if len(word_data[tok]['contexts']) < 3:
                ctx = f"  {u['corrected']}  →  {u['spanish']}" if u['spanish'] else f"  {u['corrected']}"
                word_data[tok]['contexts'].append(ctx)

# Sort by frequency
sorted_words = sorted(word_data.items(), key=lambda x: -x[1]['count'])

# Print top items grouped loosely
print(f"Total child utterances parsed: {sum(len(u) for _, u in all_utterances)}")
print(f"Unique word forms (from corrected tier): {len(sorted_words)}")
print()

# Show top 80 with children and sample contexts
print(f"{'FORM':<20} {'COUNT':>5}  {'CHILDREN':<35} SAMPLE CONTEXT")
print("-" * 120)
for word, data in sorted_words[:80]:
    children = ', '.join(f"{c}({n})" for c, n in data['children'].most_common())
    ctx = data['contexts'][0].strip() if data['contexts'] else ''
    # Truncate context
    if len(ctx) > 55:
        ctx = ctx[:52] + '...'
    print(f"{word:<20} {data['count']:>5}  {children:<35} {ctx}")

