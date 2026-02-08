import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"

ALIASES = [
    ("عامل", "عامل"),
    ("عمال", "عامل"),
    ("علاج تنفس", "علاج تنفسي"),
    ("تجهيزات ادوية", "تجهيز أدوية"),
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executemany(
    "INSERT OR REPLACE INTO specialty_aliases (alias_name, canonical_name) VALUES (?, ?)",
    ALIASES
)

conn.commit()
conn.close()

print(f"[OK] {len(ALIASES)} specialty aliases loaded")
