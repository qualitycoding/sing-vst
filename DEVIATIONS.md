# DEVIATIONS — v3.9 addendum amendment

**Repository:** `qualitycoding/sing-vst` — 2026-11-02.

1. **Source-tip drift (D-901).** Planning source branch tip `19e9056288eb64cde570ea2a156c3570acb1b675` is the
   rollout phase's addendum publication commit, direct child of audited
   `657cb1764f767cbedac0079bb8ce95786440eea8`. Implementation branch descends from the tip; nothing newer was
   overwritten.
2. **Git transport unavailable (D-905).** `github.com:443` git transport is
   blocked from this sandbox; all clone-equivalent reads used `codeload` and all
   commits/pushes used the authenticated GitHub Git database API. Remote SHAs
   were verified after every push via the refs API. The addendum's
   push-and-verify cadence was preserved in substance.
3. **No local build/test/mutation execution (D-905).** Estimates in
   `reviews/MUTATION.md` and the CI matrix are marked as estimates pending the
   first CI run; no unrun check is reported as passed.
4. **No fresh-context reviewer (D-906).** Cold read and adversarial review
   recorded as same-author substitutions with High risk, per S-ADD-090.
5. **Learning-store push deferred.** G-003 destinations requested; pushes
   await sign-off (do-not-push until then).
