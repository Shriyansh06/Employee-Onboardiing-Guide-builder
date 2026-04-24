"""Root Streamlit entrypoint."""

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parent / "project"
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


def main() -> None:
    try:
        from project.app import main as project_main
    except Exception as exc:
        import streamlit as st

        st.set_page_config(page_title="App Startup Error", layout="wide")
        st.error("Failed to load application logic from `project/app.py`.")
        st.exception(exc)
        return

    project_main()


if __name__ == "__main__":
    main()
