from typing import List, Optional
from pydantic import BaseModel, Field

class AccountMemo(BaseModel):
    account_id: str = Field(description="Unique identifier for the account")
    company_name: str = Field(description="Name of the company")
    business_hours: Optional[str] = Field(None, description="Detailed business hours, including timezone and days")
    office_address: Optional[str] = Field(None, description="Physical office address if provided")
    services_supported: List[str] = Field(default_factory=list, description="List of services the company offers")
    emergency_definition: List[str] = Field(default_factory=list, description="List of trigger conditions that classify a call as an emergency")
    emergency_routing_rules: Optional[str] = Field(None, description="Who to call, order of calling, and fallback sequence for emergencies")
    non_emergency_routing_rules: Optional[str] = Field(None, description="How non-emergency calls should be handled, such as leaving a message or booking an appointment")
    call_transfer_rules: Optional[str] = Field(None, description="Specifics on transfer timeouts, retries, and what the agent should say if a transfer fails")
    integration_constraints: Optional[str] = Field(None, description="Specific rules regarding integrations, like 'never create jobs in ServiceTrade'")
    after_hours_flow_summary: Optional[str] = Field(None, description="High level summary of the after-hours procedure")
    office_hours_flow_summary: Optional[str] = Field(None, description="High level summary of the office-hours procedure")
    questions_or_unknowns: Optional[str] = Field(None, description="Crucial missing details that could not be determined from the transcript. NEVER GUESS OR HALLUCINATE missing information; put it here instead.")
    notes: Optional[str] = Field(None, description="Brief miscellaneous notes")
    version: str = Field(description="The version of this layout string, either 'v1' or 'v2' etc.")


class RetellAgentSpec(BaseModel):
    agent_name: str = Field(description="Name of the agent, eg 'Clara'")
    voice_style: str = Field(description="Short description of the voice, usually professional and helpful")
    system_prompt: str = Field(description="The complete, comprehensive text prompt guiding the agent's behavior")
    key_variables: dict = Field(default_factory=dict, description="A dictionary of key variables like timezone, business_hours, emergency_routing that the prompt uses")
    call_transfer_protocol: str = Field(description="Summary of the call transfer protocol")
    fallback_protocol: str = Field(description="Summary of what happens if a transfer fails")
    version: str = Field(description="The version of the agent spec, typically matching the AccountMemo version ('v1' or 'v2')")
