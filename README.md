# WDS Governed Analytics

Desktop Streamlit application for governed workforce analytics, controlled staging, batch approval, and audited apply.

For fastest iPad deployment, see: `DEPLOY_STREAMLIT_EASY.md`

## 1) Setup

```powershell
cd C:\Users\Islam\Desktop\WDS_GOVERNED_ANALYTICS_DESKTOP_WINDOWS_PACKAGE
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Run Locally (PC Browser)

- Double-click `WDS.cmd` (background launch + open browser), or
- Run `RUN_WDS.bat` in terminal.

Default URL:

- `http://127.0.0.1:8501`

## 3) Run for iPad (Same Wi-Fi)

1. Run `RUN_WDS_IPAD.bat`.
2. Script prints a URL like `http://192.168.x.x:8501`.
3. Open that URL in Safari on iPad.

Notes:

- PC and iPad must be on the same network.
- If Windows Firewall prompts, allow Python/Streamlit on private networks.

## 4) Database Bootstrap / Refresh

Run import scripts in order if you need a fresh rebuild:

```powershell
python import\01_create_schema.py
python import\02_load_dimensions.py
python import\03_load_persons.py
python import\04_add_indexes.py
python import\05_create_views.py
python import\07_create_staging.py
python import\07_create_specialty_aliases.py
python import\08_load_specialty_aliases.py
python import\09_create_canonical_views.py
python import\10_create_canonical_base_view.py
```

## 5) Tests

```powershell
pytest
```

## 6) Cloud Deployment

### Option A (Recommended): Render

This option is best when you need write persistence for SQLite.

1. Upload this project to a GitHub repository.
2. In Render Dashboard, create a new Web Service from that repository.
3. Use:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python run_cloud.py`
4. Add environment variable:
   - `WDS_DB_PATH=/var/data/workforce.db`
5. (Important) Add a Persistent Disk and mount it at `/var/data`.
6. Deploy and open your Render URL on iPad.

Notes:
- Without a persistent disk, local filesystem changes are lost on redeploy/restart.
- If you keep SQLite writes, persistence is required.

### Option B (Free + Fast): Streamlit Community Cloud

1. Push the project to GitHub.
2. Go to `share.streamlit.io` and click **Create app**.
3. Select repository/branch and entrypoint file: `app/unified_app.py`.
4. Deploy and open the generated `*.streamlit.app` URL on iPad.

Note:
- Community Cloud does not guarantee persistence of local file storage across sessions.
- If persistent writes are required, use Option A (Render + disk) or move DB to managed service.
