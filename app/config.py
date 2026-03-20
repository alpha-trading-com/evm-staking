"""Path setup, env loading, and shared constants."""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)

from dotenv import load_dotenv
load_dotenv(REPO_ROOT / ".env")

COLDKEY_SS58 = os.getenv("COLDKEY", "5GBY9k83ydqCedqg1NLrWTKy8R6afTkwz5FPSyar3tCcBGQ5")
