"""Human-readable explanations for metrics, audits, and technology findings."""

from __future__ import annotations

from app.components.styles import COLORS, hex_to_rgba

# ---------------------------------------------------------------------------
# Core Web Vitals — what each metric is, thresholds, and why it matters
# ---------------------------------------------------------------------------
CWV_EXPLANATIONS: dict[str, dict] = {
    "largest_contentful_paint_ms": {
        "name": "Largest Contentful Paint (LCP)",
        "unit": "ms",
        "good": 2500,
        "poor": 4000,
        "what": "How long the largest visible element takes to render — the moment visitors perceive the page as loaded.",
        "why": "LCP is the primary signal for perceived load speed. Pages loading under 2.5s retain visitors; above 4s, bounce rates climb sharply and Google signals a poor experience.",
    },
    "first_contentful_paint_ms": {
        "name": "First Contentful Paint (FCP)",
        "unit": "ms",
        "good": 1800,
        "poor": 3000,
        "what": "Time until the first text or image appears on screen — the earliest visual feedback visitors receive.",
        "why": "FCP sets visitor expectations. Under 1.8s signals a responsive experience; above 3s creates friction that reduces the likelihood visitors stay and take action.",
    },
    "cumulative_layout_shift": {
        "name": "Cumulative Layout Shift (CLS)",
        "unit": "",
        "good": 0.1,
        "poor": 0.25,
        "what": "Measures unexpected movement of visible content during loading — elements shifting position as the page renders.",
        "why": "Layout shifts erode visitor trust by causing mis-clicks and a disorienting experience. Under 0.1 is the threshold for stability; above 0.25 creates meaningful conversion friction.",
    },
    "total_blocking_time_ms": {
        "name": "Total Blocking Time (TBT)",
        "unit": "ms",
        "good": 200,
        "poor": 600,
        "what": "Total time the main thread was blocked, preventing the page from responding to user input.",
        "why": "High TBT makes the page feel frozen — buttons don't respond, forms lag. Under 200ms delivers a responsive experience; above 600ms creates friction that directly impacts conversion pathways.",
    },
    "speed_index_ms": {
        "name": "Speed Index",
        "unit": "ms",
        "good": 3400,
        "poor": 5800,
        "what": "How quickly the visible area of the page is populated with content — capturing the overall visual loading experience.",
        "why": "Speed Index reflects the visitor's perception of how fast a page loads. Under 3.4s positions the site competitively; above 5.8s signals a loading experience that reduces engagement and visitor confidence.",
    },
    "interaction_to_next_paint_ms": {
        "name": "Interaction to Next Paint (INP)",
        "unit": "ms",
        "good": 200,
        "poor": 500,
        "what": "How quickly the page responds to user interactions — clicks, taps, and key presses.",
        "why": "INP is Google's core responsiveness metric. Under 200ms delivers the instant feedback visitors expect; above 500ms creates noticeable lag on buttons, forms, and navigation that directly impacts conversion rates.",
    },
}

# ---------------------------------------------------------------------------
# Lighthouse category labels
# ---------------------------------------------------------------------------
CATEGORY_LABELS = {
    "performance": "Performance",
    "accessibility": "Accessibility",
    "seo": "SEO",
    "best-practices": "Best Practices",
}

# ---------------------------------------------------------------------------
# Technology category explanations
# ---------------------------------------------------------------------------
TECH_EXPLANATIONS: dict[str, str] = {
    "cms": "Content management system powering the site. The CMS choice directly impacts maintenance velocity, security posture, and the ability to iterate on content and conversion pathways.",
    "hosting": "Infrastructure where the site is deployed. Hosting architecture affects page speed, uptime reliability, and geographic performance — all factors in visitor experience and search visibility.",
    "cdn": "Content delivery network distributing assets from edge locations worldwide. A well-configured CDN reduces latency for global visitors and strengthens competitive positioning on load speed.",
    "javascript frameworks": "Client-side framework driving interactivity. Framework choice affects bundle size, time-to-interactive, and the development team's ability to ship conversion-focused features.",
    "web frameworks": "Server-side framework defining the site's architecture. Determines API capabilities, scalability under traffic growth, and the foundation for future digital initiatives.",
    "analytics": "Visitor analytics and measurement tools. Provides the intelligence needed to optimize conversion pathways, though each tool adds page weight that can impact performance scores.",
    "ssl": "SSL/TLS certificate provider securing the site with HTTPS. Essential for visitor trust signals, data protection, and search engine ranking — Google treats HTTPS as a baseline requirement.",
    "widgets": "Third-party widgets and integrations extending site functionality. Each widget adds capability but also page weight — the balance directly affects performance and visitor experience.",
    "web servers": "Web server software handling incoming requests. Server choice and configuration affect caching efficiency, connection handling, and the site's ability to deliver fast responses under load.",
    "tag managers": "Tag management system centralizing third-party script deployment. Streamlines marketing and analytics implementation, but misconfigured tag managers are a common source of performance degradation.",
    "advertising": "Ad networks and tracking integrations. Revenue-generating but often the largest contributor to page weight and performance friction — requires careful balancing against visitor experience.",
    "payment": "Payment processing integrations enabling transactions. Critical for conversion completion — the payment experience directly impacts cart abandonment rates and revenue capture.",
    "email": "Email service providers for marketing automation and transactional communications. The email platform powers lead nurturing sequences and post-conversion engagement.",
    "marketing automation": "Marketing automation tools for lead nurturing, campaign management, and conversion tracking. These systems connect the website experience to the broader revenue pipeline.",
}

# ---------------------------------------------------------------------------
# SEO-specific audit explanations
# ---------------------------------------------------------------------------
SEO_AUDIT_EXPLANATIONS: dict[str, dict[str, str]] = {
    "document-title": {
        "name": "Page Title",
        "why": "The title tag is the most visible on-page SEO signal — it appears directly in search results and browser tabs. A well-crafted title drives click-through rates and strengthens search positioning.",
    },
    "meta-description": {
        "name": "Meta Description",
        "why": "The meta description appears as the snippet beneath the title in search results. A compelling, specific description directly improves click-through rates and competitive positioning in search.",
    },
    "canonical": {
        "name": "Canonical URL",
        "why": "The canonical tag tells search engines which version of a page is authoritative, preventing duplicate content from diluting search visibility and crawl efficiency.",
    },
    "hreflang": {
        "name": "Hreflang Tags",
        "why": "Signals language and regional targeting to search engines. For multi-language sites, missing hreflang tags reduce the site's ability to surface the right content to the right audience.",
    },
    "viewport": {
        "name": "Viewport Meta Tag",
        "why": "Required for proper mobile rendering under Google's mobile-first indexing. Without it, the page displays at desktop width on mobile devices — creating significant friction for the majority of visitors.",
    },
    "tap-targets": {
        "name": "Tap Target Sizing",
        "why": "Touch targets below the 48×48px threshold create friction for mobile visitors, reducing the likelihood they complete conversion actions. Mobile usability directly impacts engagement and search ranking.",
    },
    "font-size": {
        "name": "Readable Font Size",
        "why": "Text below 12px on mobile forces visitors to pinch-zoom, creating friction that increases bounce rates. Readable text is a baseline expectation for the mobile visitor experience.",
    },
    "robots-txt": {
        "name": "robots.txt",
        "why": "Controls which pages search engines and AI crawlers can access. Without robots.txt, there is no mechanism to manage crawl behavior — limiting the site's ability to direct search engine attention to high-value pages.",
    },
    "is-crawlable": {
        "name": "Crawlability",
        "why": "If a page blocks crawlers, it will not appear in search results regardless of how well-optimized the content is. Crawlability is the foundational requirement for search visibility.",
    },
    "crawlable-anchors": {
        "name": "Crawlable Links",
        "why": "Links must use standard HTML anchors for search engines to follow and discover content. Non-standard link patterns create dead ends that limit how deeply search engines index the site.",
    },
    "http-status-code": {
        "name": "HTTP Status Code",
        "why": "Pages must return 200 OK to be indexed. Error responses (4xx, 5xx) prevent indexing and waste the site's crawl budget — reducing the search engine's ability to discover and rank content.",
    },
    "image-alt": {
        "name": "Image Alt Text",
        "why": "Alt text helps search engines understand image content and is essential for accessibility. Missing alt text limits image search visibility and creates barriers for visitors using screen readers.",
    },
    "heading-order": {
        "name": "Heading Hierarchy",
        "why": "Proper heading structure (H1→H2→H3) helps search engines and AI understand content organization. A clear hierarchy strengthens the site's ability to win featured snippets and structured answers.",
    },
    "link-text": {
        "name": "Descriptive Link Text",
        "why": "Link text tells search engines what the destination page is about. Generic text like 'click here' wastes a ranking signal and reduces the visitor's confidence in where a link leads.",
    },
    "html-has-lang": {
        "name": "HTML Language Attribute",
        "why": "The lang attribute helps search engines and screen readers identify the page's language for proper indexing and pronunciation — a small implementation detail with broad visibility and accessibility impact.",
    },
    "structured-data-item": {
        "name": "Schema Markup",
        "why": "Structured data enables rich results in search — star ratings, pricing, FAQs, and more. Sites with schema markup significantly improve click-through rates and visibility in AI-generated answers.",
    },
}


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
def cwv_metric_html(
    key: str,
    value: float | None,
) -> str:
    """Render a CWV metric card with explanation."""
    info = CWV_EXPLANATIONS.get(key, {})
    name = info.get("name", key.replace("_", " ").title())
    good = info.get("good", 0)
    poor = info.get("poor", 0)
    what = info.get("what", "")
    why = info.get("why", "")
    unit = info.get("unit", "ms")

    if value is None:
        return f"""
<div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
            border-radius:10px;padding:1rem;box-shadow:{COLORS['shadow']};">
  <div style="font-weight:600;color:{COLORS['text']};font-size:0.9rem;margin-bottom:4px;">{name}</div>
  <div style="color:{COLORS['text_dim']};font-size:1.5rem;font-weight:700;">—</div>
  <div style="color:{COLORS['text_dim']};font-size:0.78rem;margin-top:6px;">{what}</div>
</div>"""

    if unit == "":
        display = f"{value:.3f}"
    elif value >= 1000:
        display = f"{value / 1000:.1f}s"
    else:
        display = f"{value:.0f}ms"

    is_good = (value <= good) if unit != "" else (value <= good)
    is_poor = (value >= poor) if unit != "" else (value >= poor)

    if is_good:
        color = COLORS["success"]
        label = "Good"
    elif is_poor:
        color = COLORS["error"]
        label = "Poor"
    else:
        color = COLORS["warning"]
        label = "Needs Improvement"

    return f"""
<div style="background:{COLORS['bg_card']};border:1px solid {hex_to_rgba(color, 0.25)};
            border-radius:10px;padding:1rem;box-shadow:{COLORS['shadow']};">
  <div style="font-weight:600;color:{COLORS['text']};font-size:0.85rem;margin-bottom:4px;">{name}</div>
  <div style="color:{color};font-size:1.6rem;font-weight:700;">{display}
    <span style="font-size:0.7rem;font-weight:500;margin-left:4px;">{label}</span>
  </div>
  <div style="color:{COLORS['text_dim']};font-size:0.75rem;margin-top:6px;">{why}</div>
</div>"""


def audit_card_html(
    audit_id: str,
    title: str,
    description: str,
    score: float | None,
    display_value: str | None,
    weight: float,
    category: str,
) -> str:
    """Render a single audit finding as a rich card."""
    if score is None:
        return ""

    if score >= 0.9:
        color = COLORS["success"]
        icon = "✓"
    elif score >= 0.5:
        color = COLORS["warning"]
        icon = "◐"
    else:
        color = COLORS["error"]
        icon = "✗"

    # Use SEO_AUDIT_EXPLANATIONS for known audits, else use description
    known = SEO_AUDIT_EXPLANATIONS.get(audit_id, {})
    explanation = known.get("why", description[:150] if description else "")
    display_name = known.get("name", title)

    value_html = ""
    if display_value:
        value_html = f"<span style='color:{COLORS['text_dim']};font-size:0.8rem;margin-left:8px;'>{display_value}</span>"

    return f"""
<div style="padding:10px 14px;margin:4px 0;background:{hex_to_rgba(color, 0.05)};
            border-left:3px solid {color};border-radius:6px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="color:{color};font-weight:600;font-size:0.85rem;">{icon} {display_name}{value_html}</span>
    <span style="color:{COLORS['text_dim']};font-size:0.72rem;">Weight: {weight:.0f}</span>
  </div>
  <div style="color:{COLORS['text_muted']};font-size:0.78rem;margin-top:4px;">{explanation}</div>
</div>"""


def tech_card_html(name: str, description: str | None, category: str) -> str:
    """Render a technology finding as a labeled card."""
    cat_lower = category.lower() if category else ""
    cat_explanation = TECH_EXPLANATIONS.get(cat_lower, "")

    desc_text = description or cat_explanation or ""
    if len(desc_text) > 120:
        desc_text = desc_text[:117] + "..."

    return f"""
<div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
            border-radius:8px;padding:10px 14px;box-shadow:{COLORS['shadow']};">
  <div style="font-weight:600;color:{COLORS['text']};font-size:0.85rem;">{name}</div>
  <div style="color:{COLORS['accent']};font-size:0.7rem;text-transform:uppercase;
              letter-spacing:0.04em;margin:2px 0 4px;">{category}</div>
  <div style="color:{COLORS['text_dim']};font-size:0.75rem;line-height:1.4;">{desc_text}</div>
</div>"""


def blended_score_html(
    label: str,
    mobile: float | None,
    desktop: float | None,
    threshold: float = 15.0,
) -> str:
    """Show a blended score — mobile primary, flag desktop only if gap > threshold."""
    if mobile is None and desktop is None:
        return f"<span style='color:{COLORS['text_dim']};'>—</span>"

    primary = mobile if mobile is not None else desktop
    color = COLORS["success"] if primary >= 90 else (COLORS["warning"] if primary >= 50 else COLORS["error"])

    gap_html = ""
    if mobile is not None and desktop is not None:
        gap = abs(desktop - mobile)
        if gap > threshold:
            gap_html = (
                f"<span style='color:{COLORS['text_dim']};font-size:0.78rem;margin-left:8px;'>"
                f"Mobile: {mobile:.0f} | Desktop: {desktop:.0f} — significant gap</span>"
            )

    return f"""
<span style="color:{color};font-size:1.5rem;font-weight:700;">{primary:.0f}</span>
<span style="color:{COLORS['text_dim']};font-size:0.78rem;">/ 100</span>
{gap_html}"""


def warning_banner_html(title: str, message: str) -> str:
    """Prominent warning banner for missing critical items."""
    return f"""
<div style="padding:12px 16px;margin:10px 0;background:{hex_to_rgba(COLORS['warning'], 0.1)};
            border:1px solid {hex_to_rgba(COLORS['warning'], 0.3)};border-radius:8px;">
  <div style="color:{COLORS['warning']};font-weight:600;font-size:0.9rem;">⚠ {title}</div>
  <div style="color:{COLORS['text_muted']};font-size:0.85rem;margin-top:4px;">{message}</div>
</div>"""


def error_banner_html(title: str, message: str) -> str:
    """Prominent error banner for critical issues."""
    return f"""
<div style="padding:12px 16px;margin:10px 0;background:{hex_to_rgba(COLORS['error'], 0.08)};
            border:1px solid {hex_to_rgba(COLORS['error'], 0.2)};border-radius:8px;">
  <div style="color:{COLORS['error']};font-weight:600;font-size:0.9rem;">✗ {title}</div>
  <div style="color:{COLORS['text_muted']};font-size:0.85rem;margin-top:4px;">{message}</div>
</div>"""
