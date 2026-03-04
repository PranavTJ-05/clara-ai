Project Context

This repository contains a zero-cost automation pipeline for Clara Answers.

The system converts client demo calls and onboarding calls into structured operational configurations for an AI voice agent built on Retell.

The pipeline simulates the real Clara onboarding workflow:

Conversation (messy human data)
      ↓
Structured Operational Logic
      ↓
Account Memo JSON
      ↓
Retell Agent Configuration
      ↓
Versioned Agent Spec (v1 → v2)

The goal is to transform unstructured transcripts into deterministic system configuration safely, repeatably, and without hallucination.

Business Context

Clara Answers is an AI voice agent used by service trade businesses.

Typical customers include:

Fire protection contractors

Sprinkler system companies

Alarm monitoring services

HVAC companies

Electrical maintenance providers

These businesses receive inbound calls that fall into categories:

Emergency Calls

Examples:

Active sprinkler leak

Fire alarm triggered

Flooding or electrical hazard

Safety-critical system failure

Emergency calls must:

be recognized quickly

collect key details immediately

transfer to dispatch or on-call staff

Non-Emergency Calls

Examples:

Inspection scheduling

General service requests

Maintenance questions

Quotes or information

These calls may:

be routed during business hours

be logged for follow-up after hours

Client Lifecycle
Stage 1 — Demo Call

Purpose:

Exploratory discussion of pain points.

Information gathered here is incomplete and uncertain.

Typical characteristics:

Business hours unclear

Routing rules incomplete

Emergency definitions vague

Integrations unknown

The pipeline must generate:

AccountMemo v1
RetellAgentSpec v1

Important rules:

Never hallucinate missing data

Missing information goes into questions_or_unknowns

Only extract explicit statements

Stage 2 — Onboarding Call

Purpose:

Operational configuration.

This call provides finalized details such as:

business hours

time zone

emergency definitions

transfer timeouts

routing hierarchy

system constraints

The pipeline must update the existing configuration:

AccountMemo v1 → v2
RetellAgentSpec v1 → v2

Requirements:

preserve history

apply minimal changes

generate a changelog

never overwrite unrelated fields

Technical Objective

Build a fully automated pipeline that:

Processes 5 demo transcripts

Processes 5 onboarding transcripts

Generates versioned configuration artifacts

Produces a clear diff between versions

All operations must use zero paid services.

System Architecture

The system follows a hybrid architecture:

n8n Orchestrator
      ↓
Python CLI Processing Engine
      ↓
LLM Extraction + Schema Validation
      ↓
Agent Spec Generator
      ↓
Version Manager
      ↓
Storage + Changelog
Core Components
n8n Orchestrator

Location

/workflows/clara_pipeline.json

Responsibilities:

monitor transcript input directory

trigger processing pipeline

log execution status

enable batch execution

n8n runs locally using Docker.

Python Processing Engine

Location

/scripts/

This layer performs the core logic.

process.py

Entry point for transcript processing.

Responsibilities:

detect transcript type (demo or onboarding)

assign account_id

trigger extraction

generate artifacts

handle versioning

schemas.py

Contains Pydantic models enforcing strict structure.

Schemas include:

AccountMemo
RetellAgentSpec

Schema validation prevents malformed outputs.

extractor.py

Handles transcript analysis.

Responsibilities:

parse transcript

extract operational data

produce AccountMemo JSON

Uses:

Groq LLM (llama-3.1-8b)
or
Local Ollama

Important constraint:

Extraction must never fabricate unknown fields.

Unknown information must be placed in:

questions_or_unknowns
agent_builder.py

Transforms AccountMemo into a Retell Agent specification.

Generates:

agent_spec.json

The spec includes:

system prompt

routing logic

business hours behavior

after-hours behavior

transfer protocol

fallback protocol

differ.py

Generates version differences.

Responsibilities:

compare v1 and v2 memo

compare v1 and v2 agent spec

produce human-readable changelog

Output format:

Markdown diff

Example:

business_hours updated
emergency_definition expanded
transfer_timeout changed
tracker.py

Simulates integration with a task tracker.

Instead of external APIs, the system writes tasks to:

tasks.json

This satisfies the automation requirement without paid APIs.

Storage Layout

Artifacts are stored using a deterministic directory structure.

outputs/
  accounts/
    <account_id>/
      v1/
        memo.json
        agent_spec.json
      v2/
        memo.json
        agent_spec.json

Changelogs stored separately:

changelogs/
  <account_id>_diff.md
Account Memo Schema

Each account produces a structured memo.

Fields:

account_id
company_name
business_hours
office_address
services_supported
emergency_definition
emergency_routing_rules
non_emergency_routing_rules
call_transfer_rules
integration_constraints
after_hours_flow_summary
office_hours_flow_summary
questions_or_unknowns
notes

Rules:

fields must only contain verified data

missing fields remain empty

uncertainty is recorded explicitly

Retell Agent Spec

The agent specification defines the behavior of the voice agent.

Key fields:

agent_name
voice_style
system_prompt
key_variables
call_transfer_protocol
fallback_protocol
version
Prompt Discipline Rules

The system prompt must follow strict conversation structure.

Business Hours Flow

Greeting

Ask purpose of call

Collect caller name

Collect phone number

Determine routing

Attempt transfer

Handle transfer failure

Confirm next steps

Ask if caller needs anything else

Close call

After Hours Flow

Greeting

Ask purpose

Determine if emergency

If emergency:

collect name

collect phone

collect address immediately

Attempt transfer

If transfer fails:

apologize

assure quick follow-up

If non-emergency:

collect request details

promise follow-up during business hours

Ask if anything else

Close call

Versioning Logic
Demo Call

Generates:

v1
Onboarding Call

Generates:

v2

Process:

Load v1 memo
Extract onboarding updates
Apply patch
Generate v2 memo
Generate v2 agent spec
Produce changelog

The pipeline must:

preserve v1 artifacts

avoid overwriting fields unnecessarily

apply only confirmed updates

Zero-Cost Constraint

No paid APIs are allowed.

Acceptable options:

LLM

Groq free tier

Ollama local models

Automation

n8n self-hosted

Storage

local filesystem

GitHub repo

Transcription

If needed:

Whisper local

If transcripts exist:

skip transcription step

Input Data

Dataset includes:

5 demo transcripts
5 onboarding transcripts

Input location:

data/inbox/

Each transcript triggers the pipeline.

Pipeline Behavior

The workflow must be:

idempotent

batch capable

reproducible

logged

failure tolerant

Running the pipeline twice must not create duplicate versions.

Verification Plan
Step 1

Generate mock transcripts

python data/mock_generator.py

Creates:

5 demo transcripts
5 onboarding transcripts
Step 2

Process demo transcript

python scripts/process.py --file data/demo_1.txt

Expected output:

outputs/accounts/account_1/v1/
Step 3

Process onboarding transcript

python scripts/process.py --file data/onboarding_1.txt

Expected output:

outputs/accounts/account_1/v2/
changelogs/account_1_diff.md
Step 4

Batch test

Run pipeline for all transcripts.

Verify:

versioning correct

diffs generated

no duplicated artifacts

Guiding Engineering Principles
Deterministic Automation

Outputs must be predictable and reproducible.

No Silent Assumptions

Missing information must be explicit.

Schema First Design

Structured JSON must always conform to schema.

Version Integrity

Historical versions must remain untouched.

Production Thinking

This pipeline should feel like an internal tool used by operations teams, not a prototype script.

Future Improvements (Out of Scope)

If production resources were available:

real Retell API integration

dashboard UI for reviewing configs

visual diff viewer

automatic QA validation

CRM integration

webhook-based ingestion

human review approval loop

Final Mental Model

Think of this system as:

Human conversations
        ↓
Operational logic extraction
        ↓
Structured configuration
        ↓
AI voice agent behavior

This repository implements the automation layer that bridges human conversation and deployable AI agents.
