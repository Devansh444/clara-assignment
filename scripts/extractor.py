from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

from io_utils import read_transcript_text, slugify
from schema import new_memo

KNOWN_SERVICES = [
    "sprinkler",
    "fire alarm",
    "extinguisher",
    "backflow",
    "electrical",
    "hvac",
    "inspection",
    "maintenance",
]

TZ_HINTS = ["EST", "EDT", "CST", "CDT", "MST", "MDT", "PST", "PDT", "IST", "UTC"]


def infer_account_id(path: Path) -> str:
    tokens = re.split(r"[_\-\s]+", path.stem.lower())
    stop = {"demo", "onboarding", "call", "recording", "transcript"}
    kept = []
    for t in tokens:
        if not t:
            continue
        if t in stop:
            continue
        if re.fullmatch(r"v\d+", t):
            continue
        kept.append(t)
    return slugify(" ".join(kept))


def _find_company_name(text: str) -> str:
    patterns = [
        r"(?:company|business|client|account)\s*(?:name)?\s*[:\-]\s*([^\n\r]{2,80})",
        r"this is\s+([^\n\r]{2,80})",
        r"we are\s+([^\n\r]{2,80})",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.I)
        if m:
            return m.group(1).strip(" .")
    # Chat-like fallback: pick first likely business-name line from "From BP : ..."
    for raw in text.splitlines():
        line = re.sub(r"^\s*\d{1,2}:\d{2}:\d{2}\s+From\s+[^:]+:\s*", "", raw, flags=re.I).strip()
        if not line:
            continue
        if "@" in line or re.search(r"\d{3}[-\s.]?\d{3}[-\s.]?\d{4}", line):
            continue
        if re.search(r"(company|electric|electrical|fire|sprinkler|hvac|maintenance|washing|solutions|services)", line, flags=re.I):
            return line.strip(" .")
    return ""


def _find_business_hours(text: str) -> Dict[str, object]:
    days = []
    start = ""
    end = ""
    timezone = ""

    day_line = re.search(r"(monday|mon\s*[-to]+\s*fri|mon\s*to\s*fri|monday\s*to\s*friday|7\s*days|weekdays)[^\n.]{0,120}", text, flags=re.I)
    if day_line:
        days_text = day_line.group(1).lower()
        if "7" in days_text:
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        else:
            days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    t = re.search(
        r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\s*(?:to|\-|until)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b",
        text,
        flags=re.I,
    )
    if not t:
        t = re.search(r"\b(\d{1,2}:\d{2})\s*(?:to|\-|until)\s*(\d{1,2}:\d{2})\b", text, flags=re.I)
    if t:
        start, end = t.group(1).strip(), t.group(2).strip()

    for hint in TZ_HINTS:
        if re.search(rf"\b{hint}\b", text):
            timezone = hint
            break

    return {"days": days, "start": start, "end": end, "timezone": timezone}


def _extract_phone_numbers(text: str) -> List[str]:
    nums = re.findall(r"(?:\+?1[\s\-\.]?)?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}", text)
    uniq = []
    for n in nums:
        n2 = re.sub(r"\s+", " ", n).strip()
        if n2 not in uniq:
            uniq.append(n2)
    return uniq


def _extract_services(text: str) -> List[str]:
    low = text.lower()
    out = []
    for s in KNOWN_SERVICES:
        if s in low:
            out.append(s)
    return out


def _extract_emergency_definitions(text: str) -> List[str]:
    lines = re.split(r"[\n\r\.]+", text)
    out = []
    for line in lines:
        low = line.lower().strip()
        if not low:
            continue
        if any(
            k in low
            for k in [
                "emergency",
                "urgent",
                "alarm triggered",
                "sprinkler leak",
                "active fire",
                "dispatch now",
            ]
        ):
            out.append(line.strip())
    return out[:8]


def _extract_integration_constraints(text: str) -> List[str]:
    lines = re.split(r"[\n\r\.]+", text)
    out = []
    for line in lines:
        low = line.lower().strip()
        if any(k in low for k in ["servicetrade", "never create", "do not create", "integration", "crm", "ticket"]):
            out.append(line.strip())
    return out[:8]


def _extract_timeout_retries(text: str) -> Dict[str, object]:
    timeout = None
    retries = None
    m1 = re.search(r"(\d{1,3})\s*seconds?", text, flags=re.I)
    if m1:
        timeout = int(m1.group(1))
    m2 = re.search(r"(\d+)\s*retries|retry\s*(\d+)", text, flags=re.I)
    if m2:
        retries = int(next(g for g in m2.groups() if g))
    return {"timeout_seconds": timeout, "retries": retries}


def _extract_address(text: str) -> str:
    m = re.search(r"(?:address|office)\s*[:\-]\s*([^\n]{5,120})", text, flags=re.I)
    return m.group(1).strip() if m else ""


def build_memo_from_text(text: str, account_id: str, version: str) -> Dict[str, object]:
    memo = new_memo(version=version)
    memo["account_id"] = account_id
    memo["company_name"] = _find_company_name(text)
    memo["business_hours"] = _find_business_hours(text)
    memo["office_address"] = _extract_address(text)
    memo["services_supported"] = _extract_services(text)
    memo["emergency_definition"] = _extract_emergency_definitions(text)

    phones = _extract_phone_numbers(text)
    memo["emergency_routing_rules"] = {
        "primary_contacts": phones[:3],
        "order": ["dispatcher", "on_call_tech", "backup_manager"] if phones else [],
        "fallback": "If transfer fails, apologize and confirm urgent callback.",
    }

    memo["non_emergency_routing_rules"] = {
        "during_business_hours": "Collect caller details and route to office queue.",
        "after_hours": "Collect details and confirm follow-up during business hours.",
    }

    tr = _extract_timeout_retries(text)
    memo["call_transfer_rules"] = {
        "timeout_seconds": tr["timeout_seconds"],
        "retries": tr["retries"],
        "transfer_fail_script": "I am sorry, I could not connect you right now. Our team will follow up shortly.",
    }

    memo["integration_constraints"] = _extract_integration_constraints(text)

    memo["office_hours_flow_summary"] = (
        "Greet, ask purpose, collect name and callback number, route or transfer, "
        "fallback on transfer failure, confirm next step, ask anything else, close."
    )
    memo["after_hours_flow_summary"] = (
        "Greet, ask purpose, confirm emergency. For emergency: collect name, number, and address immediately, "
        "attempt transfer, fallback with apology and urgent callback assurance. For non-emergency: collect details "
        "and confirm business-hours follow-up. Ask anything else, then close."
    )

    unknowns = []
    if not memo["company_name"]:
        unknowns.append("company_name not explicitly stated")
    bh = memo["business_hours"]
    if not bh["days"] or not bh["start"] or not bh["end"] or not bh["timezone"]:
        unknowns.append("business_hours incomplete (days/start/end/timezone)")
    if not memo["emergency_definition"]:
        unknowns.append("emergency_definition not clearly specified")
    if not memo["emergency_routing_rules"]["primary_contacts"]:
        unknowns.append("emergency_routing_rules contacts not found")
    if memo["call_transfer_rules"]["timeout_seconds"] is None:
        unknowns.append("call_transfer_rules timeout not specified")
    if memo["call_transfer_rules"]["retries"] is None:
        unknowns.append("call_transfer_rules retries not specified")

    memo["questions_or_unknowns"] = unknowns
    memo["notes"] = "Auto-generated by deterministic rule-based extractor."
    return memo


def extract_from_file(path: Path, account_id: str | None = None, version: str = "v1") -> Dict[str, object]:
    text = read_transcript_text(path)
    if account_id is None:
        account_id = infer_account_id(path)
    return build_memo_from_text(text=text, account_id=account_id, version=version)
