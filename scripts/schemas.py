"""
schemas.py — Pydantic models for Clara pipeline.
All fields are Optional to prevent hallucination.
Missing data stays None — never fabricated.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class BusinessHours(BaseModel):
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None
    timezone: Optional[str] = None
    notes: Optional[str] = None


class RoutingRule(BaseModel):
    condition: Optional[str] = None          # "after_hours", "business_hours", "emergency"
    action: Optional[str] = None             # "transfer", "voicemail", "log_and_callback"
    transfer_to: Optional[str] = None        # phone number or label
    transfer_timeout_seconds: Optional[int] = None
    fallback_action: Optional[str] = None


class AccountMemo(BaseModel):
    account_id: str
    company_name: Optional[str] = None
    business_hours: Optional[BusinessHours] = None
    office_address: Optional[str] = None
    services_supported: Optional[List[str]] = Field(default_factory=list)

    emergency_definition: Optional[str] = None
    emergency_keywords: Optional[List[str]] = Field(default_factory=list)
    emergency_routing_rules: Optional[List[RoutingRule]] = Field(default_factory=list)

    non_emergency_routing_rules: Optional[List[RoutingRule]] = Field(default_factory=list)
    call_transfer_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)

    integration_constraints: Optional[List[str]] = Field(default_factory=list)
    after_hours_flow_summary: Optional[str] = None
    office_hours_flow_summary: Optional[str] = None

    questions_or_unknowns: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    source_transcript_type: Optional[str] = None  # "demo" | "onboarding"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TransferProtocol(BaseModel):
    primary_number: Optional[str] = None
    timeout_seconds: Optional[int] = 30
    fallback_number: Optional[str] = None
    fallback_action: Optional[str] = None   # "voicemail" | "callback_promise" | "sms"
    announce_transfer: Optional[bool] = True
    transfer_message: Optional[str] = None


class RetellAgentSpec(BaseModel):
    agent_name: Optional[str] = None
    account_id: str
    voice_style: Optional[str] = "professional_warm"
    language: Optional[str] = "en-US"

    system_prompt: Optional[str] = None

    key_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # e.g. company_name, business_hours_summary, emergency_keywords

    call_transfer_protocol: Optional[TransferProtocol] = None
    fallback_protocol: Optional[Dict[str, Any]] = Field(default_factory=dict)

    business_hours_behavior: Optional[str] = None  # prose description
    after_hours_behavior: Optional[str] = None

    emergency_detection_phrases: Optional[List[str]] = Field(default_factory=list)
    non_emergency_flow: Optional[str] = None

    version: str = "v1"
    generated_at: Optional[str] = None