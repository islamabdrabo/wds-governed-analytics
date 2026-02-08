import os
import sys

from streamlit.web import cli as stcli


def main() -> int:
    port = os.getenv("PORT", "8501")
    sys.argv = [
        "streamlit",
        "run",
        "app/unified_app.py",
        "--server.address=0.0.0.0",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    return stcli.main()


if __name__ == "__main__":
    raise SystemExit(main())
