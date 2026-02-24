#!/usr/bin/env bash
# Run the PRD Pipeline app inside the project venv.
set -e
cd "$(dirname "$0")"

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt
exec streamlit run app/main.py "$@"
