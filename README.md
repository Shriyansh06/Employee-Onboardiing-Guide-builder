# Onboarding Intelligence?

Onboarding Intelligence is a Streamlit app that generates role-specific onboarding guides using a multi-agent pipeline.

The workflow runs five agents in sequence: research, policy fetch, plan building, guide writing, and quality judging.
This project supports Grok (xAI) API usage through the OpenAI-compatible client path.

## What This Project Does

1. Takes free-text employee context from the UI.
2. Extracts structured employee info (`name`, `role`, `department`, `seniority`).
3. Runs orchestrated agents to produce:
   - role research output,
   - policy context,
   - a 30/60/90 onboarding plan,
   - a final markdown onboarding guide,
   - quality evaluation scores and improvement suggestions.

## Agents In This Repository

- `agents/role_researcher.py`
  - Uses Tavily search (`TAVILY_API_KEY`) for role/domain research.
  - Synthesizes strict JSON with sources, best practices, tools, tasks, and timeline.
- `agents/policy_fetcher.py`
  - Loads `data/company_policies.json`.
  - Maps policy groups based on employee department.
- `agents/plan_builder.py`
  - Builds a 30/60/90 plan using research + policies + employee context.
  - Validates plan structure with `jsonschema`.
- `agents/guide_writer.py`
  - Produces the final onboarding guide in markdown.
  - Supports regeneration with prior judge suggestions.
- `agents/judge_agent.py`
  - Evaluates the guide and returns category scores plus improvements.

## Core Files

- `app.py` - Streamlit UI, provider selection, employee-info extraction, and result rendering
- `orchestrator.py` - shared state, retries, validation/coercion, and regeneration loop
- `test_agents.py` - unit tests for policy and orchestrator helpers
- `run.bat` - Windows command to launch Streamlit
- `.env.example` - environment variable template

## Tech Stack Actually Used

- Python 3.11+
- `streamlit`
- `google-genai`
- `openai` (used as OpenAI-compatible client for Grok/xAI and Groq)
- `tavily-python`
- `python-dotenv`
- `jsonschema`

Dependencies are defined in `..\requirements.txt`.

## Quick Start (Windows / PowerShell)

```powershell
cd E:\employee
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
cd .\project
pip install -r ..\requirements.txt
```

Create `.env` from `.env.example`, then run:

```powershell
..\.venv\Scripts\python.exe -m streamlit run app.py
```

Or use:

```powershell
run.bat
```

## Deploy On Railway

This repository is configured to run on Railway using the root `app.py` entrypoint.

Added deployment files at repository root:

- `Procfile`
- `railway.toml`

Both use the same command:

```bash
python -m streamlit run app.py --server.address 0.0.0.0 --server.port $PORT --server.headless true
```

### Railway setup

1. Deploy this repo from GitHub in Railway.
2. Set required environment variables in Railway Variables:
   - `XAI_API_KEY` or `GROQ_API_KEY` or `GOOGLE_API_KEY`/`GEMINI_API_KEY`
   - optional: `TAVILY_API_KEY`
3. Redeploy.

### Local Streamlit still works

Local launch remains unchanged:

```powershell
cd E:\employee\project
..\.venv\Scripts\python.exe -m streamlit run app.py
```

## Environment Variables Used

### API keys

- `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `XAI_API_KEY` (Grok/xAI API key)
- `TAVILY_API_KEY`

At least one model-provider key is required for generation.  
If `XAI_API_KEY` is set, the app uses xAI's Grok-compatible endpoint.  
`TAVILY_API_KEY` enables live research in the research agent.

### Grok-only `.env` example

```env
# Required for Grok/xAI
XAI_API_KEY=your_xai_api_key_here

# Optional but recommended for research enrichment
TAVILY_API_KEY=your_tavily_api_key_here
```

### Runtime controls

- `MAX_AGENT_RETRIES`
- `MAX_GUIDE_REGENERATIONS`
- `TAVILY_MAX_SEARCHES`
- `TAVILY_SEARCH_RETRIES`
- `RESEARCH_LLM_RETRIES`
- `PLAN_LLM_RETRIES`
- `GUIDE_LLM_RETRIES`
- `JUDGE_LLM_RETRIES`
- `PLANNER_CHAT_MODEL`
- `PLANNER_GROQ_MODEL`
- `GUIDE_CHAT_MODEL`
- `GUIDE_GROQ_MODEL`
- `JUDGE_CHAT_MODEL`
- `JUDGE_GROQ_MODEL`

## Generation Profiles In UI

The sidebar profile selector sets runtime behavior:

- `Fast`
- `Balanced`
- `Accurate`

These profiles adjust retry and search settings via environment variables at runtime.

## Run Tests

From `E:\employee\project`:

```powershell
..\.venv\Scripts\python -m unittest -q
```

## Known Limitations

- If no provider key is configured, generation cannot run.
- If `TAVILY_API_KEY` is missing, research returns fallback content.
- Policy context is limited to `data/company_policies.json`.
- Final output quality depends on external model responses.
- Current tests are unit-level and do not cover full end-to-end Streamlit execution.

## Roadmap

- Add integration tests for full pipeline runs.
- Expand policy sources beyond local JSON.
- Add persistent run history and artifact export.
- Add deeper observability for retries and stage-level timings.

## Architecture Diagram

<img width="1024" height="766" alt="image" src="https://github.com/user-attachments/assets/9ed448c7-8e9e-4858-9bd0-f1717630efe1" />


## Live App

[employee-onboardiing-guide-builder-production-b9eb.up.railway.app](https://employee-onboardiing-guide-builder-production-b9eb.up.railway.app)
