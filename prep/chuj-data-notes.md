# Chuj Data Notes

Notes from the dry run on Pedro's publicly available Chuj child language data (Harvard Dataverse).

## Format

The files are **not** standard CHAT format despite the Polinsky Lab transcription conventions PDF. They use a custom three-line structure:

```
SPEAKER utterance (child's actual production)
 = corrected/adult form
 %spa Spanish translation
```

Context lines start with `+` (noise, pauses, actions). File headers list participants and metadata (child DOB/age, transcriber, recording code, language).

The `%spa` tier is occasionally misspelled as `%span`.

## Children

| Key | Name      | Age at recording | Sex | Sessions in dataset |
|-----|-----------|-------------------|-----|---------------------|
| CB  | Brendo    | unknown           | M   | 1 (very short, 2:27)|
| CF  | Francisco | 1;7.6             | M   | 1                   |
| CI  | Isabel    | 2;0.22            | F   | 2                   |
| CM  | Mateo     | 2;1.26            | M   | 4                   |
| CY  | Yeseña    | 2;0.22            | F   | 2                   |

Mateo has the most data (2,629 child utterances across 4 recordings). Francisco is youngest (1;7). Brendo's file is tiny (27 child utterances).

## Friction points

### 1. Line endings (critical)

Three files use CR-only line terminators (classic Mac format). They look like one giant line to most tools:

- `CB120711.txt` (CR only)
- `CI260711.txt` (CR only)
- `CM260711.txt` (CR only)

Other files use CRLF or mixed CRLF/LF. Any parser needs to normalize `\r\n` → `\n` then `\r` → `\n`.

### 2. Encoding

Two files are not UTF-8:

- `CM080711.txt` — Non-ISO extended-ASCII (likely Windows-1252)
- `CM230811.txt` — Same

Reading as Latin-1 works; reading as UTF-8 produces mojibake (`sÃ­` for `sí`).

### 3. Speaker identification

The child speaker code is embedded in the header but not always obvious. The naming convention is: filename starts with two letters (e.g., `CB`), second letter = child initial (B = Brendo). The header lists `B(rendo=sujeto de investigación)` etc. A parser has to figure out which single letter is the target child.

### 4. Spanish in the data

- `%spa` tier is Spanish throughout
- Context notes (`+` lines) are in Spanish
- Some adult utterances are in Spanish (code-switching)
- Spanish words appear in Chuj utterances (e.g., `mono`, `carro`)

### 5. No standard morphological glossing

There are no morpheme-by-morpheme glosses. The `= ` line gives the corrected adult form in running Chuj, and `%spa` gives a free Spanish translation. Any morphological analysis has to be done by pattern-matching on the Chuj string — no interlinear gloss to rely on.

## Set A marker extraction: what worked and what didn't

### What worked
- Regex prefix matching finds real Set A markers: `hin-kuch` (1SG-carry), `ha-chej` (2SG-horse), `s-b'i` (3SG-name), `ko-papis` (1PL-tortilla)
- Counts show clear developmental patterns (Mateo has many more 1SG markers than Francisco)

### False positives (major issue)
- **`yo`** (Spanish "I/me") matches the `y-` 3SG pattern — inflates 3SG counts massively
- **`han`** ("pues" / discourse particle) matches `ha-` 2SG pattern
- **`hann`** (onomatopoeia, car sounds) matches 2SG
- Any word starting with `s` + consonant gets flagged as 3SG

These false positives are **great for the demo**: they show Pedro exactly why his expertise matters. The agent can code, but it can't tell `yo` (Spanish) from `y-ok` (3SG-enter) without a linguist.

### What would help
- A stoplist of Spanish function words (`yo`, `si`, `no`, `hay`, etc.)
- Distinguishing ergative (verbal) from possessive (nominal) uses
- Pedro's input on which Set A allomorphs are actually used in San Mateo Ixtatán Chuj
