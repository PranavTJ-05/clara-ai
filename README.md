# Clara Answers – Zero-Cost Automation Pipeline

An end-to-end automation pipeline that converts demo and onboarding call transcripts into dynamically configured Retell AI voice agents — built entirely using free-tier infrastructure.

The system automatically extracts structured business information from call transcripts, generates a voice-agent configuration, updates the configuration based on onboarding calls, and tracks all changes with versioned artifacts and human-readable diffs.

The entire workflow runs using a local orchestration layer, free LLM inference, and lightweight cloud services.

---

# Overview

This project implements a **zero-cost automation workflow** that processes demo and onboarding calls to configure an AI voice agent.

The pipeline performs the following steps:

1. Accepts call transcripts or recordings.
2. Extracts structured metadata using an LLM.
3. Generates a structured Retell AI agent configuration.
4. Updates the configuration when onboarding information changes.
5. Produces versioned artifacts and changelogs.
6. Streams live voice conversations through a custom LLM backend.

The system is designed to be:

* Fully automated
* Deterministic and repeatable
* Version controlled
* Deployable entirely using free infrastructure

---

# Architecture

The system follows a hybrid architecture combining local orchestration, cloud deployment, and secure tunneling.

                ┌───────────────┐
                │   Retell AI   │
                └───────┬───────┘
                        │
                        ▼
                n8n Webhook
                        │
                        ▼
                Input Normalization
                        │
                        ▼
                 FastAPI Engine
                        │
                        ▼
               LLM Extraction (Groq)
                        │
                        ▼
              Agent Spec Generator
                        │
                        ▼
           Versioning + Diff Generator
                        │
                        ▼
              Local Artifact Storage

---

## Data Flow

1. **Transcript Input**

Demo and onboarding transcripts are dropped into a monitored directory or submitted via API.

2. **n8n Orchestration**

A locally hosted n8n instance triggers the processing pipeline.

Two pipelines run simultaneously:

**Pipeline 1 — Agent Initialization**

* Watches `data/inbox/`
* Detects new transcript files
* Triggers the Python extraction engine

**Pipeline 2 — Post-Call Analysis**

* Receives webhook events from Retell AI
* Processes post-call metadata
* Routes emergency calls conditionally
* Maps structured results into Google Sheets

3. **LLM Extraction Engine**

Python scripts parse transcripts using the Groq API and the `llama-3.3-70b-versatile` model.

The system extracts structured metadata called **AccountMemo**.

4. **Agent Specification Generation**

The extracted metadata is transformed into a strict Retell AI agent configuration (`agent_spec.json`).

Two versions are produced:

* **v1** – Demo call configuration
* **v2** – Onboarding call configuration

5. **Versioning and Diff Generation**

When onboarding data modifies an existing configuration:

* New rules override previous rules
* A human-readable markdown diff is generated
* Changes are stored in `/changelogs/`

6. **Task Tracking**

Pipeline tasks are tracked locally in:

```
tasks.json
```

This acts as a lightweight CRM replacement.

7. **Voice Agent Runtime**

A FastAPI backend deployed to Railway handles:

* WebSocket streaming from Retell
* Retrieval of agent specifications
* Connection to Groq inference

8. **Secure Tunnel**

An ngrok tunnel allows Retell to reach the local n8n webhook.

---

# System Components

| Component | Purpose                         |
| --------- | ------------------------------- |
| n8n       | Workflow orchestration          |
| Docker    | Local infrastructure management |
| Python    | Transcript processing engine    |
| Groq API  | LLM inference                   |
| FastAPI   | Voice streaming backend         |
| Railway   | Free deployment for the backend |
| ngrok     | Secure webhook tunneling        |
| Retell AI | Voice agent platform            |

---

# Features

* Zero-cost infrastructure using free tiers
* Fully automated call transcript processing
* Dynamic voice-agent configuration
* Versioned agent specifications
* Human-readable changelog generation
* Emergency call routing logic
* Local task tracking
* Real-time voice streaming integration
* Deterministic LLM prompts to prevent hallucinations

---

# Installation

## Prerequisites

Install the following:

* Docker
* Python 3.10+
* ngrok
* Retell AI account
* Groq API key

---

# Environment Setup

Create a `.env` file in the project root.

```
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

Groq API keys can be obtained from:

```
https://console.groq.com
```

---

# Running the Infrastructure

Start the orchestration layer.

```
docker compose up -d
```

This launches the n8n orchestrator.

Open the n8n dashboard:

```
http://localhost:5678
```

---

# Import the n8n Workflow

1. Open the n8n UI.
2. Select **Import Workflow**.
3. Import:

```
workflows/clara_pipeline.json
```

4. Activate the workflow.

---

# Deploy the Custom LLM Backend

Retell requires a public WebSocket endpoint to stream voice conversations.

The project includes a FastAPI backend designed for this purpose.

### Deployment Steps

1. Connect this repository to **Railway**.
2. Railway automatically builds using:

```
Procfile
requirements.txt
```

3. Add the environment variable:

```
GROQ_API_KEY
```

4. Railway will generate a public URL:

```
https://your-app.up.railway.app
```

---

# Configure Retell AI

Create a new Retell AI agent.

Select **Custom LLM**.

Set the WebSocket URL:

```
wss://your-railway-url.up.railway.app/retell
```

Define the following **Post Call Data Extraction** properties:

* caller_name
* purpose
* is_emergency

---

# Configure Webhooks with ngrok

Retell must send post-call data back to the n8n workflow.

Run ngrok:

```
ngrok http 5678
```

Example public URL:

```
https://abcd.ngrok-free.app
```

Append the webhook path:

```
https://abcd.ngrok-free.app/webhook/post-call-analysis
```

Add this URL to the **Retell Webhooks Dashboard**.

---

# Running the Pipeline

To simulate incoming transcripts:

```
python data/mock_generator.py
```

The script generates multiple transcripts and drops them into:

```
data/inbox/
```

n8n automatically detects the files and triggers the pipeline.

Generated artifacts appear in:

```
outputs/
changelogs/
```

---

# Output Artifacts

Each account produces two configuration versions.

### Demo Call (v1)

```
outputs/accounts/<account_id>/v1/
```

Contains:

* memo.json
* agent_spec.json

### Onboarding Call (v2)

```
outputs/accounts/<account_id>/v2/
```

Contains:

* memo.json
* agent_spec.json

### Configuration Changes

All modifications between versions are stored in:

```
changelogs/<account_id>_diff.md
```

---

# Prompt Strategy

The system uses structured prompts to constrain LLM behavior.

The agent enforces strict information collection before escalation.

Example instruction:

```
CRITICAL INSTRUCTION:
Your primary goal is to collect information.

Do not transfer or escalate the call until you obtain:
- Caller Name
- Phone Number
- Detailed description of the issue
```

Conversation flows are explicitly defined:

```
=== BUSINESS HOURS FLOW ===
=== AFTER HOURS FLOW ===
```

These structural prompts prevent hallucinations and ensure consistent behavior.

Prompt templates are defined in:

```
scripts/agent_builder.py
```

---

# API Endpoints

| Method | Endpoint                              | Purpose                           |
| ------ | ------------------------------------- | --------------------------------- |
| POST   | `/transcripts/submit`                 | Submit a transcript manually      |
| POST   | `/webhooks/retell`                    | Receive Retell call_ended webhook |
| GET    | `/accounts`                           | List all accounts                 |
| GET    | `/accounts/{id}`                      | View account version status       |
| GET    | `/accounts/{id}/{version}/memo`       | Retrieve AccountMemo              |
| GET    | `/accounts/{id}/{version}/agent_spec` | Retrieve agent configuration      |
| GET    | `/accounts/{id}/changelog`            | Retrieve configuration diff       |
| GET    | `/health`                             | Health check                      |

---

# Project Structure

```
clara-pipeline/

scripts/
├── api.py
├── schemas.py
├── extractor.py
├── agent_builder.py
├── differ.py
├── tracker.py
├── process.py

workflows/
└── clara_pipeline.json

data/
├── inbox/
│   ├── demo_1.txt
│   ├── onboarding_1.txt
│   └── ...
├── mock_generator.py

outputs/
└── accounts/
    └── <account_id>/
        ├── v1/
        │   ├── memo.json
        │   └── agent_spec.json
        └── v2/
            ├── memo.json
            └── agent_spec.json

changelogs/
└── <account_id>_diff.md

tasks.json

docker-compose.yml
Dockerfile.n8n
README.md
```

---

# LLM Backend Options

| Backend | Setup                                              | Notes                       |
| ------- | -------------------------------------------------- | --------------------------- |
| Groq    | Add `GROQ_API_KEY` in `.env`                       | Recommended free inference  |
| Ollama  | `docker exec clara-ollama ollama pull llama3.1:8b` | Local inference, no API key |

---

# Quick Start

1. Copy environment file

```
cp .env.example .env
```

2. Add your Groq API key

```
GROQ_API_KEY=your_key
```

3. Start infrastructure

```
docker compose up -d
```

4. Import n8n workflow

```
workflows/clara_pipeline.json
```

5. Start ngrok

```
ngrok http 5678
```

6. Generate dataset

```
python scripts/mock_generator.py
```

The pipeline will automatically process the transcripts and produce agent configurations.

---

# License

This project is intended for educational and demonstration purposes.
