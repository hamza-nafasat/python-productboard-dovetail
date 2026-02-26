# How the PRD Prompt Is Built

This document explains how the application constructs the **PRD generation prompt**: what inputs are used, which steps run, and how the final text is assembled. The prompt is meant to be copied into your own AI tool (e.g. ChatGPT, Claude) to generate a Product Requirements Document; the app does not call an LLM itself.

---

## Overview

The prompt is built in three stages:

1. **You provide configuration** in the app (Steps 1–3): API keys, selected Dovetail/Productboard data, and prompt settings (context, goals, constraints, audience, tone, roadmap).
2. **The pipeline runs** (Step 4): It fetches the selected Dovetail projects/insights and Productboard features/notes, turns them into short text summaries, then passes those summaries and your config to the prompt builder.
3. **The prompt builder** runs a **strategy** (e.g. "default") that assembles one block of **instructions** and one block of **context** (your config + Dovetail summary + Productboard summary) into a single prompt string.

The result is one text prompt you can paste into an AI tool to get a structured PRD.

---

## Where the Inputs Come From (App Steps)

| Input | Source in the app |
|-------|-------------------|
| **API keys** | Step 1 (Setup): Dovetail API key, Productboard API key. Used only to fetch data. |
| **Selected Dovetail projects** | Step 2 (Data sources): You choose which projects to include. The pipeline fetches those projects and their insights. |
| **Selected Productboard items** | Step 2: You choose which features/notes to include. The pipeline fetches those features and notes. |
| **Prompt configuration** | Step 3 (Prompt config): Product context, Business goals, Constraints, Audience type, Output tone, Include roadmap section, PRD template. Stored in session and in a snapshot when you go to Step 4 so it is not lost. |

When you click **Generate PRD prompt** on Step 4, the app sends all of the above (keys, selected IDs, and prompt config) to the pipeline.

---

## Pipeline Steps (How the Prompt Is Produced)

The pipeline runs in `prd-pipeline/core/prd_generator.py` via `run_pipeline()`. It does the following in order.

### Step 1: Fetch Dovetail Data

- Calls the Dovetail API to get all projects (using your API key).
- Filters to the projects you selected on Step 2 (or uses the first 5 if none were selected).
- For each of those projects, fetches its **insights** from the Dovetail API.
- **Summarizes** projects and insights into one text string:
  - For each project (up to 20): `- Project: <name>`
  - For each insight (up to 50): `- Insight: <title>. <body truncated to 500 chars>`
- If there is no data, the summary is the placeholder: `"No Dovetail data selected."`

This string is called **dovetail_summary**.

### Step 2: Fetch Productboard Data

- Calls the Productboard API to get **features** and **notes** (using your API key).
- Filters to the features/notes you selected on Step 2 (or uses the first 20 of each if none were selected).
- **Summarizes** them into one text string:
  - For each feature (up to 30): `- Feature: <name>. <description truncated to 300 chars>`
  - For each note (up to 30): `- Note: <name>. <content truncated to 300 chars>`
- If there is no data, the summary is: `"No Productboard data selected."`

This string is called **productboard_summary**.

### Step 3: Build the Prompt (No AI Call)

- Your Step 3 configuration is converted into a **PromptBuilderConfig** object (product context, business goals, constraints, audience type, output tone, include roadmap, template id).
- The function **build_prompt_from_summaries** is called with:
  - `dovetail_summary`
  - `productboard_summary`
  - `config` (PromptBuilderConfig)

Inside the prompt builder:

- The two summaries are wrapped as single “insight” and “feedback” items (so the same strategy code can run whether data comes from the pipeline or from raw lists).
- A **strategy** is chosen by template id (e.g. `"default"`).
- The strategy’s **build** method produces the final prompt string and returns it with metadata (strategy id, template id, word count, section names).

The pipeline returns this prompt text (and metadata) to the app; you see it on Step 4 and can copy it into your AI tool.

---

## Prompt Builder Flow (Code Path)

```
run_pipeline() in core/prd_generator.py
    │
    ├── 1. Fetch Dovetail → dovetail_summary (string)
    ├── 2. Fetch Productboard → productboard_summary (string)
    └── 3. build_prompt_from_summaries(dovetail_summary, productboard_summary, config)
              │
              │  (in services/prompt_builder/builder.py)
              │
              ├── Wrap summaries as single insight/feedback items
              └── build_prompt(dovetail_raw, productboard_raw, config)
                        │
                        ├── normalize_insights / normalize_feedback (if using raw data)
                        ├── get_strategy(config.prd_template_id)  → e.g. DefaultStrategy
                        └── strategy.build(insights, feedback, config)  → prompt string
```

- **build_prompt_from_summaries** is used when the pipeline has already produced `dovetail_summary` and `productboard_summary`.
- **build_prompt** can also be used with raw lists of insight/feedback dicts (e.g. from the API server); in that case it runs the normalizer, then the strategy.

---

## Default Strategy: What Goes Into the Prompt

The **default** strategy lives in `prd-pipeline/services/prompt_builder/strategies/default.py`. It builds the prompt in two parts.

### Part 1: Instruction Block (System-Like Instructions)

- Tells the AI it is an expert product manager and must write a production-ready PRD in Markdown.
- **Guidelines**:
  - Audience and tone from your config (e.g. “Audience: Executives. Use a Concise tone.”).
  - Be specific, actionable, use headings and bullets.
  - Base content on the research and feedback below; do not invent data.
  - Output only the PRD Markdown.
- **Sections to include**: Problem statement, Goals, User personas, Requirements, Success metrics, Risks and mitigations, Rollout plan.
- If **Include roadmap section** is enabled, adds: “Include a high-level Roadmap section at the end with phases and milestones.”

### Part 2: User Content Block (Context for the PRD)

A single block of context is built from:

1. **Product context (problem space)** — Your “Product context” text from Step 3 (or “General product.” if empty).
2. **Business goals** — Your “Business goals” text (or “To be defined.” if empty).
3. **Constraints** — Your “Constraints” text (or “None specified.” if empty).
4. **User research (Dovetail)** — The `dovetail_summary` string (projects + insights from the pipeline).
5. **Product feedback (Productboard)** — The `productboard_summary` string (features + notes from the pipeline).

Then a short line instructs the AI to generate the full PRD in Markdown with headings and bullets.

### How the Two Parts Are Combined

- The instruction block and the user content block are joined with a separator: `---`.
- **Final prompt** = `instruction_block + "\n\n---\n\n" + user_content_block`.

So the structure is:

```
<Instructions for the AI (audience, tone, sections, roadmap yes/no)>

---

Use this context to write the PRD:

**Product context (problem space)**
<your product context>

**Business goals**
<your business goals>

**Constraints**
<your constraints>

**User research (Dovetail)**
<dovetail_summary: projects + insights>

**Product feedback (Productboard)**
<productboard_summary: features + notes>

Generate the full PRD in Markdown with the sections listed above. Use headings, bullets, and clear sections.
```

---

## Summary Table: Steps Used to Build the Prompt

| Step | What happens | What is used in the prompt |
|------|----------------|----------------------------|
| Step 1 | You enter API keys. | Keys are used only to fetch Dovetail/Productboard data; they are not put into the prompt text. |
| Step 2 | You select Dovetail projects and Productboard features/notes. | The pipeline fetches only those items and turns them into **dovetail_summary** and **productboard_summary**, which appear in the “User research (Dovetail)” and “Product feedback (Productboard)” sections. |
| Step 3 | You set Product context, Business goals, Constraints, Audience type, Output tone, Include roadmap, PRD template. | All of these are passed as **PromptBuilderConfig** into the prompt builder. Product context, goals, and constraints are inserted as-is into the context block; audience and tone go into the instruction block; roadmap and template control which strategy/sections are used. |
| Pipeline | Fetches Dovetail and Productboard data, summarizes them, then calls the prompt builder with summaries + config. | Produces the single prompt string (instruction + separator + context) that you see on Step 4. |

---

## Where to Find This in the Codebase

| What | File / location |
|------|------------------|
| Pipeline: fetch data + summarize + call prompt builder | `prd-pipeline/core/prd_generator.py` — `run_pipeline()`, `_summarize_dovetail()`, `_summarize_productboard()` |
| Build prompt from summaries | `prd-pipeline/services/prompt_builder/builder.py` — `build_prompt_from_summaries()`, `build_prompt()` |
| Default prompt structure (instruction + context) | `prd-pipeline/services/prompt_builder/strategies/default.py` — `DefaultStrategy.build()` |
| Config model for the builder | `prd-pipeline/services/prompt_builder/models.py` — `PromptBuilderConfig` |
| App: collect config and trigger pipeline | `prd-pipeline/pages/step_generation.py` — payload built from snapshot + session state, then `_run(payload)` which calls `run_pipeline()`. |

This should give you a clear picture of how the prompt is made and which steps and inputs affect it.
