#!/usr/bin/env python3
"""Seed the retina_standards table from the JSON library file.

Usage:
    python scripts/seed_standards.py

Re-runnable: truncates the table before inserting to ensure idempotency.
Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env or environment.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

# Load env from project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set.", file=sys.stderr)
    sys.exit(1)

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "retina_standards_library.json"


def main() -> None:
    # Read seed data
    if not DATA_FILE.exists():
        print(f"ERROR: Seed file not found at {DATA_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(DATA_FILE) as f:
        entries = json.load(f)

    print(f"Loaded {len(entries)} standards from {DATA_FILE.name}")

    # Connect to Supabase
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Clear existing entries for a clean reseed
    print("Clearing existing retina_standards rows...")
    sb.table("retina_standards").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    # Insert in batches of 20
    batch_size = 20
    inserted = 0
    for i in range(0, len(entries), batch_size):
        batch = entries[i : i + batch_size]
        resp = sb.table("retina_standards").insert(batch).execute()
        inserted += len(resp.data)

    # Report counts per lens
    counts = Counter(e["lens"] for e in entries)
    print(f"\nInserted {inserted} standards:")
    for lens, count in sorted(counts.items()):
        print(f"  {lens}: {count}")

    print("\nDone.")


if __name__ == "__main__":
    main()
