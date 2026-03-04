from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_text_from_json(path: Path) -> str:
    data = read_json(path, default={})
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        for key in ("transcript", "text", "content", "body"):
            if key in data and isinstance(data[key], str):
                return data[key]
    return json.dumps(data, ensure_ascii=False)


def pdf_to_text(path: Path) -> str:
    cmd = ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def read_transcript_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == ".json":
        return load_text_from_json(path)
    if ext == ".pdf":
        return pdf_to_text(path)
    if ext in {".m4a", ".mp3", ".wav", ".mp4", ".mov"}:
        # Zero-cost fallback: use sidecar text files when local STT is unavailable.
        chunks = []
        sidecar_txt = path.with_suffix(".txt")
        if sidecar_txt.exists():
            chunks.append(sidecar_txt.read_text(encoding="utf-8", errors="ignore"))
        chat_txt = path.parent / "chat.txt"
        if chat_txt.exists():
            chunks.append(chat_txt.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(c for c in chunks if c.strip())
    return ""


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "account"


def env_str(name: str, default: str) -> str:
    return os.getenv(name, default)
