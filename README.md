# Clara Answers Assignment Solution (Zero-Cost, Reproducible)

This repository implements the required automation pipeline:

- Pipeline A: Demo transcript -> `v1` Account Memo JSON + Retell Agent Draft Spec
- Pipeline B: Onboarding transcript/form -> `v2` memo/spec update + changelog

The implementation is fully zero-cost and uses only local, rule-based extraction (no paid APIs).

## Project Structure

- `scripts/` - extraction, merge, prompt generation, and pipeline runner
- `workflows/` - n8n workflow export (importable starter template)
- `outputs/accounts/<account_id>/v1` and `v2` - generated artifacts
- `changelog/` - per-account change logs
- `logs/` - execution logs

## Requirements

- Python 3.10+
- Optional: `pdftotext` in PATH (for PDF transcript support)

No Python package dependencies are required.

## Input Dataset Layout

Place files under `dataset/` using either layout:

Option 1:
- `dataset/demo/` (5 demo files)
- `dataset/onboarding/` (5 onboarding files)

Option 2:
- `dataset/` with filenames containing `demo` or `onboarding`

Accepted file types:
- `.txt`, `.md`, `.json`, `.pdf`, `.m4a`, `.mp3`, `.wav`, `.mp4`, `.mov`

For `.json`, the script will try keys like `transcript`, `text`, `content`.
For media files, the pipeline uses zero-cost fallback ingestion from sidecars:
- `<same_name>.txt` if present
- `chat.txt` in the same folder
- `recording.conf` in the same folder

## Run

```bash
python scripts/run_pipeline.py --input-root dataset
```

Useful flags:

```bash
python scripts/run_pipeline.py --input-root dataset --force
python scripts/run_pipeline.py --input-root dataset --account-id acme_fire
```

## Outputs Generated Per Account

- `outputs/accounts/<account_id>/v1/account_memo.json`
- `outputs/accounts/<account_id>/v1/retell_agent_spec.json`
- `outputs/accounts/<account_id>/v1/source_manifest.json`
- `outputs/accounts/<account_id>/v2/account_memo.json` (after onboarding)
- `outputs/accounts/<account_id>/v2/retell_agent_spec.json`
- `outputs/accounts/<account_id>/v2/source_manifest.json`
- `changelog/<account_id>_v1_to_v2.md`

Also generated:

- `outputs/tasks/tracker_items.json` (free Asana alternative)
- `outputs/run_summary.json`
- `logs/pipeline.log`

## Retell Setup (Free-Tier Safe)

This solution outputs `Retell Agent Draft Spec` JSON. If Retell API access is unavailable on free tier:

1. Open Retell dashboard
2. Create or edit an agent
3. Copy values from generated `retell_agent_spec.json`
4. Paste `system_prompt` and transfer/fallback configuration into the UI

No paid Retell integration is required.

## n8n Setup (Preferred Orchestrator)

A starter workflow export exists at:

- `workflows/n8n_clara_pipeline.json`

To run n8n locally (optional):

```bash
docker compose -f docker-compose.n8n.yml up -d
```

Then import workflow JSON in n8n UI and map your file paths and command nodes.

## Idempotency and Reliability

- Outputs are deterministic for same input
- Re-running overwrites the same `v1`/`v2` artifacts instead of creating duplicates
- `--force` allows full refresh
- Missing fields are never hallucinated; they go to `questions_or_unknowns`

## Known Limitations

- Rule-based extraction depends on transcript quality and phrasing
- Audio transcription is not included; expects transcript files (or PDF transcripts)
- Routing extraction from unstructured text is heuristic

## Production Improvements

- Add schema validation with strict JSON Schema checks
- Add review queue for low-confidence extraction
- Add true diff visualization UI
- Add direct integrations (Retell, task manager, CRM) when paid/API access exists
