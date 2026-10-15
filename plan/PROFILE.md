# Profile (Rule 0)

**Active profiles:** `software`, `computational` (computational implies software).
- `software`: the deliverable is code that must run: a VST3/Standalone plugin, a CLI and a Python training toolkit.
- `computational`: correctness of the outcome depends on computation — pitch mapping, frame timing, resampling, ONNX
  numerics, and objective voice-quality metrics whose values are unknown until a trained voice exists (Rule 8).

**Mode flags:** `software.deploys = false` (no service is operated; a binary release, if ever wanted, is gate G-002).

**Inactive profiles:** `math` (no statements are proved), `publication` (no manuscript or archive deposit).

**Not applicable (no artefacts, no checks):** 2A (all), 2D (all), R2b novelty search, `math/*`, `manuscript/*`,
`research/NOVELTY.md`, `plan/OPERATIONS.md`, deployment tests and operational forks for running services, publication
lenses of the pre-mortem. 2C (figures) applies to `computational` only through deliverable figures, and **this plan has
none** (results are a JSON report and audio files at G-001), so `figures/SPEC.md` is not produced (decision D-032).
