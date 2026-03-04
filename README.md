# Clara Answers Automation Pipeline

A zero-cost automated pipeline that converts unstructured client demonstration and onboarding call transcripts into structured, versioned Retell AI voice agent configurations.

## Architecture and Data Flow

1. **Ingestion**: A user drops transcript files (e.g., `demo_1.txt` or `onboarding_1.txt`) into `data/inbox/`.
2. **Orchestration**: `n8n` (running locally via Docker) watches this folder. When a file arrives, it triggers the Python CLI Engine (`process.py`).
3. **Extraction**: `extractor.py` reads the transcript and uses the **Groq Free Tier API** (`llama-3.1-8b-instant`) to rigorously extract operations rules (business hours, emergency protocols) without hallucination, outputting an `AccountMemo` object.
4. **Agent Spec Generation**: `agent_builder.py` transforms the `AccountMemo` into a `RetellAgentSpec`. It bakes the routing rules and after-hours behaviors into a master system prompt adhering strictly to Clara's prompt hygiene requirements.
5. **Versioning & Diffs**: If the script processes an onboarding call (`v2`), it calculates the differences (`differ.py`) against the demo configuration (`v1`) and produces a markdown changelog.
6. **Task Tracker Simulation**: The system logs every generation securely to `tasks.json` to simulate integration with Asana without utilizing any paid accounts.
7. **Storage**: All assets are idempotently saved to `outputs/accounts/<account_id>/<version>/`.

## Setup Instructions

### 1. Prerequisites
- Docker & Docker Compose
- A free API key from [Groq](https://console.groq.com/keys) (preferred for extreme speed & zero usage cost).

### 2. Environment Variables
Create a `.env` file in the root directory (or export directly if running locally):
```bash
export GROQ_API_KEY="gsk_your_api_key_here"
```

### 3. Spin up n8n (Orchestrator)
The platform is fully containerized with Python integrated.
```bash
docker-compose up -d
```
1. Open http://localhost:5678 in your browser.
2. In n8n, go to Workflows -> Import from File and select `workflows/clara_pipeline.json`.
3. Activate the workflow. It will now automatically process any files dropped into `data/inbox/`.

### 4. Running the Python CLI Manually (No Docker)
If you prefer running the pipeline rapidly without n8n:

1. Setup the environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt
```

2. Generate Mock Dataset (Since no data links were provided, this will build 10 highly realistic transcripts mimicking the service trades):
```bash
python data/mock_generator.py
```

3. Run pipeline for all scripts automatically in batch mode:
```bash
python scripts/process.py --batch
```

### 5. Retell AI Integration Guide (Free Tier Constraint)
Assuming you are on a free Retell tier without unrestricted programmatic Agent API creation:

1. Open [Retell AI Dashboard](https://beta.retellai.com/dashboard).
2. Click **Create Agent** and select **Single Prompt Agent**.
3. Open `outputs/accounts/account_1/v1/agent_spec.json`.
4. Copy the `system_prompt` field in its entirety and paste it into the Retell System Prompt block.
5. (Optional but recommended): Copy the exact `key_variables` dict values to reference dynamic constraints.
6. Test your agent in the sandbox. When the `v2` update arises, you can just paste the updated `system_prompt`.

## Outputs Structure
The pipeline produces:
```
outputs/accounts/<account_id>/
├── v1
│   ├── memo.json
│   └── agent_spec.json
└── v2
    ├── memo.json
    └── agent_spec.json
changelogs/
├── <account_id>_diff.md
tasks.json
```

## Known Limitations and Safeguards
- **Hallucination Guard**: The prompt relies heavily on temperature 0 and strict instructions. If the caller didn't provide business hours, the agent spec will literally define it as "unknown" and flag it in `questions_or_unknowns`.
- ***Zero Cost Constraints**: Because APIs like Retell or Asana eventually hit severe limits or charge, we write strictly to the filesystem (`outputs/`, `tasks.json`). In a production setting, this would directly invoke the `POST /validate-agent` webhook.
- **Fail-safes**: If `litellm` fails completely to find your Groq/Ollama APIs, it will safely fallback to a pure regex/rules-based parser to cleanly guarantee pipeline execution isn't blocked by missing token balances.

## What I Would Improve With Production Access
1. **Direct Retell Provisioning**: Instead of generating a `agent_spec.json`, I'd connect to the Retell SDK and call `client.agent.create(prompt=...)` directly, associating the Return ID to our database.
2. **Visual Diff Pipeline**: Set up a React based dashboard to show a side-by-side diff between v1 and v2 memos to allow human operators to approve changes before they get dispatched to the live agent.
3. **CRM Webhooks**: Integrate ServiceTrade logic directly to inject actual availability matrices depending on real technician routes instead of relying strictly on transcript dictation.
