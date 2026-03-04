# Changelog for Account: account_1

## Updates from Onboarding (v1 -> v2)
- **business_hours** updated:
  - *old:* `8:00 AM to 5:00 PM`
  - *new:* `8:00 AM to 5:00 PM EST, Monday through Friday`
- **emergency_definition** items added: `Fire alarms triggered`
- **emergency_definition** items removed: `Active sprinkler leak`
- **emergency_routing_rules** added: `Call dispatch first at 555-0199. If they don't answer within 30 seconds, fallback and call my cell at 555-0100.`
- **non_emergency_routing_rules** added: `Leave a message.`
- **call_transfer_rules** added: `Transfer to main office.`
- **integration_constraints** added: `NEVER create sprinkler jobs in ServiceTrade automatically. Only log notes.`
- **questions_or_unknowns** removed (was `Information is partial. Demo mode fallback.`)
