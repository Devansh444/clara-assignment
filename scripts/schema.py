from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict


EMPTY_MEMO_TEMPLATE: Dict[str, Any] = {
    "account_id": "",
    "company_name": "",
    "business_hours": {
        "days": [],
        "start": "",
        "end": "",
        "timezone": "",
    },
    "office_address": "",
    "services_supported": [],
    "emergency_definition": [],
    "emergency_routing_rules": {
        "primary_contacts": [],
        "order": [],
        "fallback": "",
    },
    "non_emergency_routing_rules": {
        "during_business_hours": "",
        "after_hours": "",
    },
    "call_transfer_rules": {
        "timeout_seconds": None,
        "retries": None,
        "transfer_fail_script": "",
    },
    "integration_constraints": [],
    "after_hours_flow_summary": "",
    "office_hours_flow_summary": "",
    "questions_or_unknowns": [],
    "notes": "",
    "version": "v1",
    "last_updated_utc": "",
}


def new_memo(version: str = "v1") -> Dict[str, Any]:
    memo = deepcopy(EMPTY_MEMO_TEMPLATE)
    memo["version"] = version
    memo["last_updated_utc"] = datetime.now(timezone.utc).isoformat()
    return memo
