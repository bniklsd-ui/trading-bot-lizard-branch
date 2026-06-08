"""Summarise the LLM usage / cost log — operator report (Step 5).

Reads the JSON-array usage log written by ``research.token_meter`` (default
``<repo_root>/data/state/llm_usage.json``) and prints token + USD/EUR totals
**by model** and **by day**. Read-only, no network.

Run standalone::

    python scripts/usage_report.py                 # default log path
    python scripts/usage_report.py /path/to/log.json

The aggregation lives in the pure :func:`summarize` so it can be unit-tested
without any I/O.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Record keys produced by token_meter.record (frozen shape).
_NUMERIC_KEYS = ("input_tokens", "output_tokens", "est_cost_usd", "est_cost_eur")


def _empty_bucket() -> dict[str, float]:
    bucket: dict[str, float] = {key: 0 for key in _NUMERIC_KEYS}
    bucket["calls"] = 0
    return bucket


def _add(bucket: dict[str, float], record: dict[str, Any]) -> None:
    for key in _NUMERIC_KEYS:
        bucket[key] += record.get(key, 0) or 0
    bucket["calls"] += 1


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate usage records by model and by day, plus a grand total.

    Args:
        records: List of usage records (each a token_meter record dict with
            ``ts``, ``model``, ``input_tokens``, ``output_tokens``,
            ``est_cost_usd``, ``est_cost_eur``).

    Returns:
        ``{"by_model": {model: bucket}, "by_day": {YYYY-MM-DD: bucket},
        "total": bucket}`` where each bucket carries the four numeric keys plus
        ``calls``. The day is the date prefix of ``ts`` (``"unknown"`` if absent).
    """
    by_model: dict[str, dict[str, float]] = {}
    by_day: dict[str, dict[str, float]] = {}
    total = _empty_bucket()

    for record in records:
        model = record.get("model", "unknown")
        ts = record.get("ts", "")
        day = ts[:10] if isinstance(ts, str) and ts else "unknown"

        _add(by_model.setdefault(model, _empty_bucket()), record)
        _add(by_day.setdefault(day, _empty_bucket()), record)
        _add(total, record)

    return {"by_model": by_model, "by_day": by_day, "total": total}


def _format_bucket_table(title: str, buckets: dict[str, dict[str, float]]) -> str:
    lines = [title, "-" * len(title)]
    header = f"{'key':<28}{'calls':>7}{'in_tok':>12}{'out_tok':>12}{'USD':>12}{'EUR':>12}"
    lines.append(header)
    for key in sorted(buckets):
        b = buckets[key]
        lines.append(
            f"{key:<28}{int(b['calls']):>7}{int(b['input_tokens']):>12}"
            f"{int(b['output_tokens']):>12}{b['est_cost_usd']:>12.4f}"
            f"{b['est_cost_eur']:>12.4f}"
        )
    return "\n".join(lines)


def format_report(summary: dict[str, Any]) -> str:
    """Render a :func:`summarize` result as a human-readable text report."""
    total = summary["total"]
    return "\n\n".join(
        [
            _format_bucket_table("By model", summary["by_model"]),
            _format_bucket_table("By day", summary["by_day"]),
            (
                f"TOTAL: {int(total['calls'])} calls, "
                f"{int(total['input_tokens'])} in / {int(total['output_tokens'])} out tok, "
                f"${total['est_cost_usd']:.4f} / €{total['est_cost_eur']:.4f}"
            ),
        ]
    )


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load the usage log; missing/empty/corrupt → empty list (advisory log)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as exc:
        print(f"warning: could not read {path}: {exc}", file=sys.stderr)
        return []
    return data if isinstance(data, list) else []


def _default_log_path() -> Path:
    # scripts/ -> phase4_research/ -> repo root -> data/state/llm_usage.json
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data" / "state" / "llm_usage.json"


def main(argv: list[str]) -> int:
    path = Path(argv[0]) if argv else _default_log_path()
    records = load_records(path)
    if not records:
        print(f"No usage records in {path}")
        return 0
    print(format_report(summarize(records)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
