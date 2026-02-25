"""Test script for Phase 1 PDF report generation.

Generates a sample PDF using mock data. Fetches the actual site screenshot
from the live URL (or renders cleanly without one if the fetch fails).

Usage:
    python3 scripts/test_pdf_phase1.py                 # with screenshot
    python3 scripts/test_pdf_phase1.py --no-screenshot  # without screenshot
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from retina.models.normalized import (
    AnalysisRun,
    SiteReport,
    RetinaScore,
    LensScore,
    ScoringLensType,
    TechStackData,
    Technology,
    ScreenshotData,
    AIAnalysis,
    Recommendation,
    EffortLevel,
    ImpactLevel,
    StrategicQuadrant,
)
from retina.report.renderer import render_pdf, fetch_screenshot_bytes, _encode_image


def _fetch_live_screenshot() -> str | None:
    """Fetch a viewport screenshot of maticdigital.com and return a data URI.

    Returns None if the fetch fails for any reason.
    """
    # Fetch the actual screenshot from Supabase storage (Matic Test project)
    urls_to_try = [
        # Real viewport screenshot from Supabase for maticdigital.com
        "https://xafturogqjhwtubwoval.supabase.co/storage/v1/object/public/screenshots/cb0058d1-ef23-4cf7-8628-1981fc5dae12/476b686089a14d27824a6423f3d0b9dd.png",
    ]

    for url in urls_to_try:
        print(f"  Fetching screenshot from: {url[:80]}...")
        image_bytes = fetch_screenshot_bytes(url)
        if image_bytes and len(image_bytes) > 1000:
            print(f"  ✓ Downloaded {len(image_bytes):,} bytes")
            # Detect MIME from URL extension
            mime = "image/png"
            if url.lower().split("?")[0].endswith((".jpg", ".jpeg")):
                mime = "image/jpeg"
            return _encode_image(image_bytes, mime=mime)
        print(f"  ✗ Failed or too small")

    return None


def build_sample_analysis(*, include_screenshot: bool = True) -> tuple[AnalysisRun, str | None]:
    """Create a sample AnalysisRun with mock data.

    Returns:
        Tuple of (AnalysisRun, screenshot_data_uri or None).
    """

    # Lens scores
    lens_scores = [
        LensScore(
            lens=ScoringLensType.PERFORMANCE_TECHNICAL,
            score=14.0,
            breakdown={"speed_performance": 3.5, "code_quality": 3.5, "security_ssl": 4.0, "core_web_vitals": 3.0},
            notes="Your site demonstrates excellent visual stability with zero layout shift, but faces significant speed challenges that create visitor friction.",
            is_automated=True,
        ),
        LensScore(
            lens=ScoringLensType.SEO_AI_VISIBILITY,
            score=14.0,
            breakdown={"on_page_seo": 3.5, "technical_seo": 3.5, "ai_visibility": 3.5, "structured_data": 3.5},
            notes="Good foundation for search visibility with room for improvement in AI-specific optimization.",
            is_automated=True,
        ),
        LensScore(
            lens=ScoringLensType.BRAND_MESSAGING,
            score=11.0,
            breakdown={"value_proposition": 4.0, "brand_differentiation": 5.0, "brand_voice_messaging": 2.5, "brand_visual_language": 3.0},
            notes="Matic Digital has built a technically impressive foundation that signals serious digital chops. But the messaging doesn't capitalize on what should be Matic's strongest differentiator — the rare combination of brand strategy and technical execution under one roof.",
            is_automated=False,
        ),
        LensScore(
            lens=ScoringLensType.EXPERIENCE_DESIGN,
            score=16.0,
            breakdown={"interface_design": 4.5, "content_taxonomy": 3.5, "navigation_architecture": 4.0, "responsiveness": 4.0},
            notes="The experience is polished and intentional. Navigation is clear, visual hierarchy guides the eye, and mobile responsiveness is strong.",
            is_automated=False,
        ),
        LensScore(
            lens=ScoringLensType.CONVERSION_STRATEGY,
            score=12.0,
            breakdown={"call_to_action_logic": 3.0, "funnel_design": 3.0, "trust_signals": 3.0, "lead_capture_form_design": 3.0},
            notes="CTAs exist but lack urgency and specificity. The user flow could guide visitors more deliberately toward conversion.",
            is_automated=False,
        ),
    ]

    retina_score = RetinaScore(lens_scores=lens_scores, total=67.0)

    # Tech stack
    tech_stack = TechStackData(
        technologies=[
            Technology(name="Contentful", categories=["Headless"], description="Headless CMS"),
            Technology(name="Webflow", categories=["CMS"], description="Website builder"),
            Technology(name="Google Analytics", categories=["Analytics"], description="Web analytics"),
            Technology(name="Google Analytics 4", categories=["Analytics"], description="GA4"),
            Technology(name="Google Tag Manager", categories=["Tag Management"], description="Tag management"),
            Technology(name="Clutch", categories=["CRM"], description="B2B ratings"),
            Technology(name="Mandrill", categories=["Transactional Email"], description="Email API"),
            Technology(name="Trustpilot", categories=["CRM"], description="Review platform"),
            Technology(name="React", categories=["JavaScript Frameworks"], description="UI library"),
            Technology(name="Next.js", categories=["Web Frameworks"], description="React framework"),
        ]
    )

    # Fetch live screenshot or skip
    screenshot_data_uri = None
    screenshots = None
    if include_screenshot:
        screenshot_data_uri = _fetch_live_screenshot()
        if screenshot_data_uri:
            print(f"  Screenshot data URI: {len(screenshot_data_uri):,} chars")
        else:
            print("  ⚠ No screenshot available — PDF will render without image")

    # Primary site (no local file reference — screenshot handled as data URI)
    primary_site = SiteReport(
        url="https://www.maticdigital.com",
        normalized_url="https://www.maticdigital.com",
        collected_at=datetime.now(timezone.utc),
        performance=[],
        tech_stack=tech_stack,
        screenshots=None,  # Not using local file paths
        retina_score=retina_score,
    )

    # AI Analysis with recommendations
    ai_analysis = AIAnalysis(
        executive_summary=(
            "Your digital presence demonstrates strong technical foundations and a polished "
            "user experience, scoring 67 out of 100 on the Retina Scale. The site's visual "
            "design and interaction quality stand out as particular strengths, reflecting "
            "careful attention to the craft of digital experience.\n\n"
            "However, opportunities exist to sharpen brand messaging and improve conversion "
            "strategy. The gap between your technical capability and your ability to communicate "
            "it clearly represents the most impactful area for improvement. Strengthening "
            "value proposition clarity and CTA specificity would help convert the strong "
            "impressions your site creates into measurable business outcomes."
        ),
        recommendations=[
            Recommendation(
                title="Sharpen the hero value proposition to lead with outcomes, not capabilities",
                description="Rewrite the homepage hero to focus on client outcomes rather than service descriptions.",
                effort=EffortLevel.LOW,
                impact=ImpactLevel.HIGH,
                quadrant=StrategicQuadrant.NO_BRAINER,
                rationale="Low effort, immediate impact on first impressions.",
                related_gaps=["brand_messaging"],
            ),
            Recommendation(
                title="Add specific, action-oriented CTAs throughout the site",
                description="Replace generic 'Learn More' buttons with specific, outcome-focused CTAs.",
                effort=EffortLevel.LOW,
                impact=ImpactLevel.HIGH,
                quadrant=StrategicQuadrant.NO_BRAINER,
                rationale="Quick change with direct conversion impact.",
                related_gaps=["conversion_strategy"],
            ),
            Recommendation(
                title="Implement structured data and schema markup across all pages",
                description="Add JSON-LD structured data for Organization, Service, and FAQ schemas.",
                effort=EffortLevel.LOW,
                impact=ImpactLevel.LOW,
                quadrant=StrategicQuadrant.QUICK_WIN,
                rationale="Technical improvement that supports SEO and AI visibility.",
                related_gaps=["seo_ai_visibility"],
            ),
            Recommendation(
                title="Build a case study library with measurable results",
                description="Create detailed case studies with specific metrics and outcomes.",
                effort=EffortLevel.HIGH,
                impact=ImpactLevel.HIGH,
                quadrant=StrategicQuadrant.GROWTH_MOVE,
                rationale="Significant content investment with long-term conversion benefits.",
                related_gaps=["conversion_strategy"],
            ),
            Recommendation(
                title="Redesign the brand narrative around dual expertise positioning",
                description="Develop messaging that positions Matic as uniquely combining brand strategy with technical execution.",
                effort=EffortLevel.HIGH,
                impact=ImpactLevel.HIGH,
                quadrant=StrategicQuadrant.GROWTH_MOVE,
                rationale="Strategic initiative that differentiates from competitors.",
                related_gaps=["brand_messaging"],
            ),
            Recommendation(
                title="Optimize Core Web Vitals for mobile performance",
                description="Address LCP and FCP issues on mobile to improve loading experience.",
                effort=EffortLevel.HIGH,
                impact=ImpactLevel.LOW,
                quadrant=StrategicQuadrant.TRANSFORMATIONAL,
                rationale="Technical debt reduction with long-term SEO and UX benefits.",
                related_gaps=["performance_technical_health"],
            ),
        ],
    )

    analysis = AnalysisRun(
        run_id="test-phase1-001",
        created_at=datetime.now(timezone.utc),
        primary_site=primary_site,
        competitors=[],
        ai_analysis=ai_analysis,
    )

    return analysis, screenshot_data_uri


def build_subdim_observations() -> dict[str, dict[str, str]]:
    """Create mock sub-dimension observation text for testing."""
    return {
        "performance_technical_health": {
            "speed_performance": (
                "Page load times average 3.2 seconds on mobile, notably above the recommended 2.5-second "
                "threshold. Large unoptimized images and render-blocking scripts contribute to the delay."
            ),
            "code_quality": (
                "HTML and CSS are well-structured with semantic markup. Minor issues with unused CSS "
                "and JavaScript bundles that could be tree-shaken for better performance."
            ),
            "security_ssl": (
                "SSL certificate is properly configured with HTTPS enforced across all pages. Security "
                "headers are mostly in place, though Content-Security-Policy could be tightened."
            ),
            "core_web_vitals": (
                "CLS score is excellent at near-zero, indicating strong visual stability. However, LCP "
                "at 4.1s on mobile significantly exceeds the 2.5s 'good' threshold."
            ),
        },
        "seo_ai_visibility": {
            "on_page_seo": (
                "Title tags and meta descriptions are present on all key pages. H1 usage is consistent, "
                "though some interior pages could benefit from more descriptive heading hierarchies."
            ),
            "technical_seo": (
                "XML sitemap is properly configured and submitted. Robots.txt is clean. Canonical tags "
                "are correctly implemented, preventing duplicate content issues."
            ),
            "ai_visibility": (
                "Limited structured context for AI crawlers. Adding FAQ schema and clearer entity "
                "definitions would improve how LLMs understand and cite the site's content."
            ),
            "structured_data": (
                "Basic Organization schema is present but incomplete. Missing Service, FAQ, and "
                "BreadcrumbList schemas that would enhance search result presentation."
            ),
        },
        "brand_messaging": {
            "value_proposition": (
                "The homepage hero leads with 'We build digital experiences' — a capability statement "
                "that could belong to any agency. Reframing around client outcomes would create immediate differentiation."
            ),
            "brand_differentiation": (
                "Matic's dual expertise in brand strategy and technical execution is genuinely rare. "
                "The portfolio demonstrates this clearly, but the messaging buries the lead."
            ),
            "brand_voice_messaging": (
                "Copy alternates between technical jargon and generic marketing language. A consistent "
                "voice that bridges both worlds would reinforce the brand's unique positioning."
            ),
            "brand_visual_language": (
                "The visual system is clean and modern with strong typography choices. Color palette "
                "is professional but could use more intentional brand-specific elements."
            ),
        },
        "experience_design": {
            "interface_design": (
                "Visual hierarchy is well-executed with clear content grouping and intentional whitespace. "
                "Typography scales and spacing create a polished, premium feel."
            ),
            "content_taxonomy": (
                "Micro-interactions are present but subtle. Hover states and transitions add polish "
                "without distracting from the content."
            ),
            "navigation_architecture": (
                "Primary navigation is clean and logical. The limited menu items reduce cognitive load, "
                "though deeper content requires more clicks to discover."
            ),
            "responsiveness": (
                "Mobile layout adapts well with proper breakpoints. Touch targets are appropriately sized "
                "and spacing adjusts cleanly across viewport widths."
            ),
        },
        "conversion_strategy": {
            "call_to_action_logic": (
                "CTAs default to generic 'Learn More' and 'Get in Touch' language. More specific, "
                "outcome-focused actions would improve click-through rates."
            ),
            "funnel_design": (
                "The path from homepage to contact is clear but passive. No progressive engagement "
                "mechanisms guide visitors deeper into the funnel."
            ),
            "trust_signals": (
                "Client logos and testimonials exist but lack prominence. Case studies with measurable "
                "results would significantly strengthen social proof."
            ),
            "lead_capture_form_design": (
                "The contact form is straightforward but offers only one conversion point. Adding "
                "lower-commitment options like newsletter signup could capture more leads."
            ),
        },
    }


def main():
    no_screenshot = "--no-screenshot" in sys.argv
    subdim_obs = build_subdim_observations()
    assets_dir = project_root / "assets"

    if no_screenshot:
        print("Mode: NO SCREENSHOT (testing clean fallback)")
        output_path = project_root / "test_output_no_screenshot.pdf"
    else:
        print("Mode: WITH SCREENSHOT (fetching live image)")
        output_path = project_root / "test_output_phase1.pdf"

    analysis, screenshot_data_uri = build_sample_analysis(
        include_screenshot=not no_screenshot,
    )

    print(f"\nGenerating test PDF...")
    print(f"  Output: {output_path}")
    print(f"  Assets: {assets_dir}")
    print(f"  Screenshot: {'yes' if screenshot_data_uri else 'none'}")

    result = render_pdf(
        analysis,
        output_path,
        assets_dir=str(assets_dir),
        analyst_name="Josh Fuller",
        project_title="Matic Digital",
        subdim_observations=subdim_obs,
        screenshot_data_uri=screenshot_data_uri,
    )

    print(f"\n✓ PDF generated successfully!")
    print(f"  Path: {result}")
    print(f"  Size: {result.stat().st_size:,} bytes")
    print(f"\nOpen with: open '{result}'")


if __name__ == "__main__":
    main()
