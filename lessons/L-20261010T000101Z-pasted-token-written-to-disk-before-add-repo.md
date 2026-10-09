---
id: L-20261010T000101Z-pasted-token-written-to-disk-before-add-repo
title: 'A token pasted in chat was written to a file and a git credential helper instead of attaching the repository with add_repo'
status: active
supersedes: []
recurrence_of: L-20261009T160400Z-pasted-token-rejected-401-add-repo-not-tried-first
occurrences: 1
severity: Medium
tags: [tech:github, tech:git, kind:security, phase:planning]
recorded_by: planner
run: gen-20261004T095012Z-singing-voice-vst-pitch-lyrics
recorded_at: 2026-10-10T00:01:01Z
---
## Trigger
The human pastes a GitHub token in chat; an add_repo tool exists or may exist in the session.
## What went wrong
The token was stored in ~/.tok and wired into a global credential.helper; add_repo was never tried. In the next session the proxy rejected the token for unattached repositories anyway.
## Correction
Deleted the file, attached sing-vst, knowledge and lessons with add_repo (access push), and pushed through the session proxy. Advised the human to revoke the token.
## Prevention rule
Call add_repo with access push for every repository the task names before reading or using any pasted token, and never write a pasted token to disk.
## Detection check
`grep -rIl 'github_pat_\|ghp_' ~ 2>/dev/null` and `git config --global --get-regexp credential` print nothing.
## Evidence
Bash history of 2026-10-04 (`printf ... > .tok`); add_repo results of 2026-10-10.
