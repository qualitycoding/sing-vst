---
id: L-20261016T000000Z-save-tool-silently-used-another-sessions-identity
title: "The save tool fell back to the planning session's commit trailers when the implementer's were missing"
status: active
supersedes: []
recurrence_of: null
occurrences: 1
severity: Medium
tags: [applies:all, tech:git, kind:process, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-16T00:00:00Z
---
## Trigger
A shared commit helper carries a default identity (trailers, author, session link) for when the caller supplies none.
## What went wrong
Cold read pass 4 item S5: after a sandbox reset the untracked trailer file is gone, and save.sh would silently attribute every implementer commit to the planning session.
## Correction
save.sh refuses to commit without trailers; S-000's session preamble rewrites .git/singvst-trailers in every session.
## Prevention rule
Never default an identity in shared tooling: a missing identity is an error that names how to provide it.
## Detection check
Run save.sh with no trailer file and no variable; it exits non-zero without committing.
## Evidence
premortem/coldread-pass-4.md S5; tools/save.sh.
