---
id: L-20261015T073500Z-syllable-split-assumed-instead-of-read-from-the-dictionary
title: "An evaluation phrase split 'every' into two syllables, but CMUdict gives it three vowels (eh v er iy)"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Low
tags: [domain:singing-voice-synthesis, tech:g2p, kind:wrong-assumption, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-15T07:35:00Z
---
## Trigger
Writing lyric fixtures with hyphenated syllables for a pipeline that syllabifies by dictionary vowels (D-005).
## What went wrong
The phrase 'ev- ery morn- ing ...' would have produced an alignment warning in every evaluation render.
## Correction
The generator's dictionary check stopped it; split as 'ev- er- y' and added a note.
## Prevention rule
Generate lyric fixtures with a check that each word's hyphen count + 1 equals its CMUdict vowel count.
## Detection check
`python -I tools/gen/phrases.py` exits 0.
## Evidence
AssertionError: every: 2 syllables but 3 vowels ['eh', 'v', 'er', 'iy'].
