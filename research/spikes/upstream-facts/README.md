Spike R6 round 2 (2026-10-10). `bash verify.sh <empty scratch dir>` clones each pinned upstream ref and asserts every code-level fact a claim rests on.
Output: output.txt (all PASS). Also prints upstream drift (latest tags) used for pinning in plan/ENVIRONMENT.md.
Two checks failed on the first run because of mistakes in the check, not upstream (C-022b quoting) and because a recalled
pluginval flag (--validate-in-process) does not exist (C-015b/c; lesson L-20261010T001500Z-ci-tool-flags-and-versions-from-memory).
