import os
import sys
from pathlib import Path

os.environ["GROQ_API_KEY"] = "chave-falsa-de-teste"
os.environ["APP_ENV"] = "development"
os.environ["RATE_LIMIT_CHAT"] = "100000 per minute"
os.environ["RATE_LIMIT_DIARIO"] = "100000 per day"
os.environ["RATE_LIMIT_GLOBAL"] = "100000 per hour"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "servidor"))
