"""Lightweight PDF adapter for Vercel deployment.

This version provides fallback functionality when heavy dependencies
like weasyprint and playwright are not available.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def build_analysis_run(project_id: str) -> Dict[str, Any]:
    """Build analysis run data from Supabase.
    
    This is a lightweight version that focuses on data retrieval
    without heavy PDF generation dependencies.
    """
    try:
        # Import the original function if available
        from api.services.pdf_adapter import build_analysis_run as original_build
        return original_build(project_id)
    except ImportError as e:
        logger.warning("Heavy dependencies not available, using lite version: %s", e)
        
        # Fallback implementation - return basic project data
        # This would need to be implemented based on your actual data structure
        return {
            "analysis": None,
            "project_title": f"Project {project_id}",
            "analyst_name": "System",
            "subdim_observations": {},
            "error": "PDF generation not available in lite deployment"
        }


def render_pdf_lite(analysis_run: Any, output_path: str, **kwargs) -> None:
    """Lightweight PDF rendering fallback.
    
    This creates a simple text-based report instead of a full PDF.
    """
    logger.info("Using lite PDF rendering - creating text report")
    
    with open(output_path, 'w') as f:
        f.write("RETINA ANALYSIS REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write("This is a simplified report generated in lite mode.\n")
        f.write("Full PDF generation requires additional dependencies.\n\n")
        
        if analysis_run:
            f.write(f"Project: {kwargs.get('project_title', 'Unknown')}\n")
            f.write(f"Analyst: {kwargs.get('analyst_name', 'System')}\n")
            f.write("\nNote: Full analysis data available via API endpoints.\n")
        else:
            f.write("Analysis data not available.\n")
    
    logger.info("Lite report generated at %s", output_path)
