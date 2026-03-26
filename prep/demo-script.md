# Demo Script

Exact prompts and expected outcomes for the Pedro session. Brett drives, Pedro watches via Zoom.

## Setup (before Pedro joins)

- Open terminal in `pedro-coding-workshop/data/`
- Have the files visible: `ls`
- Start Claude Code: `claude`

## Prompt 1: Describe the format

**Type:**
```
Read these Chuj transcription files and describe the format. What information is in the headers? How are utterances structured?
```

**What will happen:**
- Agent reads several files, likely starting with the smaller ones
- It will identify the three-line structure (utterance / = corrected / %spa)
- It will note the participant header format
- It may struggle with CB120711.txt (CR-only line endings, looks like one line)
- **Teaching moment:** "See how it figured out the format without us explaining it? But it might miss the line-ending problem."

**Expected output (summary):** The agent describes the triplet format, lists the children with ages, and identifies the `+` context lines and `%spa` Spanish translation tier.

**Follow-up Pedro might ask:** "What about the corrected line?" / "Why does it say CB has no lines?"

## Prompt 2: Ergative markers

**Type:**
```
Extract all Set A (ergative) person markers from the child utterances and count them by child. Set A markers in Chuj are prefixes: hin- (1SG), ha- (2SG), s-/y- (3SG), ko- (1PL). Search in the corrected adult form (the = line) for child utterances only.
```

**What will happen:**
- Agent writes a Python script to parse files and regex-match prefixes
- First run will have false positives (yo, han, etc.)
- **Teaching moment:** This is where Pedro's expertise comes in. Ask him: "Pedro, `yo` is showing up as a 3SG marker — that's just Spanish, right? What should we exclude?"

**Expected issues the agent will hit:**
1. Encoding errors on CM080711/CM230811 (non-UTF-8)
2. `yo` matching as 3SG y- prefix
3. `han` matching as 2SG ha- prefix
4. Distinguishing ergative from possessive uses of Set A

**Expected output (approximate counts):**

| Child     | 1SG | 2SG | 3SG  | 1PL |
|-----------|-----|-----|------|-----|
| Brendo    | 1   | 1   | —    | —   |
| Francisco | 2   | —   | ~4   | 2   |
| Isabel    | 14  | 13* | 13   | 1   |
| Mateo     | 93  | 37* | 157* | 9   |
| Yeseña    | 22  | 51* | 102* | 29  |

*inflated by false positives

## Prompt 3: Correction loop

After Pedro flags the false positives, type something like:

```
Good catch. Remove Spanish words (yo, ya, hay, han) from the 3SG and 2SG counts. Also exclude onomatopoeia and anything in parentheses.
```

**What will happen:**
- Agent revises the script with a stoplist
- Counts drop, especially 3SG
- **Teaching moment:** "This is the correction loop. You tell it what it got wrong, it fixes the code. You don't need to write the code yourself."

## Prompt 4 (if time): Developmental comparison

```
Compare Mateo's marker use across his four recordings (July 8, July 26, August 9, August 23). Does the frequency or variety of Set A markers change over this month?
```

**What will happen:**
- Agent splits Mateo's data by file/date
- May produce a simple table or even a chart
- Could show increase in 1SG markers over time (or not — the window is short)
- **Teaching moment:** "In a month of data, we probably won't see dramatic change, but this is the kind of question you could ask across a larger dataset."

## Prompt 5 (backup, if ergative markers don't work well)

```
Find all questions in the data — utterances where the Spanish translation contains '?' or starts with a question word (dónde, qué, quién, cómo). How many questions does each child produce?
```

This is a simpler task that doesn't require Chuj morphological knowledge and will definitely work.

## Debrief points

1. "You just saw me give plain-language instructions and get working code back. I didn't write any Python."
2. "The agent made mistakes — it counted Spanish words as Chuj morphology. Your expertise caught that. This is the RA model: you supervise, it codes."
3. "You can install Claude Code on your own machine and do this with your Q'anjob'al data."
4. "Want me to help you set it up?"
