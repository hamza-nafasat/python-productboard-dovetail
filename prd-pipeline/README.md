# Automated PRD Generation Pipeline

A production-ready Streamlit application for enterprise product managers. It integrates **Dovetail**, **Productboard**, **Anthropic Claude**, and **Confluence** to generate, review, and publish Product Requirements Documents (PRDs) through a multi-step wizard.

## Features

- **Step 1 – Setup**: API configuration (Dovetail, Productboard, Anthropic, Confluence) with test connection and status indicators
- **Step 2 – Data sources**: Select Dovetail projects and Productboard areas with filters (tags, date range, priority)
- **Step 3 – Prompt config**: PRD template, product context, business goals, constraints, audience, tone, roadmap option
- **Step 4 – PRD generation**: Async pipeline with progress, logs, and retry
- **Step 5 – PRD review**: Markdown editor, side-by-side preview, section regeneration, version comparison
- **Step 6 – Publish**: Publish to Confluence (title, parent page, space, preview)
- **Step 7 – History**: Local audit of generated PRDs with metadata and export

## Setup

1. **Clone and enter the project**
   ```bash
   cd prd-pipeline
   ```

2. **Virtual environment (recommended)**  
   On Debian/Ubuntu you may need: `sudo apt install python3-venv` first.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment variables (optional)**  
   Copy `.env.example` to `.env` and fill in API keys for local development. The app prioritizes keys entered manually in the UI (session state).

## Run

**Option A – Use the run script (creates venv if missing, installs deps, starts app)**

```bash
# Linux/macOS
chmod +x run.sh && ./run.sh

# Windows
run.bat
```

**Option B – Manual (with venv already activated)**

From the project root:

```bash
streamlit run app/main.py
```

Then open the URL shown in the terminal (default: http://localhost:8501).

## Project structure

- `app/` – Entry point, config, session state, async runner
- `api/` – API clients (Dovetail, Productboard, Anthropic, Confluence)
- `core/` – PRD generator, prompts, data models
- `services/` – History store (local JSON)
- `ui/` – Sidebar, layout, theme
- `components/` – Reusable UI (connection status, loading, forms, data preview, markdown editor)
- `pages/` – Wizard steps 1–7
- `templates/` – PRD templates

## Deployment (e.g. Streamlit Cloud)

- Set environment variables in the cloud dashboard for API keys if you want to prefill (optional).
- Do not commit `.env` or any file containing API keys.

## License

Internal use. Adjust as needed for your organization.
