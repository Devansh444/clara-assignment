from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from extractor import extract_from_file, infer_account_id
from io_utils import ensure_dir, file_sha256, read_json, write_json, write_text
from merge import changes_to_markdown, merge_memo_v2
from prompt_builder import build_retell_spec


@dataclass
class PipelineConfig:
    input_root: Path
    output_root: Path
    changelog_root: Path
    logs_root: Path
    force: bool = False
    account_id_override: str | None = None


def _setup_logging(logs_root: Path) -> None:
    ensure_dir(logs_root)
    log_path = logs_root / "pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )


def _discover_inputs(input_root: Path) -> tuple[List[Path], List[Path]]:
    supported = {".txt", ".md", ".json", ".pdf", ".m4a", ".mp3", ".wav", ".mp4", ".mov"}
    demo = []
    onboarding = []

    demo_dir = input_root / "demo"
    onboarding_dir = input_root / "onboarding"

    if demo_dir.exists() and onboarding_dir.exists():
        def keep_file(p: Path) -> bool:
            if not p.is_file() or p.suffix.lower() not in supported:
                return False
            if p.name.lower() in {"chat.txt", "recording.conf"}:
                return False
            return True

        demo = sorted(p for p in demo_dir.rglob("*") if keep_file(p))
        onboarding = sorted(p for p in onboarding_dir.rglob("*") if keep_file(p))
        return demo, onboarding

    for p in sorted(input_root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in supported:
            continue
        low = p.name.lower()
        if "onboarding" in low:
            onboarding.append(p)
        elif "demo" in low:
            demo.append(p)

    return demo, onboarding


def _state_path(output_root: Path) -> Path:
    return output_root / ".state" / "run_state.json"


def _load_state(output_root: Path) -> Dict[str, str]:
    return read_json(_state_path(output_root), default={}) or {}


def _save_state(output_root: Path, state: Dict[str, str]) -> None:
    write_json(_state_path(output_root), state)


def _account_dir(output_root: Path, account_id: str, version: str) -> Path:
    return output_root / "accounts" / account_id / version


def _write_task_tracker(output_root: Path, account_id: str, version: str, source: Path) -> None:
    tracker_path = output_root / "tasks" / "tracker_items.json"
    items = read_json(tracker_path, default=[])
    key = f"{account_id}:{version}:{source.name}"
    if not any(i.get("key") == key for i in items):
        items.append(
            {
                "key": key,
                "account_id": account_id,
                "version": version,
                "source_file": str(source),
                "status": "generated",
            }
        )
        write_json(tracker_path, items)


def process_demo_file(cfg: PipelineConfig, source: Path, state: Dict[str, str]) -> str:
    checksum = file_sha256(source)
    state_key = f"demo:{source}"
    if not cfg.force and state.get(state_key) == checksum:
        logging.info("Skip unchanged demo file: %s", source)
        account_id = cfg.account_id_override or infer_account_id(source)
        return account_id

    account_id = cfg.account_id_override or infer_account_id(source)
    memo_v1 = extract_from_file(source, account_id=account_id, version="v1")
    spec_v1 = build_retell_spec(memo_v1)

    out_dir = _account_dir(cfg.output_root, account_id, "v1")
    ensure_dir(out_dir)
    write_json(out_dir / "account_memo.json", memo_v1)
    write_json(out_dir / "retell_agent_spec.json", spec_v1)
    write_json(
        out_dir / "source_manifest.json",
        {"source_type": "demo", "source_path": str(source), "sha256": checksum},
    )

    _write_task_tracker(cfg.output_root, account_id, "v1", source)
    state[state_key] = checksum
    logging.info("Generated v1 for account_id=%s from %s", account_id, source)
    return account_id


def process_onboarding_file(cfg: PipelineConfig, source: Path, state: Dict[str, str]) -> str:
    checksum = file_sha256(source)
    state_key = f"onboarding:{source}"
    account_id = cfg.account_id_override or infer_account_id(source)

    if not cfg.force and state.get(state_key) == checksum:
        logging.info("Skip unchanged onboarding file: %s", source)
        return account_id

    v1_path = _account_dir(cfg.output_root, account_id, "v1") / "account_memo.json"
    v1 = read_json(v1_path, default=None)
    if not v1:
        logging.warning("No v1 found for account_id=%s. Creating v1 first from onboarding as fallback.", account_id)
        v1 = extract_from_file(source, account_id=account_id, version="v1")
        write_json(_account_dir(cfg.output_root, account_id, "v1") / "account_memo.json", v1)
        write_json(_account_dir(cfg.output_root, account_id, "v1") / "retell_agent_spec.json", build_retell_spec(v1))

    patch = extract_from_file(source, account_id=account_id, version="v2")
    v2, changes = merge_memo_v2(v1, patch)
    spec_v2 = build_retell_spec(v2)

    out_dir = _account_dir(cfg.output_root, account_id, "v2")
    ensure_dir(out_dir)
    write_json(out_dir / "account_memo.json", v2)
    write_json(out_dir / "retell_agent_spec.json", spec_v2)
    write_json(
        out_dir / "source_manifest.json",
        {"source_type": "onboarding", "source_path": str(source), "sha256": checksum},
    )

    ensure_dir(cfg.changelog_root)
    write_text(cfg.changelog_root / f"{account_id}_v1_to_v2.md", changes_to_markdown(account_id, changes))

    _write_task_tracker(cfg.output_root, account_id, "v2", source)
    state[state_key] = checksum
    logging.info("Generated v2 for account_id=%s from %s", account_id, source)
    return account_id


def run_pipeline(cfg: PipelineConfig) -> dict:
    _setup_logging(cfg.logs_root)
    logging.info("Starting pipeline with input_root=%s", cfg.input_root)

    ensure_dir(cfg.output_root)
    state = _load_state(cfg.output_root)

    demo_files, onboarding_files = _discover_inputs(cfg.input_root)
    logging.info("Discovered %d demo files and %d onboarding files", len(demo_files), len(onboarding_files))

    accounts_seen = set()
    for p in demo_files:
        accounts_seen.add(process_demo_file(cfg, p, state))
    for p in onboarding_files:
        accounts_seen.add(process_onboarding_file(cfg, p, state))

    _save_state(cfg.output_root, state)

    summary = {
        "accounts_processed": sorted(accounts_seen),
        "demo_files": [str(p) for p in demo_files],
        "onboarding_files": [str(p) for p in onboarding_files],
        "output_root": str(cfg.output_root),
        "changelog_root": str(cfg.changelog_root),
    }
    write_json(cfg.output_root / "run_summary.json", summary)
    logging.info("Pipeline complete. Accounts processed: %d", len(accounts_seen))
    return summary
