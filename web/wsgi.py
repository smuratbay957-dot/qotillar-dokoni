import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from app import app as application  # noqa: E402
from app import init_db  # noqa: E402

init_db()
