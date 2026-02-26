# PRD Pipeline (Streamlit app)

This folder is the main **PRD Generation Pipeline** app. For a full **project overview** (libraries, flow, structure), see the root **[README.md](../README.md)** in the repo.

---

## What this app does

- **Step 1 – Setup**: Enter Dovetail, Productboard, and Confluence API keys; test connections.
- **Step 2 – Data sources**: Select which Dovetail projects and Productboard features/notes to use.
- **Step 3 – Prompt config**: Set product context, business goals, constraints, audience, tone, and roadmap option. Config is saved when you go to Step 4 so it stays visible after “Refresh status”.
- **Step 4 – Generate PRD prompt**: Runs a pipeline that fetches your selected data, builds one combined prompt (your config + Dovetail summary + Productboard summary). You click “Refresh status” when done, then **copy the prompt into your own AI tool** (e.g. ChatGPT, Claude) to generate the PRD. The app does not call an LLM.
- **Step 5 – PRD review**: Paste the PRD from your AI tool, edit in the app, compare versions.
- **Step 6 – Publish**: Publish the current PRD to Confluence (parent page, title, space).

History is available from the sidebar (local JSON store).

---

## Setup

1. **Go to this directory**
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

3. **Environment (optional)**  
   - Copy `.env.example` to `.env` and add API keys for local dev; the app can prefill from them.
   - Or use Streamlit secrets (e.g. `.streamlit/secrets.toml`). If no secrets file exists, the app still runs; you enter keys in Step 1.

---

## Run

**Option A – Run script (creates venv if missing, installs deps, starts app)**

```bash
# Linux/macOS
chmod +x run.sh && ./run.sh

# Windows
run.bat
```

**Option B – Manual (with venv already activated)**

From **prd-pipeline**:

```bash
streamlit run app/main.py
```

Then open the URL shown (default: http://localhost:8501).

---

## Project structure (this folder)

| Path | Purpose |
|------|--------|
| `app/` | Entry point (`main.py`), config, session state, optional API server |
| `api/` | Dovetail, Productboard, Confluence API clients |
| `core/` | Data models, `run_pipeline()` (fetch + summarize + build prompt) |
| `services/prompt_builder/` | Prompt assembly (strategies, normalizer, config) |
| `services/history.py` | Local PRD history (JSON) |
| `pages/` | Wizard steps 1–6 (one file per step) |
| `ui/` | Sidebar, theme, layout |
| `components/` | Connection status, forms, markdown editor, etc. |
| `data/`, `logs/` | Created at runtime |
| `scripts/` | e.g. `verify_prompt_build.py` to check prompt content |

---

## Deployment (e.g. Streamlit Cloud)

- Set environment variables or Streamlit secrets for API keys if you want prefilled values (optional).
- Do not commit `.env` or any file containing API keys.

---

## License

Internal use. Adjust as needed for your organization.
