"""
Clara Answers — FastAPI Processing Backend
Receives Retell AI webhook events and transcript submissions,
runs the full pipeline: extract → validate → build agent spec → version → diff.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional
import json
import os
import uuid
import logging
from datetime import datetime

from schemas import AccountMemo, RetellAgentSpec
from extractor import extract_memo_from_transcript
from agent_builder import build_agent_spec
from differ import generate_diff
from tracker import create_task
from version_manager import save_artifact, load_artifact, version_exists

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Clara Answers Pipeline API",
    description="Processes Retell AI call transcripts into versioned agent configurations.",
    version="1.0.0"
)


# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class TranscriptSubmission(BaseModel):
    """
    Submitted manually (batch mode or internal tooling).
    """
    account_id: Optional[str] = Field(None, description="Existing account ID. Auto-generated if blank.")
    transcript_type: str = Field(..., description="'demo' or 'onboarding'")
    transcript_text: str = Field(..., description="Raw transcript content")
    company_name: Optional[str] = Field(None, description="Company name hint for extraction")


class RetellWebhookPayload(BaseModel):
    """
    Retell AI sends this after a call ends.
    Maps to their standard call_ended webhook schema.
    """
    event: str                                      # "call_ended"
    call_id: str
    agent_id: str
    call_status: str                                # "ended"
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    transcript: Optional[str] = None               # Full call transcript text
    transcript_object: Optional[list] = None        # Structured turn-by-turn
    call_analysis: Optional[dict] = None            # Retell's built-in analysis
    metadata: Optional[dict] = None                 # Custom fields set on call start
    # Fields populated from metadata by convention:
    # metadata.account_id   → existing account to update
    # metadata.call_type    → "demo" | "onboarding"
    # metadata.company_name → human-readable name


# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ─────────────────────────────────────────────
# MANUAL TRANSCRIPT SUBMISSION
# ─────────────────────────────────────────────

@app.post("/transcripts/submit")
async def submit_transcript(payload: TranscriptSubmission, background_tasks: BackgroundTasks):
    """
    Submit a transcript directly (batch processing, internal tooling, testing).
    Triggers full pipeline in background.
    """
    account_id = payload.account_id or f"account_{uuid.uuid4().hex[:8]}"
    logger.info(f"[SUBMIT] account={account_id} type={payload.transcript_type}")

    background_tasks.add_task(
        run_pipeline,
        account_id=account_id,
        transcript_type=payload.transcript_type,
        transcript_text=payload.transcript_text,
        company_name=payload.company_name
    )

    return {
        "status": "accepted",
        "account_id": account_id,
        "transcript_type": payload.transcript_type,
        "message": "Pipeline triggered. Check /accounts/{account_id} for results."
    }


# ─────────────────────────────────────────────
# RETELL AI WEBHOOK
# ─────────────────────────────────────────────

@app.post("/webhooks/retell")
async def retell_webhook(payload: RetellWebhookPayload, background_tasks: BackgroundTasks):
    """
    Retell AI call_ended webhook.
    Configure this URL in Retell dashboard → Agent → Webhook URL.

    Expected metadata keys on the Retell call object:
      - account_id   (optional — omit for new accounts)
      - call_type    ("demo" or "onboarding")
      - company_name (optional hint)
    """
    if payload.event != "call_ended":
        logger.info(f"[WEBHOOK] Ignoring event: {payload.event}")
        return {"status": "ignored", "reason": "not call_ended"}

    if not payload.transcript:
        logger.warning(f"[WEBHOOK] call_id={payload.call_id} has no transcript. Skipping.")
        return {"status": "skipped", "reason": "empty transcript"}

    meta = payload.metadata or {}
    call_type = meta.get("call_type", "demo")
    account_id = meta.get("account_id") or f"account_{uuid.uuid4().hex[:8]}"
    company_name = meta.get("company_name")

    logger.info(f"[WEBHOOK] call_id={payload.call_id} account={account_id} type={call_type}")

    background_tasks.add_task(
        run_pipeline,
        account_id=account_id,
        transcript_type=call_type,
        transcript_text=payload.transcript,
        company_name=company_name,
        source_call_id=payload.call_id,
        call_analysis=payload.call_analysis
    )

    return {"status": "accepted", "account_id": account_id, "call_id": payload.call_id}


# ─────────────────────────────────────────────
# RESULTS ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/accounts/{account_id}")
def get_account(account_id: str):
    """Return all available versions for an account."""
    base = f"outputs/accounts/{account_id}"
    if not os.path.exists(base):
        raise HTTPException(status_code=404, detail="Account not found")

    versions = {}
    for v in ["v1", "v2"]:
        vpath = os.path.join(base, v)
        if os.path.exists(vpath):
            versions[v] = {
                "memo": os.path.exists(os.path.join(vpath, "memo.json")),
                "agent_spec": os.path.exists(os.path.join(vpath, "agent_spec.json"))
            }

    changelog_path = f"changelogs/{account_id}_diff.md"
    has_diff = os.path.exists(changelog_path)

    return {"account_id": account_id, "versions": versions, "changelog_available": has_diff}


@app.get("/accounts/{account_id}/{version}/memo")
def get_memo(account_id: str, version: str):
    """Return the AccountMemo for a specific version."""
    data = load_artifact(account_id, version, "memo.json")
    if not data:
        raise HTTPException(status_code=404, detail=f"No memo for {account_id}/{version}")
    return data


@app.get("/accounts/{account_id}/{version}/agent_spec")
def get_agent_spec(account_id: str, version: str):
    """Return the Retell Agent Spec for a specific version."""
    data = load_artifact(account_id, version, "agent_spec.json")
    if not data:
        raise HTTPException(status_code=404, detail=f"No agent_spec for {account_id}/{version}")
    return data


@app.get("/accounts/{account_id}/changelog")
def get_changelog(account_id: str):
    """Return the markdown diff between v1 and v2."""
    path = f"changelogs/{account_id}_diff.md"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="No changelog yet")
    with open(path) as f:
        return {"account_id": account_id, "changelog": f.read()}


@app.get("/accounts")
def list_accounts():
    """List all known accounts."""
    base = "outputs/accounts"
    if not os.path.exists(base):
        return {"accounts": []}
    return {"accounts": os.listdir(base)}


# ─────────────────────────────────────────────
# CORE PIPELINE
# ─────────────────────────────────────────────

def run_pipeline(
    account_id: str,
    transcript_type: str,
    transcript_text: str,
    company_name: Optional[str] = None,
    source_call_id: Optional[str] = None,
    call_analysis: Optional[dict] = None
):
    """
    Full pipeline execution.
    demo transcript  → generates v1 memo + agent_spec
    onboarding transcript → loads v1, patches to v2, generates diff
    """
    logger.info(f"[PIPELINE START] account={account_id} type={transcript_type}")

    try:
        # ── STEP 1: Extract structured memo from transcript ──
        memo: AccountMemo = extract_memo_from_transcript(
            transcript_text=transcript_text,
            transcript_type=transcript_type,
            account_id=account_id,
            company_name_hint=company_name
        )

        if transcript_type == "demo":
            version = "v1"

            # Guard: don't re-process if already exists
            if version_exists(account_id, version):
                logger.warning(f"[PIPELINE] {account_id}/{version} already exists. Skipping.")
                return

            # ── STEP 2: Build agent spec ──
            spec: RetellAgentSpec = build_agent_spec(memo)

            # ── STEP 3: Save artifacts ──
            save_artifact(account_id, version, "memo.json", memo.model_dump())
            save_artifact(account_id, version, "agent_spec.json", spec.model_dump())

            # ── STEP 4: Create tracker task ──
            create_task(account_id, "demo_processed", {
                "version": version,
                "company": memo.company_name,
                "unknowns": len(memo.questions_or_unknowns)
            })

            logger.info(f"[PIPELINE DONE] {account_id}/v1 saved.")

        elif transcript_type == "onboarding":
            version = "v2"

            if version_exists(account_id, version):
                logger.warning(f"[PIPELINE] {account_id}/{version} already exists. Skipping.")
                return

            # Load existing v1 memo
            v1_data = load_artifact(account_id, "v1", "memo.json")
            if not v1_data:
                logger.error(f"[PIPELINE] No v1 memo for {account_id}. Cannot process onboarding.")
                create_task(account_id, "onboarding_failed", {"reason": "missing_v1"})
                return

            v1_memo = AccountMemo(**v1_data)

            # ── STEP 2: Merge onboarding updates onto v1 ──
            merged_memo = merge_memos(v1_memo, memo)

            # ── STEP 3: Build updated agent spec ──
            spec: RetellAgentSpec = build_agent_spec(merged_memo)
            spec.version = "v2"

            # ── STEP 4: Save artifacts ──
            save_artifact(account_id, version, "memo.json", merged_memo.model_dump())
            save_artifact(account_id, version, "agent_spec.json", spec.model_dump())

            # ── STEP 5: Generate changelog ──
            generate_diff(account_id, v1_memo.model_dump(), merged_memo.model_dump())

            # ── STEP 6: Task ──
            create_task(account_id, "onboarding_processed", {
                "version": version,
                "company": merged_memo.company_name,
            })

            logger.info(f"[PIPELINE DONE] {account_id}/v2 saved + diff generated.")

        else:
            logger.error(f"[PIPELINE] Unknown transcript_type: {transcript_type}")

    except Exception as e:
        logger.error(f"[PIPELINE ERROR] account={account_id} error={str(e)}", exc_info=True)
        create_task(account_id, "pipeline_error", {"error": str(e), "type": transcript_type})


def merge_memos(v1: AccountMemo, onboarding: AccountMemo) -> AccountMemo:
    """
    Applies onboarding memo fields onto v1.
    Only overwrites fields that have actual values in the onboarding memo.
    Preserves v1 data where onboarding provides nothing.
    Merges questions_or_unknowns lists.
    """
    v1_dict = v1.model_dump()
    ob_dict = onboarding.model_dump()

    merged = dict(v1_dict)
    skip_fields = {"account_id", "questions_or_unknowns"}

    for key, value in ob_dict.items():
        if key in skip_fields:
            continue
        if value is not None and value != "" and value != [] and value != {}:
            merged[key] = value

    # Merge unknowns: remove resolved ones if onboarding now answers them
    all_unknowns = list(set(v1_dict.get("questions_or_unknowns", []) + ob_dict.get("questions_or_unknowns", [])))
    merged["questions_or_unknowns"] = all_unknowns

    return AccountMemo(**merged)