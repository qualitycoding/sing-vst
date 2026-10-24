# (1) The GPU check comes first: Runtime -> Change runtime type -> a GPU (T4 is enough).
import time
CLOCK = globals().get("CLOCK", time.time)
SESSION_T0 = CLOCK()
!nvidia-smi
