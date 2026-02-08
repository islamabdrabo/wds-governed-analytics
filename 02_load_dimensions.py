import sqlite3
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"
CSV_PATH = BASE_DIR / "data" / "workforce master.csv"


def cleaned_values(df: pd.DataFrame, column_name: str):
    values = (
        df[column_name]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    values = values[values != ""]
    values = values.drop_duplicates()
    return values.tolist()


df = pd.read_csv(CSV_PATH, low_memory=False)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()


def load_dimension(table_name: str, source_col: str, target_col: str):
    values = cleaned_values(df, source_col)
    cur.executemany(
        f"INSERT OR IGNORE INTO {table_name} ({target_col}) VALUES (?)",
        [(v,) for v in values],
    )
    print(f"[OK] {table_name}: {len(values)} candidate rows")


load_dimension("specialties", "final specialty", "specialty_name")
load_dimension("regions", "region", "region_name")
load_dimension("workplaces", "workplace", "workplace_name")

conn.commit()
conn.close()

print("[DONE] Dimensions loaded")
