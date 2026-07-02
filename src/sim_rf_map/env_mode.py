import os

# Frozen at import time by design (the GUI reads it once at startup).
# Normalization matches mode_selector.choose_mode: strip + lower.
ONYX_MODE = os.getenv("ONYX_MODE", "full").strip().lower()
IS_LITE = ONYX_MODE == "lite"
