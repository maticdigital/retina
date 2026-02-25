#!/usr/bin/env python3
"""Test full PDF render: adapter → renderer → PDF file."""

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
run = build_analysis_run(PROJECT_ID)
print(f"   Score: {run.primary_site.retina_score.total}, "
      f"Lenses: {len(run.primary_site.retina_score.lens_scores)}, "
      f"Recs: {len(run.ai_analysis.recommendations) if run.ai_analysis else 0}")

print("2. Rendering PDF...")
path = render_pdf(run, OUTPUT, assets_dir=ASSETS)
size = path.stat().st_size
print(f"   PDF saved: {path} ({size:,} bytes)")
print(f"\n   open {path}")
