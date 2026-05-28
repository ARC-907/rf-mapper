import os

ONYX_MODE = os.getenv("ONYX_MODE", "full").lower()
IS_LITE = ONYX_MODE == "lite"
