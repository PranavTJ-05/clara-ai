# Retell AI — Data Collection Setup Guide
## Clara Answers Pipeline Integration

---

## 1. What You Need to Configure in Retell

### 1A. Webhook URL (Required)
In **Retell Dashboard → Agent → Settings → Webhook URL**, set:
```
https://your-domain.com/webhooks/retell
```
Or locally via ngrok:
```
https://<ngrok-id>.ngrok.io/webhooks/retell
```

Retell will POST to this URL on every `call_ended` event.

---

## 2. Metadata Fields to Set on Every Call

When you initiate or configure a Retell call, you must pass these fields in the `metadata` object.
These tell the pipeline how to process the transcript.

### Required Metadata

| Field | Type | Values | Purpose |
|-------|------|---------|---------|
| `call_type` | string | `"demo"` or `"onboarding"` | Determines if pipeline generates v1 or v2 |
| `account_id` | string | e.g. `"account_abc123"` | Links the call to an existing account. **Omit for new accounts** (auto-generated) |
| `company_name` | string | e.g. `"Apex Fire Protection"` | Extraction hint. Helps LLM identify the company if not mentioned clearly in transcript |

### How to Set Metadata via Retell API (Call Creation)
```json
POST https://api.retellai.com/v2/create-phone-call
{
  "agent_id": "your_agent_id",
  "from_number": "+1...",
  "to_number": "+1...",
  "metadata": {
    "call_type": "demo",
    "account_id": null,
    "company_name": "Apex Fire Protection"
  }
}
```

For onboarding calls on an existing account:
```json
"metadata": {
  "call_type": "onboarding",
  "account_id": "account_abc123",
  "company_name": "Apex Fire Protection"
}
```

---

## 3. What the Pipeline Extracts from the Transcript

The LLM extraction layer reads the raw `transcript` field Retell sends and pulls:

### 3A. Business Configuration

| Data Point | Example | Required For |
|-----------|---------|-------------|
| Company name | "Apex Fire Protection" | Both |
| Business hours (per day) | "Mon–Fri 8am–5pm" | Both |
| Timezone | "Eastern Time" | Both |
| Office address | "123 Main St, Atlanta GA" | Onboarding |
| Services offered | "sprinkler, alarm, HVAC" | Both |

### 3B. Emergency Protocol

| Data Point | Example | Required For |
|-----------|---------|-------------|
| Emergency definition | "active leak, triggered alarm, flooding" | Both |
| Emergency keywords | ["leak", "fire", "flooding", "alarm"] | Both |
| On-call / dispatch number | "+14045550100" | Onboarding |
| Transfer timeout | 30 seconds | Onboarding |
| Fallback if no answer | "voicemail", "callback_promise" | Onboarding |

### 3C. Routing Rules

| Data Point | Example | Required For |
|-----------|---------|-------------|
| After-hours handling | "transfer to on-call then voicemail" | Onboarding |
| Business hours routing | "transfer to front desk" | Onboarding |
| Non-emergency after hours | "log for callback next day" | Onboarding |
| Secondary contact | "+14045550200" | Onboarding |

### 3D. Integrations & Constraints

| Data Point | Example | Required For |
|-----------|---------|-------------|
| CRM or dispatch tool | "ServiceTitan", "None currently" | Onboarding |
| Do-not-call rules | "Don't transfer to personal cells" | Onboarding |
| Special instructions | "Spanish-speaking callers — transfer to Maria" | Onboarding |

---

## 4. Retell Webhook Payload — What We Receive

When a call ends, Retell sends this JSON to your webhook:

```json
{
  "event": "call_ended",
  "call_id": "call_abc123",
  "agent_id": "agent_xyz",
  "call_status": "ended",
  "start_timestamp": 1710000000000,
  "end_timestamp": 1710000300000,
  "transcript": "Agent: Thank you for calling Apex Fire Protection...\nUser: Hi, I'm calling about...",
  "transcript_object": [
    {
      "role": "agent",
      "content": "Thank you for calling Apex Fire Protection. How can I help?",
      "words": [...]
    },
    {
      "role": "user",
      "content": "Hi, I wanted to ask about your inspection scheduling...",
      "words": [...]
    }
  ],
  "call_analysis": {
    "call_summary": "Caller inquired about annual inspection scheduling...",
    "user_sentiment": "Positive",
    "agent_sentiment": "Positive",
    "call_successful": true,
    "custom_analysis_data": {}
  },
  "metadata": {
    "call_type": "demo",
    "account_id": null,
    "company_name": "Apex Fire Protection"
  }
}
```

### Key Fields Our Pipeline Uses

| Field | Used For |
|-------|---------|
| `transcript` | LLM extraction input |
| `metadata.call_type` | Routes to v1 or v2 pipeline |
| `metadata.account_id` | Account lookup or creation |
| `metadata.company_name` | Extraction hint |
| `call_analysis.call_summary` | Stored as notes field |
| `call_id` | Logged for traceability |

---

## 5. Retell Agent Prompt Variables (What to Inject)

When the pipeline produces a `RetellAgentSpec`, these variables should be injected into your Retell agent's system prompt using Retell's **dynamic variables** feature:

```
{{company_name}}          → "Apex Fire Protection"
{{business_hours_summary}} → "Mon–Fri 8am–5pm Eastern"
{{emergency_keywords}}    → "leak, fire, flooding, alarm"
{{emergency_definition}}  → "Any active safety-critical system failure"
{{transfer_number}}       → "+14045550100"
{{transfer_timeout}}      → 30
```

In your Retell agent system prompt, reference them like:
```
You are Clara, an AI agent for {{company_name}}.
Business hours: {{business_hours_summary}}
Emergency keywords: {{emergency_keywords}}
```

Set these in **Retell Dashboard → Agent → Dynamic Variables**.

---

## 6. Post-Call Data Collection Checklist

Use this checklist to verify each account has all required data before marking configuration complete:

### After Demo Call (v1)
- [ ] Company name extracted
- [ ] At least one service type identified
- [ ] Emergency concept mentioned (even if vague)
- [ ] v1 memo saved at `outputs/accounts/{account_id}/v1/memo.json`
- [ ] `questions_or_unknowns` list reviewed — schedule follow-up

### After Onboarding Call (v2)
- [ ] Exact business hours confirmed (all days)
- [ ] Timezone confirmed
- [ ] Emergency definition finalized
- [ ] On-call / dispatch phone number confirmed
- [ ] Transfer timeout confirmed
- [ ] After-hours fallback confirmed
- [ ] All `questions_or_unknowns` from v1 resolved
- [ ] v2 memo saved at `outputs/accounts/{account_id}/v2/memo.json`
- [ ] Changelog generated at `changelogs/{account_id}_diff.md`
- [ ] Retell agent updated with v2 `system_prompt`

---

## 7. Common Missing Data (What Goes Into `questions_or_unknowns`)

These fields are almost always missing from demo calls and must be collected during onboarding:

1. Exact business hours per day (not just "weekdays")
2. Timezone
3. On-call phone number
4. Transfer timeout preference
5. Fallback if no answer (voicemail vs callback promise vs SMS)
6. After-hours non-emergency handling
7. Any CRM or dispatch software in use
8. Whether bilingual support is needed
9. Seasonal business hour changes (e.g., summer schedule)
10. Holiday closures and what happens to calls

---

## 8. Quick Reference — Pipeline Trigger Summary

| Trigger | Path | Result |
|---------|------|--------|
| Retell webhook (call_ended) | `POST /webhooks/retell` | Auto-detected type, full pipeline |
| Manual submission | `POST /transcripts/submit` | Explicit type, full pipeline |
| File in data/inbox/ | n8n poller every 5 min | Filename-detected type, full pipeline |
| CLI | `python process.py --file ... --type demo` | Direct execution |