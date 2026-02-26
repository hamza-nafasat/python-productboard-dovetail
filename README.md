# PRD Generation Pipeline

A **Streamlit** app that helps product managers build **Product Requirements Documents (PRDs)** by pulling user research from **Dovetail**, product feedback from **Productboard**, and combining them with your instructions into a single prompt. You then copy that prompt into your own AI tool (e.g. ChatGPT, Claude) to generate the PRD, and can optionally publish the result to **Confluence**.

---

## What this project does (high-level)

1. **Connect** – You enter API keys for Dovetail, Productboard, and (optionally) Confluence.
2. **Select data** – You pick which Dovetail projects and Productboard features/notes to use.
3. **Configure the prompt** – You set product context, business goals, constraints, audience, tone, and whether to include a roadmap section.
4. **Generate a prompt** – The app fetches the selected data, merges it with your config, and produces one **text prompt** (no AI call inside the app).
5. **Use the prompt elsewhere** – You copy that prompt into your preferred AI tool to get the actual PRD.
6. **Review & publish** – You paste the PRD back into the app to edit, compare versions, and optionally publish to Confluence.

So: **this app builds the prompt and manages the workflow; it does not call an LLM itself.** For a detailed explanation of how the prompt is built (which steps, which inputs, and the final structure), see **[PROMPT_BUILDING.md](PROMPT_BUILDING.md)**.

---

## Libraries and tech stack

| Library / tech | Purpose |
|----------------|--------|
| **Streamlit** | Web UI, wizard steps, forms, session state |
| **httpx** | HTTP client for Dovetail, Productboard, Confluence APIs |
| **Pydantic** | Data models and validation (config, API payloads, prompt builder) |
| **python-dotenv** | Optional: load API keys from `.env` for local dev |
| **FastAPI** | Optional: REST API server (e.g. `api_server.py`) for headless/automation |
| **uvicorn** | Optional: ASGI server for FastAPI |

All are listed in `requirements.txt` (repo root and `prd-pipeline/`).

---

## How the flow works (step by step)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Setup                                                              │
│  Enter Dovetail API key, Productboard API key, Confluence URL/space/token.  │
│  Test connections. Keys live in session only (or optional .env / secrets).   │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: Data sources                                                       │
│  App fetches your Dovetail projects and Productboard features/notes.         │
│  You select which projects/items to include in the prompt.                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: Prompt configuration                                               │
│  Set: product context, business goals, constraints, audience, tone,         │
│  roadmap yes/no. Stored in session and in a snapshot when you go to Step 4.  │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: Generate PRD prompt                                                │
│  • Pipeline runs in a background thread.                                    │
│  • Fetches Dovetail insights and Productboard data for your selections.     │
│  • Builds one prompt = your instructions + Dovetail summary + Productboard   │
│    summary (via services/prompt_builder).                                    │
│  • You click “Refresh status” to see when it’s done, then copy the prompt   │
│    into your AI tool. Your Step 3 config is kept (snapshot) so it doesn’t   │
│    disappear after refresh.                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: PRD review                                                          │
│  Paste the PRD you generated with your AI tool. Edit in the app, compare     │
│  versions, then proceed to publish.                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 6: Publish to Confluence                                               │
│  Set Confluence parent page and title, then publish the current PRD.         │
└─────────────────────────────────────────────────────────────────────────────┘
```

- **History** – From the sidebar you can open a history view of past runs (stored locally).

---

## How the project is structured

```
python-productboard-dovetail/
├── README.md                    # This file (project overview)
├── requirements.txt             # Python dependencies (root)
└── prd-pipeline/                # Main application
    ├── README.md                # App-specific readme (setup, run, structure)
    ├── requirements.txt         # Same deps as root (for running from prd-pipeline)
    ├── run.sh                   # Convenience: venv + pip install + streamlit run
    ├── app/
    │   ├── main.py              # Streamlit entry point, step routing
    │   ├── config.py             # Paths, step names, constants
    │   ├── state.py              # Session state init, secrets handling, step helpers
    │   └── api_server.py         # Optional FastAPI server
    ├── api/                      # External API clients
    │   ├── dovetail.py           # Dovetail API (projects, insights)
    │   ├── productboard.py       # Productboard API (features, notes)
    │   ├── confluence.py         # Confluence API (publish pages)
    │   └── base.py               # Shared HTTP/request logic
    ├── core/
    │   ├── models.py             # APIConfig, PromptConfig, etc.
    │   ├── prd_generator.py      # run_pipeline: fetch data → summarize → build prompt
    │   └── prompts.py            # Legacy prompt helpers (deprecated in favour of prompt_builder)
    ├── services/
    │   ├── prompt_builder/       # Builds the final prompt text
    │   │   ├── builder.py        # build_prompt, build_prompt_from_summaries
    │   │   ├── models.py         # PromptBuilderConfig, NormalizedInsights/Feedback, PromptResult
    │   │   ├── normalizer.py     # Normalize raw Dovetail/Productboard data
    │   │   └── strategies/       # e.g. default strategy (sections, tone, audience)
    │   └── history.py            # Local PRD history (JSON)
    ├── pages/                    # One module per wizard step
    │   ├── step_setup.py         # Step 1
    │   ├── step_data_sources.py  # Step 2
    │   ├── step_prompt_config.py # Step 3
    │   ├── step_generation.py    # Step 4
    │   ├── step_review.py        # Step 5
    │   └── step_publish.py       # Step 6
    ├── ui/                       # Sidebar, theme, layout
    ├── components/               # Reusable UI (connection status, forms, markdown editor, etc.)
    ├── data/                     # Created at runtime (e.g. history JSON)
    ├── logs/                     # App logs
    └── scripts/
        └── verify_prompt_build.py # Script to verify prompt contains config + Dovetail/Productboard
```

**Data flow (prompt generation):**

- **Step 2** → `selected_dovetail_project_ids`, `selected_productboard_ids` (session state).
- **Step 3** → Prompt config (product context, goals, constraints, audience, tone, roadmap) in session state; when you click “Next”, a **snapshot** is saved so it isn’t lost on Step 4 (where Step 3 widgets aren’t rendered).
- **Step 4 “Generate PRD prompt”** → `run_pipeline()` in `core/prd_generator.py`:
  - Fetches Dovetail projects/insights and Productboard features/notes using the selected IDs.
  - Summarizes them into text.
  - Calls `build_prompt_from_summaries(dovetail_summary, productboard_summary, config)` from `services/prompt_builder`.
  - Returns one prompt string (no LLM call). The UI shows it; you copy it into your AI tool.

---

## Quick start

1. **Clone and go to the app directory**
   ```bash
   cd prd-pipeline
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux/macOS; on Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   ./run.sh
   ```
   or, with venv already activated:
   ```bash
   streamlit run app/main.py
   ```
   Then open the URL shown (default: http://localhost:8501).

4. **Optional** – Copy `.env.example` to `.env` and add API keys so the app can prefill them (or use Streamlit’s secrets). If no secrets file exists, the app still runs; you type keys in Step 1.

For more detail (troubleshooting, deployment, structure), see **`prd-pipeline/README.md`**.

---

## Summary

- **Libraries:** Streamlit, httpx, Pydantic, python-dotenv; optionally FastAPI/uvicorn.
- **Flow:** Setup → Select Dovetail/Productboard data → Configure prompt → Generate one combined prompt → Copy to your AI tool → Paste PRD back → Review → Publish to Confluence.
- **How it works:** The app fetches and summarizes Dovetail and Productboard data, merges that with your Step 3 config into a single prompt, and shows it to you. You use your own AI tool to turn that prompt into a PRD, then use the app again to review and publish.
