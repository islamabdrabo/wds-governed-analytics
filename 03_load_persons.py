import sqlite3
import pandas as pd
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"
CSV_PATH = BASE_DIR / "data" / "workforce master.csv"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

WARNINGS_PATH = LOGS_DIR / "import_warnings.csv"

# --- Load CSV ---
df = pd.read_csv(CSV_PATH, low_memory=False)

# --- Connect DB ---
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

# --- Build lookup maps ---
def build_map(table, id_col, name_col):
    rows = cur.execute(f"SELECT {id_col}, {name_col} FROM {table}").fetchall()
    mapping = {}
    for _id, name in rows:
        if name is None:
            continue
        normalized = str(name).strip()
        if normalized:
            mapping[normalized] = _id
    return mapping

specialty_map = build_map("specialties", "specialty_id", "specialty_name")
region_map    = build_map("regions", "region_id", "region_name")
workplace_map = build_map("workplaces", "workplace_id", "workplace_name")

# --- Prepare warnings ---
warnings = []

# --- Insert persons ---
inserted = 0
skipped_duplicates = 0

for idx, row in df.iterrows():
    person_id = str(row.get("civil id")).strip()

    if not person_id or person_id.lower() == "nan":
        warnings.append({
            "row_index": idx,
            "issue": "missing_civil_id"
        })
        continue

    # Check duplicate
    exists = cur.execute(
        "SELECT 1 FROM persons WHERE person_id = ?",
        (person_id,)
    ).fetchone()

    if exists:
        skipped_duplicates += 1
        warnings.append({
            "row_index": idx,
            "person_id": person_id,
            "issue": "duplicate_civil_id"
        })
        continue

    specialty_id = specialty_map.get(str(row.get("final specialty")).strip())
    region_id    = region_map.get(str(row.get("region")).strip())
    workplace_id = workplace_map.get(str(row.get("workplace")).strip())

    # Log missing dimensions
    if specialty_id is None:
        warnings.append({
            "row_index": idx,
            "person_id": person_id,
            "issue": "missing_specialty"
        })
    if region_id is None:
        warnings.append({
            "row_index": idx,
            "person_id": person_id,
            "issue": "missing_region"
        })
    if workplace_id is None:
        warnings.append({
            "row_index": idx,
            "person_id": person_id,
            "issue": "missing_workplace"
        })

    cur.execute("""
        INSERT INTO persons (person_id, specialty_id, region_id, workplace_id)
        VALUES (?, ?, ?, ?)
    """, (person_id, specialty_id, region_id, workplace_id))

    inserted += 1

conn.commit()
conn.close()

# --- Write warnings ---
if warnings:
    pd.DataFrame(warnings).to_csv(WARNINGS_PATH, index=False)

print("[DONE] Persons loaded")
print(f"[INFO] Inserted persons: {inserted}")
print(f"[INFO] Skipped duplicates: {skipped_duplicates}")
print(f"[INFO] Warnings file: {WARNINGS_PATH if warnings else 'none'}")
