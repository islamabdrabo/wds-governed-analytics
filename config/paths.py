import os
from pathlib import Path


def _resolve_path(env_name: str, default_path: Path) -> Path:
    value = os.getenv(env_name, "").strip()
    if not value:
        return default_path
    return Path(value).expanduser().resolve()


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = _resolve_path("WDS_DATA_DIR", PROJECT_ROOT / "data")
DB_DIR = _resolve_path("WDS_DB_DIR", PROJECT_ROOT / "db")
LOGS_DIR = _resolve_path("WDS_LOGS_DIR", PROJECT_ROOT / "artifacts" / "logs")
EXPORTS_DIR = _resolve_path("WDS_EXPORTS_DIR", PROJECT_ROOT / "artifacts" / "exports")
EXPORT_DIR = EXPORTS_DIR

CSV_PATH = _resolve_path("WDS_CSV_PATH", DATA_DIR / "workforce master.csv")
DB_PATH = _resolve_path("WDS_DB_PATH", DB_DIR / "workforce.db")

# Ensure writable folders exist in all environments (desktop/cloud).
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
