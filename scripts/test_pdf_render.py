#!/usr/bin/env python3
"""Test full PDF render: adapter → renderer → PDF file.

Exercises the same code path as the export endpoint:
  build_analysis_run() → render_pdf() → PDF on disk.
"""

import os
import sys

project_root = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))

from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

# Ensure WeasyPrint can find native libs
os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

from api.services.pdf_adapter import build_analysis_run
from retina.report.renderer import render_pdf

PROJECT_ID = "cb0058d1-ef23-4cf7-8628-1981fc5dae12"
OUTPUT = "/tmp/retina_test_report.pdf"
ASSETS = os.path.join(project_root, "assets")

print("1. Building AnalysisRun...")
result = build_analysis_run(PROJECT_ID)

# Destructure the dict result
analysis = result["analysis"]
project_title = result.get("project_title")
analyst_name = result.get("analyst_name")
subdim_observations = result.get("subdim_observations")

print(f"   Score: {analysis.primary_site.retina_score.total}, "
      f"Lenses: {len(analysis.primary_site.retina_score.lens_scores)}, "
      f"Recs: {len(analysis.ai_analysis.recommendations) if analysis.ai_analysis else 0}")
print(f"   Project: {project_title}, Analyst: {analyst_name}")

print("2. Rendering PDF...")
path = render_pdf(
    analysis,
    OUTPUT,
    assets_dir=ASSETS,
    project_title=project_title,
    analyst_name=analyst_name,
    subdim_observations=subdim_observations,
)
size = path.stat().st_size
print(f"   PDF saved: {path} ({size:,} bytes)")
print(f"\n   open {path}")
