from __future__ import annotations

import json
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC)


def timestamp_slug() -> str:
    return utc_now().strftime("%Y%m%d_%H%M%S")


def sanitize_name(name: str) -> str:
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
    cleaned = "".join(ch if ch in allowed else "-" for ch in name.strip())
    return cleaned.strip("-") or "run"


def create_run_directory(base_output_dir: Path, run_name: str, run_id: str) -> Path:
    base_output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = base_output_dir / f"{sanitize_name(run_name)}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")


def write_lines(path: Path, lines: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def detect_git_commit(cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return None

    commit = completed.stdout.strip()
    return commit or None
