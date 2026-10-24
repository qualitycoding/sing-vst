# (2a) Parameters. The owner edits this cell; GATE-G-004.md states every value (D-035).
import re
VOICE = "myvoice"                  # lower-case letters, digits and "-"
RUN = 1
EXPECTED_COMMIT = ""               # the 40-hex commit named in GATE-G-004.md
RESUME = False                     # @RESUME_RULE@
PLATFORM_EXPECTED = ""             # "colab" or "kaggle", as GATE-G-004.md states
PRUNE = ""                         # @PRUNE_RULE@
PRIOR_VOICE_GPU_HOURS = 0.0        # GPU hours of this voice that this platform's budget-voice.json does not hold (GATE-G-004.md)
KILLED_HOURS = 0.0                 # @KILLED_RULE@
DEREVERB = False
EPOCHS = 200                       # a multiple of 10
SPEAKER_ID = 0
GUIDE = "tiger"
assert re.fullmatch(r"[a-z0-9-]+", VOICE), "VOICE: lower-case letters, digits and - only"
assert isinstance(RUN, int) and RUN >= 1, "RUN must be a whole number from 1"
assert re.fullmatch(r"[0-9a-f]{40}", EXPECTED_COMMIT), "EXPECTED_COMMIT must be the 40-hex commit named in GATE-G-004.md"
assert isinstance(EPOCHS, int) and EPOCHS > 0 and EPOCHS % 10 == 0, "EPOCHS must be a positive multiple of 10"
assert isinstance(SPEAKER_ID, int) and SPEAKER_ID >= 0
