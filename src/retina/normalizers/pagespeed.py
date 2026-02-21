"""Normalize raw PageSpeed Insights API responses into Pydantic models."""

from __future__ import annotations

from datetime import datetime, timezone

from retina.models.normalized import (
    AuditItem,
    CoreWebVitals,
    DeviceStrategy,
    LighthouseScores,
    PerformanceData,
)


def normalize_pagespeed(raw: dict, strategy: DeviceStrategy) -> PerformanceData:
    """Transform a raw PageSpeed Insights response into a PerformanceData model.

    Args:
        raw: Raw JSON response from the PageSpeed API.
        strategy: Which device strategy this response represents.

    Returns:
        Normalized PerformanceData with scores, Core Web Vitals, and audits.
    """
    lr = raw.get("lighthouseResult", {})
    categories = lr.get("categories", {})
    audits = lr.get("audits", {})

    lighthouse_scores = LighthouseScores(
        performance=_score_to_100(categories.get("performance", {}).get("score")),
        accessibility=_score_to_100(categories.get("accessibility", {}).get("score")),
        best_practices=_score_to_100(categories.get("best-practices", {}).get("score")),
        seo=_score_to_100(categories.get("seo", {}).get("score")),
    )

    cwv = CoreWebVitals(
        largest_contentful_paint_ms=_numeric(audits, "largest-contentful-paint"),
        first_contentful_paint_ms=_numeric(audits, "first-contentful-paint"),
        cumulative_layout_shift=_numeric(audits, "cumulative-layout-shift"),
        total_blocking_time_ms=_numeric(audits, "total-blocking-time"),
        speed_index_ms=_numeric(audits, "speed-index"),
        interaction_to_next_paint_ms=_numeric(audits, "interaction-to-next-paint"),
    )

    audit_items = _extract_audits(lr)

    return PerformanceData(
        strategy=strategy,
        lighthouse_scores=lighthouse_scores,
        core_web_vitals=cwv,
        audits=audit_items,
        fetch_time=_parse_time(lr.get("fetchTime")),
    )


def _score_to_100(score: float | None) -> float | None:
    """Convert Lighthouse 0-1 score to 0-100 scale."""
    if score is None:
        return None
    return round(score * 100, 1)


def _numeric(audits: dict, key: str) -> float | None:
    """Extract numericValue from an audit entry."""
    audit = audits.get(key, {})
    value = audit.get("numericValue")
    return float(value) if value is not None else None


def _parse_time(time_str: str | None) -> datetime | None:
    """Parse Lighthouse fetchTime ISO string."""
    if not time_str:
        return None
    try:
        return datetime.fromisoformat(time_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def _extract_audits(lr: dict) -> list[AuditItem]:
    """Walk categories → auditRefs and merge with the audits map.

    Returns a list of AuditItem models with category and weight info.
    """
    items: list[AuditItem] = []
    categories = lr.get("categories", {})
    audits_map = lr.get("audits", {})
    seen_ids: set[str] = set()

    for cat_key, cat_obj in categories.items():
        for ref in cat_obj.get("auditRefs", []):
            audit_id = ref.get("id", "")
            if not audit_id:
                continue

            # An audit can appear in multiple categories — include it with each
            # category's weight, but deduplicate by (id, category) pair
            dedup_key = f"{audit_id}:{cat_key}"
            if dedup_key in seen_ids:
                continue
            seen_ids.add(dedup_key)

            audit_data = audits_map.get(audit_id, {})
            items.append(
                AuditItem(
                    id=audit_id,
                    title=audit_data.get("title", audit_id),
                    description=audit_data.get("description", ""),
                    score=audit_data.get("score"),
                    display_value=audit_data.get("displayValue"),
                    category=cat_key,
                    weight=ref.get("weight", 0),
                )
            )

    return items
