"""Tests for the usage-report aggregation (Step 5) — pure, no I/O."""

from __future__ import annotations

from scripts.usage_report import format_report, summarize

_RECORDS = [
    {"ts": "2026-06-08T09:30:00.000Z", "model": "claude-sonnet-4-6",
     "input_tokens": 100, "output_tokens": 50, "est_cost_usd": 0.001, "est_cost_eur": 0.0009},
    {"ts": "2026-06-08T17:00:00.000Z", "model": "claude-sonnet-4-6",
     "input_tokens": 200, "output_tokens": 80, "est_cost_usd": 0.002, "est_cost_eur": 0.0018},
    {"ts": "2026-06-09T09:30:00.000Z", "model": "claude-opus-4-8",
     "input_tokens": 300, "output_tokens": 120, "est_cost_usd": 0.005, "est_cost_eur": 0.0046},
]


def test_summarize_aggregates_by_model() -> None:
    s = summarize(_RECORDS)
    sonnet = s["by_model"]["claude-sonnet-4-6"]
    assert sonnet["calls"] == 2
    assert sonnet["input_tokens"] == 300
    assert sonnet["output_tokens"] == 130
    assert round(sonnet["est_cost_usd"], 6) == 0.003
    assert s["by_model"]["claude-opus-4-8"]["calls"] == 1


def test_summarize_aggregates_by_day() -> None:
    s = summarize(_RECORDS)
    assert set(s["by_day"]) == {"2026-06-08", "2026-06-09"}
    assert s["by_day"]["2026-06-08"]["calls"] == 2
    assert s["by_day"]["2026-06-09"]["input_tokens"] == 300


def test_summarize_total_and_empty() -> None:
    total = summarize(_RECORDS)["total"]
    assert total["calls"] == 3
    assert total["input_tokens"] == 600
    assert total["output_tokens"] == 250

    empty = summarize([])
    assert empty["total"]["calls"] == 0
    assert empty["by_model"] == {}


def test_format_report_renders_totals() -> None:
    report = format_report(summarize(_RECORDS))
    assert "By model" in report and "By day" in report
    assert "TOTAL: 3 calls" in report
