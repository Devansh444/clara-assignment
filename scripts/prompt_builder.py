from __future__ import annotations

from typing import Any, Dict


def build_system_prompt(memo: Dict[str, Any]) -> str:
    company = memo.get("company_name") or "the company"
    tz = memo.get("business_hours", {}).get("timezone") or "local timezone"
    bh = memo.get("business_hours", {})
    days = ", ".join(bh.get("days", [])) if bh.get("days") else "unspecified days"
    start = bh.get("start") or "unspecified start"
    end = bh.get("end") or "unspecified end"
    address = memo.get("office_address") or "not provided"

    emergency_rules = memo.get("emergency_definition", [])
    emergency_text = "; ".join(emergency_rules) if emergency_rules else "Use provided emergency triggers; if unclear, ask one clarifying question."

    transfer_fail_script = memo.get("call_transfer_rules", {}).get("transfer_fail_script") or (
        "I am sorry, I could not connect you right now. Our team will follow up shortly."
    )

    return f"""
You are Clara, the inbound call assistant for {company}.

Operating context:
- Timezone: {tz}
- Business hours: {days}, {start} to {end}
- Office address: {address}
- Emergency definition guidance: {emergency_text}

Conversation rules:
- Be concise and professional.
- Do not mention tools, function calls, JSON, or internal systems to callers.
- Ask only necessary routing/dispatch questions.

Business-hours flow (must follow):
1) Greet caller.
2) Ask purpose of call.
3) Collect caller full name and callback number.
4) Route or transfer based on purpose and rules.
5) If transfer fails, use transfer-fail protocol.
6) Confirm next steps.
7) Ask if caller needs anything else.
8) Close if no.

After-hours flow (must follow):
1) Greet caller.
2) Ask purpose of call.
3) Confirm whether this is an emergency.
4) If emergency: immediately collect name, callback number, and service address.
5) Attempt transfer per emergency routing protocol.
6) If transfer fails: apologize and assure urgent follow-up.
7) If non-emergency: collect details and confirm follow-up during business hours.
8) Ask if caller needs anything else.
9) Close call.

Transfer protocol:
- Attempt transfer to configured target order.
- Respect timeout/retry settings.
- If transfer fails, say exactly: {transfer_fail_script}
- Capture enough details for dispatch handoff.

Data capture minimum:
- Name
- Callback number
- Service address (immediately for emergency)
- Short issue summary
""".strip()


def build_retell_spec(memo: Dict[str, Any]) -> Dict[str, Any]:
    account_id = memo.get("account_id", "account")
    version = memo.get("version", "v1")
    return {
        "agent_name": f"clara_{account_id}_{version}",
        "voice_style": "calm_professional",
        "system_prompt": build_system_prompt(memo),
        "key_variables": {
            "timezone": memo.get("business_hours", {}).get("timezone", ""),
            "business_hours": memo.get("business_hours", {}),
            "office_address": memo.get("office_address", ""),
            "emergency_routing": memo.get("emergency_routing_rules", {}),
        },
        "tool_invocation_placeholders": {
            "dispatch_handoff": "placeholder_dispatch_handoff",
            "crm_lookup": "placeholder_crm_lookup",
            "call_transfer": "placeholder_call_transfer",
        },
        "call_transfer_protocol": memo.get("call_transfer_rules", {}),
        "fallback_protocol_if_transfer_fails": memo.get("call_transfer_rules", {}).get(
            "transfer_fail_script", ""
        ),
        "version": version,
    }
