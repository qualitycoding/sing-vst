# Pre-mortem: round 7 (Phase 4, Amendment 02 scope)

**Scope.** I re-read the steps that Amendment 02 adds or changes: S-REVIEW, S-ADVERSARIAL, S-MUTATE, the post-conditions of
S-017…S-KNOW, D-042, D-043 and D-044, and how they interact with the open gate G-004. I asked one question for each: assume the
plan failed at this point; why did it fail? Severities follow Rule 4.

| # | Failure story | Severity | Outcome |
|---|---|---|---|
| 1 | S-REVIEW finds a High defect in `python/` after G-004 was issued, and the owner trains on the defective commit anyway. | High | D-042 re-issue rule; **R-119** |
| 2 | The owner started the run before the re-issue; the upload passes S-017's checks because the old pin is on the impl branch. | Medium | D-042 `pre-fix` rule, S-017 action 2a; **R-120** |
| 3 | S-MUTATE's target is unreachable with the frozen suite, and the implementer is tempted to lower it or add tests. | Low | Measured baseline in D-044; expected halt and planning amendment; **R-121** |
| 4 | mutmut cannot run the suite: the frozen conftest puts `<root>/python` first on `sys.path`, T-P25 starts a child process, T-P08b needs git. | Medium | Found and fixed by the spike (workspace layout, `.pth` file, empty commit); S-MUTATE copies the spike exactly. No new risk. |
| 5 | Coverage commands differ from what the plan quotes. | Low | Spike research/spikes/coverage ran them; S-REVIEW quotes them. No new risk. |
| 6 | S-ADVERSARIAL probes crash the host (5000-note, 900 s, cancel storms). | Low | They run against `../build-asan` with per-probe timeouts, as S-ADVERSARIAL says. No new risk. |
| 7 | New review steps make S-019 wait on G-004 although they finished early. | — | Not a failure: S-019 already waits on S-017. |

**Convergence.** This round adds three risks: one High (mitigated), one Medium (mitigated) and one Low (open, expected). No Critical or
High item is open in the amendment's scope.
