import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

cur.executescript(
    """
    DROP TABLE IF EXISTS persons;
    DROP TABLE IF EXISTS specialties;
    DROP TABLE IF EXISTS regions;
    DROP TABLE IF EXISTS workplaces;

    CREATE TABLE specialties (
        specialty_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        specialty_name TEXT NOT NULL CHECK (LENGTH(TRIM(specialty_name)) > 0)
    );

    CREATE TABLE regions (
        region_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        region_name TEXT NOT NULL CHECK (LENGTH(TRIM(region_name)) > 0)
    );

    CREATE TABLE workplaces (
        workplace_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        workplace_name TEXT NOT NULL CHECK (LENGTH(TRIM(workplace_name)) > 0)
    );

    CREATE TABLE persons (
        person_id    TEXT PRIMARY KEY NOT NULL CHECK (LENGTH(TRIM(person_id)) > 0),
        specialty_id INTEGER,
        region_id    INTEGER,
        workplace_id INTEGER,
        FOREIGN KEY (specialty_id) REFERENCES specialties(specialty_id),
        FOREIGN KEY (region_id) REFERENCES regions(region_id),
        FOREIGN KEY (workplace_id) REFERENCES workplaces(workplace_id)
    );

    CREATE UNIQUE INDEX idx_specialties_name_unique
    ON specialties (specialty_name COLLATE NOCASE);

    CREATE UNIQUE INDEX idx_regions_name_unique
    ON regions (region_name COLLATE NOCASE);

    CREATE UNIQUE INDEX idx_workplaces_name_unique
    ON workplaces (workplace_name COLLATE NOCASE);
    """
)

conn.commit()
conn.close()

print("[OK] SQLite schema created with integrity constraints")
