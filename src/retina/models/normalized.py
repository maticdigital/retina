"""Unified data schema for Retina site analysis.

All API responses are normalized into these Pydantic models.
The schema supports both automated (API-derived) and analyst-scored lenses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DeviceStrategy(str, Enum):
    MOBILE = "mobile"
    DESKTOP = "desktop"


class ScoringLensType(str, Enum):
    PERFORMANCE_TECHNICAL = "performance_technical_health"
    SEO_AI_VISIBILITY = "seo_ai_visibility"
    BRAND_MESSAGING = "brand_messaging"
    EXPERIENCE_DESIGN = "experience_design"
    CONVERSION_STRATEGY = "conversion_strategy"


# ---------------------------------------------------------------------------
# Performance (from PageSpeed Insights)
# ---------------------------------------------------------------------------


class CoreWebVitals(BaseModel):
    """Core Web Vitals metrics extracted from Lighthouse."""

    largest_contentful_paint_ms: float | None = None
    first_contentful_paint_ms: float | None = None
    cumulative_layout_shift: float | None = None
    interaction_to_next_paint_ms: float | None = None
    total_blocking_time_ms: float | None = None
    speed_index_ms: float | None = None


class LighthouseScores(BaseModel):
    """Raw 0-100 scores from Lighthouse categories."""

    performance: float | None = None
    accessibility: float | None = None
    best_practices: float | None = None
    seo: float | None = None


class AuditItem(BaseModel):
    """A single Lighthouse audit finding."""

    id: str
    title: str
    description: str
    score: float | None = None  # 0-1 scale, None if informational
    display_value: str | None = None
    category: str  # which Lighthouse category this belongs to
    weight: float = 0.0  # weight within that category


class PerformanceData(BaseModel):
    """Performance data for a single device strategy (mobile or desktop)."""

    strategy: DeviceStrategy
    lighthouse_scores: LighthouseScores
    core_web_vitals: CoreWebVitals
    audits: list[AuditItem] = Field(default_factory=list)
    fetch_time: datetime | None = None


# ---------------------------------------------------------------------------
# Tech Stack (from BuiltWith)
# ---------------------------------------------------------------------------


class Technology(BaseModel):
    """A single detected technology."""

    name: str
    description: str | None = None
    link: str | None = None
    categories: list[str] = Field(default_factory=list)
    tag: str | None = None  # BuiltWith tag grouping


class TechStackData(BaseModel):
    """Complete technology profile for a domain."""

    technologies: list[Technology] = Field(default_factory=list)
    meta: dict[str, str] = Field(default_factory=dict)
    social_profiles: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Screenshots
# ---------------------------------------------------------------------------


class ScreenshotData(BaseModel):
    """Paths to captured screenshots for a site."""

    full_page: str | None = None  # path to full-page screenshot
    viewport: str | None = None  # path to above-the-fold screenshot
    analyst_overrides: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


class LensScore(BaseModel):
    """Score for a single scoring lens (0-20 points)."""

    lens: ScoringLensType
    score: float = Field(ge=0, le=20)
    breakdown: dict[str, float] = Field(default_factory=dict)
    notes: str | None = None
    is_automated: bool = True


class RetinaScore(BaseModel):
    """Composite 100-point score across all 5 lenses."""

    lens_scores: list[LensScore] = Field(default_factory=list)
    total: float = Field(ge=0, le=100, default=0)

    def compute_total(self) -> float:
        """Sum all lens scores and update the total."""
        self.total = round(sum(ls.score for ls in self.lens_scores), 2)
        return self.total


# ---------------------------------------------------------------------------
# Top-Level Report Models
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# AI Analysis (from Claude API)
# ---------------------------------------------------------------------------


class EffortLevel(str, Enum):
    LOW = "low"
    HIGH = "high"


class ImpactLevel(str, Enum):
    LOW = "low"
    HIGH = "high"


class StrategicQuadrant(str, Enum):
    NO_BRAINER = "no_brainer"          # low effort, high impact
    GROWTH_MOVE = "growth_move"         # high effort, high impact
    QUICK_WIN = "quick_win"             # low effort, lower impact
    TRANSFORMATIONAL = "transformational"  # high effort, long-term payoff


class CompetitiveDimension(BaseModel):
    """How the primary site compares on a specific dimension."""

    dimension: str
    primary_score: float | None = None
    competitor_scores: dict[str, float | None] = Field(default_factory=dict)
    assessment: str  # over-performs, under-performs, on-par
    detail: str


class GapItem(BaseModel):
    """A specific gap or missed opportunity identified in the analysis."""

    title: str
    description: str
    severity: str  # critical, moderate, minor
    related_dimension: str


class Recommendation(BaseModel):
    """A single prioritized recommendation from the AI analysis."""

    title: str
    description: str
    effort: EffortLevel
    impact: ImpactLevel
    quadrant: StrategicQuadrant
    rationale: str
    related_gaps: list[str] = Field(default_factory=list)
    estimated_score_impact: str | None = None


class AIAnalysis(BaseModel):
    """Complete AI-generated competitive analysis."""

    executive_summary: str
    competitive_comparison: list[CompetitiveDimension] = Field(default_factory=list)
    gaps: list[GapItem] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    model_used: str | None = None
    tokens_used: int | None = None


# ---------------------------------------------------------------------------
# Top-Level Report Models
# ---------------------------------------------------------------------------


class SiteReport(BaseModel):
    """Complete normalized report for a single URL."""

    url: str
    normalized_url: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    performance: list[PerformanceData] = Field(default_factory=list)
    tech_stack: TechStackData | None = None
    screenshots: ScreenshotData | None = None
    retina_score: RetinaScore = Field(default_factory=RetinaScore)
    raw_responses: dict[str, dict] = Field(default_factory=dict)


class AnalysisRun(BaseModel):
    """A complete analysis run: primary site + competitors."""

    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    primary_site: SiteReport
    competitors: list[SiteReport] = Field(default_factory=list)
    ai_analysis: AIAnalysis | None = None
