import sys
from pathlib import Path

# Ensure the project root is on sys.path so tests importing `src` work
ROOT = Path(__file__).resolve().parents[1]
ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)
