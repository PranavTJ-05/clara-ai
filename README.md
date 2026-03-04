# Clara Answers - Zero-Cost Automation Pipeline

This repository contains a full, zero-cost, end-to-end automation pipeline to process demo and onboarding call transcripts to dynamically configure an AI voice agent built on Retell AI.

## Architecture & Data Flow

This project uses a hybrid architecture designed to securely manage API keys, utilize free-tier tools exclusively, and provide a repeatable, idempotent data pipeline.

1. **Ingestion (n8n & Docker):** Transcripts are dropped into the `data/inbox/` folder. A locally hosted instance of n8n monitors this folder.
2. **Extraction Engine (Python & Groq):** When a file appears, n8n triggers the Python CLI `scripts/process.py`.
3. **LLM Parsing (Groq API):** The script sends the transcript to the free-tier Groq API using the latest `llama-3.3-70b-versatile` model to extract structured metadata (AccountMemo).
4. **Agent Spec Generation:** Based on the extracted metadata, the script generates a strict system prompt (`agent_spec.json`) enforcing conversation hygiene (v1 for Demo, v2 for Onboarding).
5. **Versioning & Diffing:** Onboarding calls merge updates over the Demo configurations and generate a markdown changelog in `/changelogs/`.
6. **Task Tracking:** The pipeline logs automated task tickets locally to `tasks.json` instead of paying for external APIs.
7. **Retell AI WebSocket Backend (FastAPI & Railway):** A lightweight FastAPI server is deployed to Railway on a free tier. Retell connects to this via WebSocket. The backend reads the generated `agent_spec.json` and creates a seamless, low-latency conversational agent connected to Groq.
8. **Post-Call Data Extraction (ngrok & n8n):** When the call finishes, Retell extracts conversational metadata (Name, Phone, Emergency status) and sends it over a webhook to a secure ngrok tunnel routing back into your local n8n instance.
9. **Analytics (Google Sheets):** n8n parses the webhook and logs the organized caller data into a Google Sheet.

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
