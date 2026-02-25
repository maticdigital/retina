#!/usr/bin/env python3
"""Migrate analyst_scores sub_scores from old sub-dimension keys to new standardized keys.

Old → New mapping:
  Brand & Messaging (was 4×5, stays 4×5):
    brand_clarity_consistency → brand_visual_language
    content_quality_tone → brand_voice_messaging
    value_proposition_strength → value_proposition
    visual_identity_differentiation → brand_differentiation

  Experience & Design (was 5×4, now 4×5):
    visual_design_quality → interface_design
    content_layout_readability → content_taxonomy
    navigation_information_architecture → navigation_architecture
    responsiveness_cross_device → responsiveness
    interaction_design_micro_interactions → DROPPED

  Conversion & Strategy (was 5×4, now 4×5):
    cta_effectiveness → call_to_action_logic
    lead_capture_form_design → lead_capture_form_design (unchanged)
    trust_signals_social_proof → trust_signals
    user_journey_funnel_design → funnel_design
    strategic_positioning_vs_competitors → DROPPED

For experience/conversion lenses that had 5 sub-dims at /4 each (total 20),
the scores are rescaled to /5 each (still total 20) using: new_score = old_score * (5/4).
"""

import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")

# Mapping: old_key → new_key
OLD_TO_NEW = {
    # Brand & Messaging
    "brand_clarity_consistency": "brand_visual_language",
    "content_quality_tone": "brand_voice_messaging",
    "value_proposition_strength": "value_proposition",
    "visual_identity_differentiation": "brand_differentiation",
    # Experience & Design
    "visual_design_quality": "interface_design",
    "content_layout_readability": "content_taxonomy",
    "navigation_information_architecture": "navigation_architecture",
    "responsiveness_cross_device": "responsiveness",
    # Conversion & Strategy
    "cta_effectiveness": "call_to_action_logic",
    "user_journey_funnel_design": "funnel_design",
    "trust_signals_social_proof": "trust_signals",
    # lead_capture_form_design stays the same
}

# Sub-dims that are dropped (no mapping)
DROPPED = {"interaction_design_micro_interactions", "strategic_positioning_vs_competitors"}

# Lenses where scores need rescaling from /4 to /5
RESCALE_LENSES = {"experience_design", "conversion_strategy"}

# New valid sub-dimension keys per lens
NEW_KEYS = {
    "brand_messaging": {"brand_visual_language", "brand_voice_messaging", "value_proposition", "brand_differentiation"},
    "experience_design": {"interface_design", "content_taxonomy", "navigation_architecture", "responsiveness"},
    "conversion_strategy": {"call_to_action_logic", "lead_capture_form_design", "trust_signals", "funnel_design"},
}


def migrate_sub_scores(lens_name: str, sub_scores: dict) -> dict:
    """Migrate a single sub_scores dict from old keys to new keys."""
    if not isinstance(sub_scores, dict):
        return sub_scores

    new_scores = {}
    needs_rescale = lens_name in RESCALE_LENSES

    for old_key, value in sub_scores.items():
        # Skip dropped sub-dimensions
        if old_key in DROPPED:
            print(f"  DROPPED: {old_key}")
            continue

        # Map old key to new key
        new_key = OLD_TO_NEW.get(old_key, old_key)

        # Extract score and observation from value
        if isinstance(value, dict):
            score = float(value.get("score", 0))
            observation = value.get("observation", "")
        elif isinstance(value, (int, float)):
            score = float(value)
            observation = ""
        else:
            score = 0.0
            observation = ""

        # Rescale if needed (from /4 to /5)
        if needs_rescale and old_key != new_key:
            old_score = score
            score = round(score * (5.0 / 4.0) * 2) / 2  # round to nearest 0.5
            score = min(score, 5.0)  # clamp to max
            print(f"  RESCALE: {old_key} ({old_score}) → {new_key} ({score})")
        elif old_key != new_key:
            print(f"  RENAME: {old_key} → {new_key}")
        else:
            print(f"  KEEP: {old_key}")

        new_scores[new_key] = {
            "score": score,
            "observation": observation,
        }

    return new_scores


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        # Try loading from .env
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")

    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "") or os.environ.get("SUPABASE_KEY", "")

    if not url or not key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY/SUPABASE_SERVICE_ROLE_KEY must be set")
        sys.exit(1)

    sb = create_client(url, key)

    # Fetch all analyst_scores records
    resp = sb.table("analyst_scores").select("*").execute()
    records = resp.data or []
    print(f"Found {len(records)} analyst_scores records to migrate\n")

    migrated = 0
    skipped = 0

    for record in records:
        record_id = record["id"]
        lens_name = record.get("lens_name", "")
        sub_scores = record.get("sub_scores") or {}

        if not isinstance(sub_scores, dict) or not sub_scores:
            print(f"SKIP (empty): id={record_id} lens={lens_name}")
            skipped += 1
            continue

        # Check if already migrated (new keys present)
        valid_new = NEW_KEYS.get(lens_name, set())
        existing_keys = set(sub_scores.keys())
        if existing_keys.issubset(valid_new):
            print(f"SKIP (already migrated): id={record_id} lens={lens_name}")
            skipped += 1
            continue

        print(f"MIGRATE: id={record_id} lens={lens_name} keys={list(sub_scores.keys())}")
        new_sub_scores = migrate_sub_scores(lens_name, sub_scores)
        print(f"  → new keys: {list(new_sub_scores.keys())}")

        # Update in database
        sb.table("analyst_scores").update({"sub_scores": new_sub_scores}).eq("id", record_id).execute()
        migrated += 1
        print()

    print(f"\nDone! Migrated: {migrated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
