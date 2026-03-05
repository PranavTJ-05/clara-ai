"""
agent_builder.py — Transforms AccountMemo into a Retell Agent Spec.
Generates the system prompt and call flow configuration.
"""

from datetime import datetime, timezone
from typing import Optional
from schemas import AccountMemo, RetellAgentSpec, TransferProtocol


BUSINESS_HOURS_FLOW = """
## Business Hours Call Flow

1. **Greeting**
   - "Thank you for calling {company_name}. This is Clara, your virtual assistant. How can I help you today?"

2. **Identify Purpose**
   - Listen for emergency keywords: {emergency_keywords}
   - If emergency detected → jump to Emergency Protocol immediately

3. **Collect Caller Info**
   - "May I get your name please?"
   - "And the best phone number to reach you?"

4. **Determine Routing**
   - Emergency → transfer to dispatch immediately
   - Service request / scheduling → collect details, route to office
   - General inquiry → answer if possible, offer callback

5. **Transfer Attempt**
   - Announce: "Let me connect you with our team."
   - Attempt transfer. Timeout: {transfer_timeout}s
   - On timeout: "I wasn't able to reach them directly. I've noted your information and someone will call you back shortly."

6. **Confirm & Close**
   - Confirm next steps with caller
   - "Is there anything else I can help you with?"
   - "Thank you for calling {company_name}. Have a great day!"
"""

AFTER_HOURS_FLOW = """
## After Hours Call Flow

1. **Greeting**
   - "Thank you for calling {company_name}. You've reached us outside of our normal business hours. I'm Clara, your virtual assistant."

2. **Identify Purpose**
   - "Are you calling about an emergency situation, or can this wait until the next business day?"
   - Listen for emergency keywords: {emergency_keywords}

3. **If EMERGENCY:**
   - "I understand — let me get some information so we can help you right away."
   - Collect: Full name → callback number → service address → describe the situation briefly
   - "I'm connecting you to our on-call team now."
   - Attempt transfer. Timeout: {transfer_timeout}s
   - On failure: "I wasn't able to reach them directly. Your information has been sent to our on-call team and they will call you back as quickly as possible. Please stay safe."

4. **If NON-EMERGENCY:**
   - "I'd be happy to help. Our office is open {business_hours_summary}."
   - "Can I take down your name and number so our team can follow up with you?"
   - Collect: name, phone, brief description of need
   - "We'll reach out during business hours. Is there anything else?"

5. **Close**
   - Thank the caller
   - Reassure follow-up
"""


def build_agent_spec(memo: AccountMemo) -> RetellAgentSpec:
    """Build a complete Retell Agent Spec from a validated AccountMemo."""

    now = datetime.now(timezone.utc).isoformat()
    company = memo.company_name or "our company"

    # Build emergency keywords string
    keywords = ", ".join(memo.emergency_keywords) if memo.emergency_keywords else "leak, fire, alarm, flooding, hazard, emergency"

    # Transfer info
    primary_transfer = None
    timeout = 30
    fallback_action = "callback_promise"

    if memo.emergency_routing_rules:
        rule = memo.emergency_routing_rules[0]
        primary_transfer = rule.transfer_to
        timeout = rule.transfer_timeout_seconds or 30
        fallback_action = rule.fallback_action or "callback_promise"

    transfer_protocol = TransferProtocol(
        primary_number=primary_transfer,
        timeout_seconds=timeout,
        fallback_action=fallback_action,
        announce_transfer=True,
        transfer_message=f"Please hold while I connect you to the {company} team."
    )

    # Business hours summary
    bh = memo.business_hours
    if bh:
        days = []
        day_map = {
            "monday": bh.monday, "tuesday": bh.tuesday,
            "wednesday": bh.wednesday, "thursday": bh.thursday,
            "friday": bh.friday, "saturday": bh.saturday, "sunday": bh.sunday
        }
        for day, hours in day_map.items():
            if hours:
                days.append(f"{day.capitalize()}: {hours}")
        bh_summary = ", ".join(days) if days else "Monday–Friday standard business hours"
        if bh.timezone:
            bh_summary += f" ({bh.timezone})"
    else:
        bh_summary = "Monday–Friday, business hours (timezone not confirmed)"

    # Build system prompt
    bh_flow = BUSINESS_HOURS_FLOW.format(
        company_name=company,
        emergency_keywords=keywords,
        transfer_timeout=timeout
    )
    ah_flow = AFTER_HOURS_FLOW.format(
        company_name=company,
        emergency_keywords=keywords,
        transfer_timeout=timeout,
        business_hours_summary=bh_summary
    )

    system_prompt = f"""# Clara Voice Agent — {company}

You are Clara, a professional and calm AI voice agent for {company}.

## Company Context
- Company: {company}
- Services: {', '.join(memo.services_supported) if memo.services_supported else 'Not specified'}
- Emergency Definition: {memo.emergency_definition or 'Active safety hazards, system failures requiring immediate response'}
- Emergency Keywords: {keywords}

## Business Hours
{bh_summary}

{bh_flow}

{ah_flow}

## General Rules
- Always be calm, professional, and empathetic
- Never promise specific technician arrival times unless confirmed
- Never diagnose problems — collect information and route appropriately
- If unsure, say "Let me make sure the right person reaches you" and collect callback info
- Always confirm caller name and callback number before ending any call
"""

    spec = RetellAgentSpec(
        agent_name=f"Clara — {company}",
        account_id=memo.account_id,
        voice_style="professional_warm",
        language="en-US",
        system_prompt=system_prompt,
        key_variables={
            "company_name": company,
            "business_hours_summary": bh_summary,
            "emergency_keywords": memo.emergency_keywords,
            "emergency_definition": memo.emergency_definition,
            "transfer_number": primary_transfer,
            "transfer_timeout": timeout,
        },
        call_transfer_protocol=transfer_protocol,
        fallback_protocol={
            "action": fallback_action,
            "message": "Your information has been recorded. Someone will reach you as soon as possible.",
            "log_to_crm": True
        },
        business_hours_behavior=memo.office_hours_flow_summary or "Route to staff during business hours",
        after_hours_behavior=memo.after_hours_flow_summary or "Triage emergency vs non-emergency after hours",
        emergency_detection_phrases=memo.emergency_keywords,
        version="v1",
        generated_at=now
    )

    return spec