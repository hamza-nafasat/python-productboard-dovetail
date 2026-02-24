@echo off
REM Run the PRD Pipeline app inside the project venv.
cd /d "%~dp0"

if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
streamlit run app/main.py %*
