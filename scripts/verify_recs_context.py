#!/usr/bin/env python3
"""Verify that recommendations context builder uses fresh analyst data."""

import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.services.supabase_client import get_supabase
from app.services.recommendations import _sum_sub_scores

sb = get_supabase()
project_id = "cb0058d1-ef23-4cf7-8628-1981fc5dae12"

proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
project = proj_resp.data[0]

data_resp = sb.table("project_data").select("*").eq("project_id", project_id).execute()
project_data = data_resp.data[0] if data_resp.data else {}

scores_resp = sb.table("analyst_scores").select("*").eq("project_id", project_id).execute()
analyst_scores = scores_resp.data or []

reports_resp = (
    sb.table("reports").select("*").eq("project_id", project_id)
    .order("generated_at", desc=True).limit(1).execute()
)
report = reports_resp.data[0] if reports_resp.data else None

# Build context
context_parts = []
context_parts.append("Website: " + project["primary_url"])
context_parts.append("Project: " + project["name"])

if report and report.get("retina_score"):
    context_parts.append("Overall Retina Score: " + str(report["retina_score"]) + "/100")

# Analyst scores
if analyst_scores:
    context_parts.append("\n## Analyst Lens Scores")
    for s in analyst_scores:
        sub = s.get("sub_scores", {})
        total = _sum_sub_scores(sub)
        context_parts.append("- " + s["lens_name"] + ": " + str(round(total, 1)) + "/20")
        for dim_key, dim_val in sub.items():
            if isinstance(dim_val, dict):
                dim_score = dim_val.get("score", 0)
                dim_obs = dim_val.get("observation", "")
                label = dim_key.replace("_", " ").title()
                context_parts.append("  - " + label + ": " + str(dim_score) + "/5")
                if dim_obs:
                    context_parts.append("    " + dim_obs[:100] + "...")
            elif isinstance(dim_val, (int, float)):
                label = dim_key.replace("_", " ").title()
                context_parts.append("  - " + label + ": " + str(dim_val) + "/5")
        if s.get("raw_observations"):
            context_parts.append("  Overall observations: " + s["raw_observations"][:100] + "...")

# User-edited observations
interps = project_data.get("interpretations") or {}
user_edits = interps.get("_user_edits") or {}
if user_edits:
    context_parts.append("\n## Analyst-Edited Observations")
    for lens_key, obs_text in user_edits.items():
        if obs_text and not lens_key.startswith("_"):
            label = lens_key.replace("_", " ").title()
            context_parts.append("\n### " + label)
            context_parts.append(str(obs_text)[:150] + "...")

user_message = "\n".join(context_parts)
print("Context length:", len(user_message), "chars")
print("---")
print(user_message[:2500])
print("\n---\n[TRUNCATED]")
