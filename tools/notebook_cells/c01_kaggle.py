# (1) The GPU check comes first: this notebook needs Accelerator = GPU T4, Internet = On, and a phone-verified account.
import time
CLOCK = globals().get("CLOCK", time.time)
SESSION_T0 = CLOCK()
!nvidia-smi
print("PRIVACY: keep the Kaggle dataset singvst-<VOICE> and this notebook Private, and never publish a version (A-011, R-021).")
print("Run as 'Save & Run All'. Check your weekly GPU quota in Settings before starting.")
