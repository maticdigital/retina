#!/usr/bin/env python3
"""Test the PDF adapter standalone — verify AnalysisRun is built correctly."""

import os
import sys
import json

project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from api.services.pdf_adapter import build_analysis_run

PROJECT_ID = "cb0058d1-ef23-4cf7-8628-1981fc5dae12"

print("Building AnalysisRun for Matic Test project...")
print("=" * 60)

run = build_analysis_run(PROJECT_ID)

print(f"\nrun_id: {run.run_id}")
print(f"created_at: {run.created_at}")
print(f"primary_site.url: {run.primary_site.url}")
print(f"primary_site.normalized_url: {run.primary_site.normalized_url}")

# Retina Score
rs = run.primary_site.retina_score
print(f"\nRetina Score total: {rs.total}")
print(f"Lens scores ({len(rs.lens_scores)}):")
for ls in rs.lens_scores:
    print(f"  {ls.lens.value}: {ls.score:.1f}/20 (automated={ls.is_automated})")
    if ls.breakdown:
        for k, v in ls.breakdown.items():
            print(f"    {k}: {v}")
    if ls.notes:
        print(f"    notes: {ls.notes[:100]}...")

# Performance
print(f"\nPerformance data: {len(run.primary_site.performance)} devices")
for pd in run.primary_site.performance:
    print(f"  {pd.strategy.value}: perf={pd.lighthouse_scores.performance}, seo={pd.lighthouse_scores.seo}")
    cwv = pd.core_web_vitals
    print(f"    LCP={cwv.largest_contentful_paint_ms}, FCP={cwv.first_contentful_paint_ms}, CLS={cwv.cumulative_layout_shift}")

# Tech stack
ts = run.primary_site.tech_stack
if ts:
    print(f"\nTech stack: {len(ts.technologies)} technologies")
    for t in ts.technologies[:5]:
        print(f"  {t.name} ({', '.join(t.categories[:2])})")
    if len(ts.technologies) > 5:
        print(f"  ... and {len(ts.technologies) - 5} more")
else:
    print("\nTech stack: None")

# Screenshots
ss = run.primary_site.screenshots
if ss:
    print(f"\nScreenshots: viewport={ss.viewport}")
else:
    print("\nScreenshots: None")

# AI Analysis
ai = run.ai_analysis
if ai:
    print(f"\nAI Analysis:")
    print(f"  Executive summary: {ai.executive_summary[:100]}..." if ai.executive_summary else "  Executive summary: (empty)")
    print(f"  Recommendations: {len(ai.recommendations)}")
    for r in ai.recommendations[:3]:
        print(f"    [{r.quadrant.value}] {r.title}")
    if len(ai.recommendations) > 3:
        print(f"    ... and {len(ai.recommendations) - 3} more")
else:
    print("\nAI Analysis: None")

# Competitors
print(f"\nCompetitors: {len(run.competitors)}")

print("\n" + "=" * 60)
print("SUCCESS: AnalysisRun built successfully!")
