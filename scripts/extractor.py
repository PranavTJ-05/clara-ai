"""
extractor.py — LLM-powered transcript extraction.
Produces a validated AccountMemo from raw transcript text.
Never fabricates. All unknowns go to questions_or_unknowns.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from schemas import AccountMemo, BusinessHours, RoutingRule

logger = logging.getLogger(__name__)

# ── LLM client setup ──
# Priority: Groq (free tier) → Ollama local
try:
    from groq import Groq
    _groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
    LLM_BACKEND = "groq"
except ImportError:
    _groq_client = None
    LLM_BACKEND = "ollama"

GROQ_MODEL = "llama-3.1-8b-instant"
OLLAMA_MODEL = "llama3.1:8b"
OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


EXTRACTION_SYSTEM_PROMPT = """
You are an expert operations analyst for Clara Answers, an AI voice agent company.
Your job is to extract structured operational configuration from raw call transcripts.

CRITICAL RULES:
1. NEVER invent or guess information that is not explicitly stated.
2. If a field is unclear or not mentioned, leave it null or empty.
3. Record ALL missing or ambiguous information in questions_or_unknowns as a list of strings.
4. Only extract what is clearly and explicitly stated by the client.
5. Return ONLY valid JSON. No preamble, no markdown fences, no explanation.

Extract this JSON schema from the transcript:
{
  "company_name": string or null,
  "business_hours": {
    "monday": "HH:MM-HH:MM" or null,
    "tuesday": "HH:MM-HH:MM" or null,
    "wednesday": "HH:MM-HH:MM" or null,
    "thursday": "HH:MM-HH:MM" or null,
    "friday": "HH:MM-HH:MM" or null,
    "saturday": "HH:MM-HH:MM" or null,
    "sunday": "HH:MM-HH:MM" or null,
    "timezone": string or null,
    "notes": string or null
  },
  "office_address": string or null,
  "services_supported": [list of strings],
  "emergency_definition": string or null,
  "emergency_keywords": [list of trigger words/phrases],
  "emergency_routing_rules": [
    {
      "condition": string,
      "action": "transfer" or "voicemail" or "log_and_callback",
      "transfer_to": phone number or label or null,
      "transfer_timeout_seconds": integer or null,
      "fallback_action": string or null
    }
  ],
  "non_emergency_routing_rules": [...same structure...],
  "call_transfer_rules": {},
  "integration_constraints": [list of strings],
  "after_hours_flow_summary": string or null,
  "office_hours_flow_summary": string or null,
  "questions_or_unknowns": [list of strings describing missing/unclear info],
  "notes": string or null
}
"""


def extract_memo_from_transcript(
    transcript_text: str,
    transcript_type: str,
    account_id: str,
    company_name_hint: Optional[str] = None
) -> AccountMemo:
    """
    Call LLM to extract structured fields from transcript.
    Falls back gracefully if LLM is unavailable.
    """
    user_prompt = f"""
Transcript Type: {transcript_type.upper()}
{f'Company Name Hint: {company_name_hint}' if company_name_hint else ''}

--- TRANSCRIPT START ---
{transcript_text}
--- TRANSCRIPT END ---

Extract the operational configuration. Return only JSON.
"""

    raw_json = _call_llm(user_prompt)
    extracted = _safe_parse_json(raw_json, account_id)

    # Build validated AccountMemo
    now = datetime.now(timezone.utc).isoformat()

    bh_data = extracted.get("business_hours") or {}
    business_hours = BusinessHours(**bh_data) if bh_data else None

    emergency_rules = [
        RoutingRule(**r) for r in (extracted.get("emergency_routing_rules") or [])
        if isinstance(r, dict)
    ]
    non_emergency_rules = [
        RoutingRule(**r) for r in (extracted.get("non_emergency_routing_rules") or [])
        if isinstance(r, dict)
    ]

    memo = AccountMemo(
        account_id=account_id,
        company_name=extracted.get("company_name") or company_name_hint,
        business_hours=business_hours,
        office_address=extracted.get("office_address"),
        services_supported=extracted.get("services_supported") or [],
        emergency_definition=extracted.get("emergency_definition"),
        emergency_keywords=extracted.get("emergency_keywords") or [],
        emergency_routing_rules=emergency_rules,
        non_emergency_routing_rules=non_emergency_rules,
        call_transfer_rules=extracted.get("call_transfer_rules") or {},
        integration_constraints=extracted.get("integration_constraints") or [],
        after_hours_flow_summary=extracted.get("after_hours_flow_summary"),
        office_hours_flow_summary=extracted.get("office_hours_flow_summary"),
        questions_or_unknowns=extracted.get("questions_or_unknowns") or [],
        notes=extracted.get("notes"),
        source_transcript_type=transcript_type,
        created_at=now,
        updated_at=now,
    )

    logger.info(
        f"[EXTRACTOR] account={account_id} "
        f"unknowns={len(memo.questions_or_unknowns)} "
        f"backend={LLM_BACKEND}"
    )
    return memo


def _call_llm(user_prompt: str) -> str:
    if LLM_BACKEND == "groq" and _groq_client:
        return _call_groq(user_prompt)
    return _call_ollama(user_prompt)


def _call_groq(user_prompt: str) -> str:
    try:
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2048
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[GROQ] Error: {e}")
        return "{}"


def _call_ollama(user_prompt: str) -> str:
    try:
        import requests
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.1}
        }
        resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()["message"]["content"].strip()
    except Exception as e:
        logger.error(f"[OLLAMA] Error: {e}")
        return "{}"


def _safe_parse_json(raw: str, account_id: str) -> dict:
    """Strip markdown fences and parse. Returns empty dict on failure."""
    cleaned = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"[EXTRACTOR] JSON parse failed for {account_id}: {e}")
        return {"questions_or_unknowns": ["LLM extraction failed — manual review required."]}