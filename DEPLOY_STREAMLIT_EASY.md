# Easy Deploy (Streamlit Cloud)

Use this path if you want the fastest way to run on iPad with a public URL.

## 1) Push project to GitHub

From project folder:

```powershell
git init
git add .
git commit -m "WDS cloud-ready"
git branch -M main
git remote add origin https://github.com/<YOUR_USER>/<YOUR_REPO>.git
git push -u origin main
```

## 2) Deploy in Streamlit Cloud

1. Open: `https://share.streamlit.io`
2. Click `Create app`
3. Select your repo + branch `main`
4. Main file path: `app/unified_app.py`
5. Click `Deploy`

## 3) Open on iPad

Open the generated URL:

`https://<your-app>.streamlit.app`

## Important note

Streamlit Cloud storage is not persistent for SQLite writes.
If you need permanent data changes, deploy on Render with a persistent disk.
