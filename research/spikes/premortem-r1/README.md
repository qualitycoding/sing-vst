# Pre-mortem round 1 spikes (2026-10-16)
- `take_cache_sketch.cpp` — planning sketch of D-038; compiled with tests/cpp/test_take_cache.cpp and Catch2 v3.16.1:
  "All tests passed (21 assertions in 2 test cases)". It caught the 56 + 4n size (the first draft of T-067 said 52).
- `limits_fixture_check.py` / `.out.txt` — the SMF bytes T-069 builds parse as intended with mido 1.3.3.
- `rvc_resume.txt` — RVC 81eed5e resume and final-save behaviour, read from the pinned source (C-061).
- `notebook_deps.txt` — RVC's cu128 file lists no torch requirement; webrtcvad 2.0.10 imports pkg_resources, webrtcvad-wheels
  2.0.14 does not on Python ≥ 3.8; Resemblyzer 0.1.4 requires `webrtcvad` (C-062).
