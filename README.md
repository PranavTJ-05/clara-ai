# Clara Answers - Zero-Cost Automation Pipeline

This repository contains a full, zero-cost, end-to-end automation pipeline to process demo and onboarding call transcripts to dynamically configure an AI voice agent built on Retell AI.

## Architecture & Data Flow

This project uses a hybrid architecture designed to securely manage API keys, utilize free-tier tools exclusively, and provide a repeatable, idempotent data pipeline.

1. **Zero-Cost Orchestrator (n8n & Docker):** A single locally hosted instance of n8n orchestrates two parallel, isolated pipelines simultaneously:
   * **Pipeline 1 (Agent Initialization):** Listens to `data/inbox/`. When a script drops a call transcript, n8n triggers the Python extraction engine.
   * **Pipeline 2 (Post-Call Analysis):** An exposed n8n webhook listens to Retell AI. It captures post-call data, checks for "Emergency" parameters to determine conditional routing routing, and perfectly maps the result into Google Sheets columns.
2. **LLM Extraction Engine (Python & Groq API):** The Python scripts parse transcripts using the free-tier Groq API and the `llama-3.3-70b-versatile` model to extract AccountMemo metadata.
3. **Agent Spec Generation:** Extracted metadata is synthesized into a rigid system prompt (`agent_spec.json`) enforcing business hours and emergency conversation hygiene (v1 for Demo, v2 for Onboarding).
4. **Versioning & Diffing:** Onboarding calls merge new rules over Demo configurations and automatically generate a markdown diff in `/changelogs/`.
5. **Task Tracking:** The pipeline tracks completion by locally writing tasks to `tasks.json`.
6. **Retell AI WebSocket Backend (FastAPI & Railway):** A FastAPI server deployed to Railway free-tier accepts Retell interactions over a continuous WebSocket, retrieves the generated `agent_spec.json`, and seamlessly connects the voice stream to Groq.
7. **Secure Tunneling (ngrok):** The Retell Post-Call Analysis reaches your local n8n Pipeline 2 through a secure ngrok tunnel.

## Setup Instructions

### 1. Run the Docker Infrastructure
We use Docker to run n8n orchestrator locally for zero cost.
```bash
# Start n8n background service
docker compose up -d
```
Access the n8n UI at `http://localhost:5678`.

### 2. Configure Environment Variables
Create a `.env` file in the root directory and add your free Groq API key:
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

### 3. Deploy the Custom LLM Backend (Railway)
Retell AI needs a public WebSocket endpoint to stream voice data. We have prepared a FastAPI backend.
1. Connect this GitHub repository to Railway (free tier).
2. The `Procfile` and root `requirements.txt` are pre-configured to build automatically.
3. In Railway, add the `GROQ_API_KEY` environmental variable.
4. Railway will provide a URL (e.g., `clara-production.up.railway.app`).

### 4. Configure Retell AI
1. Create a free Retell AI account and create a new agent.
2. Select **Custom LLM**.
3. Set the Custom LLM URL to your Railway websocket: `wss://your-railway-url.up.railway.app/retell`
4. In the Retell Agent settings, define the **Post Call Data Extraction** properties you want the AI to pull after the call (e.g., `caller_name`, `purpose`, `is_emergency`).

### 5. Start Ngrok for the n8n Webhook
n8n needs a public URL to receive the post-call data from Retell.
```bash
ngrok http 5678
```
Take the ngrok URL (e.g., `https://a1b2.ngrok-free.app`) and append your n8n webhook path (e.g., `/webhook/post-call-analysis`).
Paste this full URL into the **Webhooks** section of your Retell Dashboard.

### 6. Process the Pipeline Dataset!
To simulate dropping the 10 demo/onboarding files into the pipeline:
```bash
python data/mock_generator.py
```
n8n will automatically detect these files and trigger the extraction pipeline.
Check the `/outputs/` and `/changelogs/` folders to see the v1 (Demo) and v2 (Onboarding) JSON and markdown diff artifacts successfully generated!

## Prompt Strategy
The exact prompt structure used to constrain the LLM inside Retell enforces strict information collection and routing rules. You can find the exact template in `scripts/agent_builder.py`.

It utilizes explicit commands like:
`CRITICAL INSTRUCTION: Your primary goal is to COLLECT INFORMATION. Do NOT prematurely forward or transfer the call without first getting the caller's Name, Phone Number, and the exact details of their issue.`

And implements rigid structural flows:
`=== BUSINESS HOURS FLOW ===` and `=== AFTER HOURS FLOW ===`
to prevent hallucination and assure safe escalation.

## Folder Structure
```text
clara-pipeline/
│
├── scripts/                        # Core Python processing engine
│   ├── api.py                      # FastAPI app — all endpoints
│   ├── schemas.py                  # Pydantic models (AccountMemo, RetellAgentSpec)
│   ├── extractor.py                # LLM transcript extraction (Groq / Ollama)
│   ├── agent_builder.py            # AccountMemo → RetellAgentSpec
│   ├── differ.py                   # v1 vs v2 changelog generator
│   ├── tracker.py                  # Task log → tasks.json
│   ├── process.py                  # CLI entry point
│
├── workflows/
│   └── clara_pipeline.json         # n8n workflow (import into n8n UI)
│
├── data/
│   ├── inbox/                      # Drop transcript .txt files here (batch mode)
│   │   ├── demo_1.txt
│   │   ├── onboarding_1.txt
│   │   └── ...
│   ├── mock_generator.py           # Generated mock transcripts
│
├── outputs/
│   └── accounts/
│       └── <account_id>/
│           ├── v1/
│           │   ├── memo.json       # AccountMemo from demo call
│           │   └── agent_spec.json # RetellAgentSpec v1
│           └── v2/
│               ├── memo.json       # Merged AccountMemo from onboarding
│               └── agent_spec.json # RetellAgentSpec v2
│
├── changelogs/
│   └── <account_id>_diff.md        # Human-readable v1→v2 diff
│
├── tasks.json                      # Pipeline task log (replaces CRM)
│
├── docker-compose.yml              # Runs n8n Orchestrator via Docker
├── Dockerfile.n8n                  # n8n custom dockerfile
└── README.md                       # Project documentation
```

## Quick Start
**1. Set environment variables**
```bash
cp .env.example .env
# Add your GROQ_API_KEY (free at console.groq.com)
```
**2. Start services**
```bash
docker-compose up -d
```
**3. Import n8n workflow**
1. Open http://localhost:5678
2. Import `workflows/clara_pipeline.json`
3. Activate the workflow

**4. Configure Retell webhook**
Using ngrok: `https://your-domain.ngrok-free.app/webhook/post-call-analysis`

**5. Process via CLI (or drop files into data/inbox)**
```bash
# Generate the massive dataset (triggers n8n automatically)
python scripts/mock_generator.py
```
