"""
Export child lexicon from Chuj transcriptions to TSV.
Columns: form, count, children, category (blank for manual annotation), sample_context, spanish
"""
import re
import os
from collections import defaultdict, Counter

CHILD_CODES = {
    'CB120711.txt': 'B', 'CF110711_1.txt': 'F',
    'CI120711.txt': 'I', 'CI260711.txt': 'I',
    'CM080711.txt': 'M', 'CM090811.txt': 'M',
    'CM230811.txt': 'M', 'CM260711.txt': 'M',
    'CY120711.txt': 'Y', 'CY260711.txt': 'Y',
}
CHILD_NAMES = {
    'B': 'Brendo', 'F': 'Francisco', 'I': 'Isabel',
    'M': 'Mateo', 'Y': 'Yeseña',
}

def parse_file(filepath):
    fname = os.path.basename(filepath)
    child_code = CHILD_CODES.get(fname)
    if not child_code:
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.read().split('\n')
    utterances = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith(child_code + ' ') and not line.startswith('+'):
            raw = line[2:].strip()
            corrected = ''
            spanish = ''
            j = i + 1
            while j < len(lines) and j <= i + 3:
                nxt = lines[j].strip()
                if nxt.startswith('= '):
                    corrected = nxt[2:].strip()
                elif nxt.startswith('%spa ') or nxt.startswith('%span '):
                    spanish = re.sub(r'^%spa[n]?\s+', '', nxt).strip()
                    break
                elif nxt.startswith('+') or (len(nxt) > 0 and nxt[0].isupper() and ' ' in nxt):
                    break
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

# Collect
word_data = defaultdict(lambda: {
    'children': Counter(), 'contexts': [], 'spanish': [], 'count': 0
})

for fname in sorted(CHILD_CODES.keys()):
    path = os.path.join('.', fname)
    if os.path.exists(path):
        for u in parse_file(path):
            form = u['corrected'] if u['corrected'] else u['raw']
            if form == '( )' or not form:
                continue
            tokens = re.findall(r"[a-záéíóúñü'`]+", form.lower())
            for tok in tokens:
                word_data[tok]['children'][u['child']] += 1
                word_data[tok]['count'] += 1
                if len(word_data[tok]['contexts']) < 3:
                    word_data[tok]['contexts'].append(u['corrected'])
                if u['spanish'] and len(word_data[tok]['spanish']) < 3:
                    word_data[tok]['spanish'].append(u['spanish'])

# Write TSV
sorted_words = sorted(word_data.items(), key=lambda x: -x[1]['count'])

with open('child_lexicon.tsv', 'w', encoding='utf-8') as f:
    f.write('form\tcount\tchildren\tcategory\tsample_context\tspanish\n')
    for word, data in sorted_words:
        children = '; '.join(f"{c}({n})" for c, n in data['children'].most_common())
        ctx = ' | '.join(data['contexts'][:2])
        spa = ' | '.join(data['spanish'][:2])
        f.write(f"{word}\t{data['count']}\t{children}\t\t{ctx}\t{spa}\n")

print(f"Wrote {len(sorted_words)} entries to child_lexicon.tsv")
