from __future__ import annotations

import argparse
from pathlib import Path

from pipeline import PipelineConfig, run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Clara assignment automation pipeline")
    parser.add_argument("--input-root", default="dataset", help="Input dataset directory")
    parser.add_argument("--output-root", default="outputs", help="Output directory")
    parser.add_argument("--changelog-root", default="changelog", help="Changelog directory")
    parser.add_argument("--logs-root", default="logs", help="Logs directory")
    parser.add_argument("--force", action="store_true", help="Reprocess even if file checksum unchanged")
    parser.add_argument("--account-id", default=None, help="Override account_id for all processed files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = PipelineConfig(
        input_root=Path(args.input_root),
        output_root=Path(args.output_root),
        changelog_root=Path(args.changelog_root),
        logs_root=Path(args.logs_root),
        force=args.force,
        account_id_override=args.account_id,
    )
    summary = run_pipeline(cfg)
    print("Pipeline complete")
    print(summary)


if __name__ == "__main__":
    main()
