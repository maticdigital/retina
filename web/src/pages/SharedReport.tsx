import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { verifyShareToken, ApiError } from '../api';
import type { SharedProjectData, SharedLensData, LensScore, RecommendationQuadrant, RecommendationItem, TechStack } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import { useIsMobile } from '../hooks/useIsMobile';

import performanceIcon from '../assets/performance_icon.svg';
import seoIcon from '../assets/seo_icon.svg';
import brandIcon from '../assets/brand_icon.svg';
import experienceIcon from '../assets/experience_icon.svg';
import conversionIcon from '../assets/conversion_icon.svg';

/* ── Constants ────────────────────────────────────── */

const LENS_COLORS: Record<string, string> = {
  performance_technical_health: '#076EFF',
  seo_ai_visibility: '#00C864',
  brand_messaging: '#9B59B6',
  experience_design: '#E74C3C',
  conversion_strategy: '#FF8C00',
};

const LENS_ICONS: Record<string, string> = {
  performance_technical_health: performanceIcon,
  seo_ai_visibility: seoIcon,
  brand_messaging: brandIcon,
  experience_design: experienceIcon,
  conversion_strategy: conversionIcon,
};

const LENS_DEFINITIONS: Record<string, string> = {
  performance_technical_health: 'Speed, stability, and technical foundation of the site',
  seo_ai_visibility: 'How findable and readable the site is to search engines and AI',
  brand_messaging: 'How clearly the site communicates who it\'s for and why it matters',
  experience_design: 'How intuitive, modern, and intentional the site feels to visitors',
  conversion_strategy: 'How effectively the site turns attention into action',
};

const SUB_DIM_MAX: Record<string, Record<string, number>> = {
  brand_messaging: {
    brand_visual_language: 5, brand_voice_messaging: 5,
    value_proposition: 5, brand_differentiation: 5,
  },
  experience_design: {
    interface_design: 5, content_taxonomy: 5,
    navigation_architecture: 5, responsiveness: 5,
  },
  conversion_strategy: {
    call_to_action_logic: 5, lead_capture_form_design: 5,
    trust_signals: 5, funnel_design: 5,
  },
};

/* ── Password Entry ───────────────────────────────── */

function PasswordGate({ token, onVerified }: { token: string; onVerified: (data: SharedProjectData) => void }) {
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await verifyShareToken(token, password);
      onVerified(data);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        if (err.status === 404) setError('This report is no longer available');
        else if (err.status === 401) setError('Incorrect password');
        else setError(err.message);
      } else {
        setError('Something went wrong');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={gateStyles.page}>
      <div style={gateStyles.card}>
        <div style={gateStyles.logoWrap}>
          <svg width="40" height="40" viewBox="0 0 664 664" fill="none">
            <path
              d="M332 20C149 20 0 169 0 352h87c0-135 110-245 245-245s245 110 245 245h87C664 169 515 20 332 20Zm101 332c0-56-45-101-101-101s-101 45-101 101 45 101 101 101 101-45 101-101Zm87 0c0 104-85 188-188 188S144 456 144 352s85-188 188-188 188 85 188 188Zm-130 0c0 32-26 58-58 58s-58-26-58-58 26-58 58-58 58 26 58 58Z"
              fill={color.text}
            />
          </svg>
          <div style={gateStyles.logoText}>
            <span style={gateStyles.logoLine}>Matic</span>
            <span style={gateStyles.logoLine}>Retina</span>
          </div>
        </div>

        <h1 style={gateStyles.heading}>Enter password to view report</h1>

        {error && <div style={gateStyles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={gateStyles.form}>
          <label style={gateStyles.label}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter report password"
              required
              style={gateStyles.input}
              autoFocus
            />
          </label>
          <button type="submit" disabled={loading} style={gateStyles.button}>
            {loading ? 'Verifying...' : 'View Report'}
          </button>
        </form>
      </div>
    </div>
  );
}

const gateStyles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: color.bgPage,
    padding: space.lg,
  },
  card: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    padding: space.xl,
    boxShadow: color.shadowMd,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  logoWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: space.xs,
    marginBottom: space.lg,
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
    lineHeight: 1.15,
  },
  logoLine: {
    fontFamily: font.family,
    fontWeight: font.weightBold,
    fontSize: font.sizeLg,
    color: color.text,
  },
  heading: {
    margin: 0,
    marginBottom: space.lg,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeMd,
    color: color.textMuted,
    textAlign: 'center',
  },
  error: {
    width: '100%',
    padding: space.sm,
    marginBottom: space.md,
    borderRadius: radius.md,
    backgroundColor: '#FEE2E2',
    color: color.error,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    textAlign: 'center',
  },
  form: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: space.md,
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: space.xxs,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    color: color.text,
  },
  input: {
    padding: `${space.sm} ${space.md}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    fontFamily: font.family,
    fontSize: font.sizeBase,
    color: color.text,
    outline: 'none',
    boxSizing: 'border-box' as const,
  },
  button: {
    marginTop: space.xs,
    padding: `${space.sm} ${space.md}`,
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeBase,
    fontWeight: font.weightSemibold,
    cursor: 'pointer',
  },
};

/* ══════════════════════════════════════════════════════
   SMALL HELPERS — mirrors from LensDetail & Report
   ══════════════════════════════════════════════════════ */

function humanizeKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

type StatusLevel = 'good' | 'warning' | 'poor';

function statusDot(level: StatusLevel): React.CSSProperties {
  const colors = { good: '#22C55E', warning: '#F59E0B', poor: '#EF4444' };
  return { width: 10, height: 10, borderRadius: '50%', backgroundColor: colors[level], display: 'inline-block', flexShrink: 0 };
}

function cwvStatus(metric: string, value: number | null): StatusLevel {
  if (value === null) return 'poor';
  const thresholds: Record<string, [number, number]> = {
    lcp: [2500, 4000], fcp: [1800, 3000], cls: [0.1, 0.25], tbt: [200, 600],
  };
  const t = thresholds[metric];
  if (!t) return 'warning';
  return value <= t[0] ? 'good' : value <= t[1] ? 'warning' : 'poor';
}

function lighthouseScoreColor(score: number): string {
  if (score >= 90) return '#22C55E';
  if (score >= 50) return '#F59E0B';
  return '#EF4444';
}

function formatMs(ms: number | null): string {
  if (ms === null) return '—';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatCLS(value: number | null): string {
  if (value === null) return '—';
  return value.toFixed(3);
}

function scoreInterpretation(score: number): string {
  if (score >= 90) return 'Strong performance';
  if (score >= 70) return 'Solid, with room to improve';
  if (score >= 50) return 'Needs improvement';
  return 'Needs significant improvement';
}

function Tooltip({ text }: { text: string }) {
  const [show, setShow] = useState(false);
  return (
    <span
      style={{ position: 'relative', display: 'inline-flex', cursor: 'help' }}
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="2" style={{ opacity: 0.6 }}>
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
      {show && (
        <div style={{
          position: 'absolute', bottom: 'calc(100% + 8px)', left: '50%',
          transform: 'translateX(-50%)', background: '#1a1a1a', color: '#fff',
          padding: `${space.xs} ${space.sm}`, borderRadius: radius.md,
          fontSize: font.sizeXs, fontFamily: font.family, lineHeight: 1.4,
          width: 220, zIndex: 100, pointerEvents: 'none', whiteSpace: 'normal',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        }}>
          {text}
        </div>
      )}
    </span>
  );
}

const CWV_TOOLTIPS: Record<string, string> = {
  lcp: 'Largest Contentful Paint measures how long it takes for the biggest visible element to load. Under 2.5 seconds is considered fast.',
  fcp: 'First Contentful Paint is how quickly the first text or image appears on screen. Under 1.8 seconds is considered fast.',
  cls: 'Cumulative Layout Shift measures how much the page jumps around while loading. A score under 0.1 means the page is visually stable.',
  tbt: 'Total Blocking Time measures how long the page is unresponsive to clicks. Under 200ms is considered good.',
};

const LIGHTHOUSE_TOOLTIPS: Record<string, string> = {
  performance: 'Overall page speed score based on Core Web Vitals and load metrics.',
  accessibility: 'How usable the site is for people with disabilities — screen readers, contrast, keyboard navigation.',
  best_practices: 'Security, modern web standards, and code quality indicators.',
  seo: 'How well the page is structured for search engine crawling and indexing.',
};

/* ── Donut Chart (from Report.tsx) ──────────────── */

function ScoreDonut({ lensScores, retinaScore }: { lensScores: LensScore[]; retinaScore: number | null }) {
  const size = 180;
  const strokeWidth = 22;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const totalMax = lensScores.reduce((s, l) => s + l.max_score, 0);
  let offset = 0;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#E5E7EB" strokeWidth={strokeWidth} />
      {lensScores.map((lens) => {
        const segmentFraction = lens.max_score / totalMax;
        const segmentLength = circumference * segmentFraction;
        const gap = 3;
        const filledFraction = lens.score !== null ? lens.score / lens.max_score : 0;
        const filledLength = Math.max(0, (segmentLength - gap) * filledFraction);
        const dashArray = `${filledLength} ${circumference - filledLength}`;
        const dashOffset = -(offset + gap / 2);
        offset += segmentLength;
        return (
          <circle key={lens.lens_id} cx={size / 2} cy={size / 2} r={r} fill="none"
            stroke={lens.score !== null ? LENS_COLORS[lens.lens_id] || color.textDim : '#E5E7EB'}
            strokeWidth={strokeWidth} strokeDasharray={dashArray} strokeDashoffset={dashOffset}
            strokeLinecap="round" transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        );
      })}
      <text x={size / 2} y={size / 2 - 6} textAnchor="middle" style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: '2rem' }} fill={color.text}>
        {retinaScore !== null ? Math.round(retinaScore) : '—'}
      </text>
      <text x={size / 2} y={size / 2 + 16} textAnchor="middle" style={{ fontFamily: font.family, fontSize: font.sizeSm }} fill={color.textMuted}>
        /100
      </text>
    </svg>
  );
}

/* ── Lens Donut (from LensDetail.tsx) ──────────── */

function LensDonut({ score, maxScore, lensColor, diameter = 80 }: { score: number | null; maxScore: number; lensColor: string; diameter?: number }) {
  const strokeWidth = diameter * 0.1;
  const r = (diameter - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;
  const fraction = score !== null ? Math.max(0, Math.min(score / maxScore, 1)) : 0;
  const filledLength = circumference * fraction;
  const scoreFontSize = diameter * 0.28;
  const maxFontSize = diameter * 0.12;
  return (
    <svg width={diameter} height={diameter} viewBox={`0 0 ${diameter} ${diameter}`} style={{ flexShrink: 0 }}>
      <circle cx={diameter / 2} cy={diameter / 2} r={r} fill="none" stroke="#E5E7EB" strokeWidth={strokeWidth} />
      {score !== null && (
        <circle cx={diameter / 2} cy={diameter / 2} r={r} fill="none"
          stroke={lensColor} strokeWidth={strokeWidth}
          strokeDasharray={`${filledLength} ${circumference - filledLength}`}
          strokeDashoffset={circumference * 0.25} strokeLinecap="round"
          transform={`rotate(-90 ${diameter / 2} ${diameter / 2})`}
          style={{ transition: 'stroke-dasharray 0.6s ease' }}
        />
      )}
      <text x={diameter / 2} y={diameter / 2 - diameter * 0.04} textAnchor="middle"
        style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: `${scoreFontSize}px` }} fill={color.text}>
        {score !== null ? (score % 1 === 0 ? score : score.toFixed(1)) : '—'}
      </text>
      <text x={diameter / 2} y={diameter / 2 + diameter * 0.14} textAnchor="middle"
        style={{ fontFamily: font.family, fontSize: `${maxFontSize}px` }} fill={color.textMuted}>
        /{maxScore}
      </text>
    </svg>
  );
}

function normalizeItem(item: string | RecommendationItem): RecommendationItem {
  if (typeof item === 'string') {
    try {
      const parsed = JSON.parse(item);
      if (typeof parsed === 'object' && parsed !== null && 'title' in parsed) return parsed as RecommendationItem;
    } catch { /* not JSON */ }
    return { title: item };
  }
  return item;
}

/* ══════════════════════════════════════════════════════
   PERFORMANCE SECTION — read-only mirror of LensDetail
   ══════════════════════════════════════════════════════ */

function SharedPerformanceSection({ lens }: { lens: SharedLensData }) {
  const [techDetailsOpen, setTechDetailsOpen] = useState(false);
  const lhData = lens.lighthouse_data as Record<string, Record<string, unknown>> || {};
  const mobile = lhData.mobile || {};
  const desktop = lhData.desktop || {};
  const cwv = (mobile.core_web_vitals || {}) as Record<string, number | null>;
  const desktopCwv = (desktop.core_web_vitals || {}) as Record<string, number | null>;
  const lhScores = (mobile.lighthouse_scores || {}) as Record<string, number>;
  const lensColor = lens.lens_color;

  // Tech stack by tag
  const bwData = lens.builtwith_data as Record<string, unknown> || {};
  const techs = (bwData.technologies || []) as Array<{ name: string; tag?: string }>;
  const TAG_LABELS: Record<string, string> = {
    cms: 'CMS', framework: 'Framework', analytics: 'Analytics', cdn: 'CDN',
    cdns: 'CDN', hosting: 'Hosting', javascript: 'JavaScript', ssl: 'SSL',
    widgets: 'Widgets', mx: 'Email', ns: 'DNS', ads: 'Advertising',
    mobile: 'Mobile', payment: 'Payment', robots: 'Robots / AI', link: 'Social Links',
  };
  const groups: Record<string, string[]> = {};
  for (const t of techs) {
    const tag = t.tag || 'other';
    const label = TAG_LABELS[tag];
    if (!label) continue;
    groups[label] = groups[label] || [];
    groups[label].push(t.name);
  }

  // Interpretation
  const perfInterp = lens.interpretations.performance as Record<string, unknown> | undefined;
  const narrative = perfInterp?.section_narrative as string | undefined;

  // CWV interpretations
  const cwvInterps = perfInterp?.cwv as Record<string, { what?: string; why?: string; where?: string }> | undefined;
  const CWV_INTERP_MAP: Record<string, string> = {
    lcp: 'largest_contentful_paint_ms', fcp: 'first_contentful_paint_ms',
    cls: 'cumulative_layout_shift', tbt: 'total_blocking_time_ms',
  };

  const headlineScores: { key: string; label: string; tooltip: string }[] = [
    { key: 'performance', label: 'Performance Score', tooltip: LIGHTHOUSE_TOOLTIPS.performance },
    { key: 'accessibility', label: 'Accessibility Score', tooltip: LIGHTHOUSE_TOOLTIPS.accessibility },
    { key: 'seo', label: 'SEO Score', tooltip: LIGHTHOUSE_TOOLTIPS.seo },
    { key: 'best_practices', label: 'Best Practices Score', tooltip: LIGHTHOUSE_TOOLTIPS.best_practices },
  ];

  // Accessibility audit analysis
  const mobileAudits = (mobile.audits || []) as Array<{ id: string; score: number | null; title: string; category: string; description?: string }>;
  const a11yAudits = mobileAudits.filter((a) => a.category === 'accessibility' && a.score !== null && a.score < 1);
  const a11yIssueCount = a11yAudits.length;

  const CRITICAL_A11Y = ['aria-required-attr', 'aria-valid-attr', 'aria-roles', 'button-name', 'input-image-alt', 'label', 'form-field-multiple-labels'];
  const MINOR_A11Y = ['image-alt', 'link-name', 'meta-viewport', 'tabindex'];
  const a11yCats = { critical: [] as string[], moderate: [] as string[], minor: [] as string[] };
  for (const a of a11yAudits) {
    if (CRITICAL_A11Y.includes(a.id)) a11yCats.critical.push(a.title);
    else if (MINOR_A11Y.includes(a.id)) a11yCats.minor.push(a.title);
    else a11yCats.moderate.push(a.title);
  }

  const cwvMetrics = [
    { key: 'lcp', label: 'Largest Contentful Paint', techLabel: 'LCP', value: cwv.largest_contentful_paint_ms ?? null, desktopValue: desktopCwv.largest_contentful_paint_ms ?? null, format: formatMs, thresholdKey: 'lcp', explanation: 'Time for the largest visible element to render. Under 2.5s is good.' },
    { key: 'fcp', label: 'First Contentful Paint', techLabel: 'FCP', value: cwv.first_contentful_paint_ms ?? null, desktopValue: desktopCwv.first_contentful_paint_ms ?? null, format: formatMs, thresholdKey: 'fcp', explanation: 'Time until the first text or image appears. Under 1.8s is good.' },
    { key: 'cls', label: 'Cumulative Layout Shift', techLabel: 'CLS', value: cwv.cumulative_layout_shift ?? null, desktopValue: desktopCwv.cumulative_layout_shift ?? null, format: formatCLS, thresholdKey: 'cls', explanation: 'Measures visual stability during loading. Under 0.1 is good.' },
    { key: 'tbt', label: 'Total Blocking Time', techLabel: 'TBT', value: cwv.total_blocking_time_ms ?? null, desktopValue: desktopCwv.total_blocking_time_ms ?? null, format: formatMs, thresholdKey: 'tbt', explanation: 'Total time the page is unresponsive to input. Under 200ms is good.' },
  ];

  return (
    <>
      {/* Headline Score Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: space.md, marginTop: space.md }} className="mobile-grid-2">
        {headlineScores.map((cat) => {
          const score = Math.round(lhScores[cat.key] ?? 0);
          const bg = lighthouseScoreColor(score);
          const interp = scoreInterpretation(score);
          return (
            <div key={cat.key} style={{
              backgroundColor: color.bgCard, borderRadius: radius.xl, padding: space.lg,
              boxShadow: color.shadow, textAlign: 'center' as const, borderTop: `3px solid ${bg}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: space.xs, marginBottom: space.sm }}>
                <span style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightSemibold, color: color.text }}>{cat.label}</span>
                <Tooltip text={cat.tooltip} />
              </div>
              <div style={{ fontFamily: font.family, fontSize: '2.5rem', fontWeight: font.weightBold, color: bg, lineHeight: 1 }}>{score}</div>
              <div style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, marginTop: space.xs }}>{interp}</div>
            </div>
          );
        })}
      </div>

      {/* Site Speed Overview */}
      <h3 style={s.sectionTitle}>Site Speed Overview</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: space.md }} className="mobile-grid-1">
        <div style={s.metricCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
            <span style={statusDot(cwvStatus('lcp', desktopCwv.largest_contentful_paint_ms ?? null))} />
            <span style={s.metricLabel}>Desktop Load Time</span>
          </div>
          <div style={s.metricValue}>{formatMs(desktopCwv.largest_contentful_paint_ms ?? null)}</div>
          <p style={s.metricInterpretation}>How quickly the main content loads on desktop</p>
        </div>
        <div style={s.metricCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
            <span style={statusDot(cwvStatus('lcp', cwv.largest_contentful_paint_ms ?? null))} />
            <span style={s.metricLabel}>Mobile Load Time</span>
          </div>
          <div style={s.metricValue}>{formatMs(cwv.largest_contentful_paint_ms ?? null)}</div>
          <p style={s.metricInterpretation}>How quickly the main content loads on mobile</p>
        </div>
        <div style={s.metricCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
            <span style={statusDot(cwvStatus('tbt', cwv.total_blocking_time_ms ?? null))} />
            <span style={s.metricLabel}>Time to Interactive</span>
          </div>
          <div style={s.metricValue}>{formatMs(cwv.total_blocking_time_ms ?? null)}</div>
          <p style={s.metricInterpretation}>How long before visitors can click and interact</p>
        </div>
      </div>

      {/* Accessibility Overview */}
      <h3 style={s.sectionTitle}>Accessibility Overview</h3>
      <div style={{ backgroundColor: color.bgCard, borderRadius: radius.xl, padding: space.lg, boxShadow: color.shadow }}>
        {a11yIssueCount === 0 ? (
          <p style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.text, margin: 0 }}>
            No accessibility issues detected — the site meets basic WCAG compliance standards.
          </p>
        ) : (
          <>
            <p style={{ fontFamily: font.family, fontSize: font.sizeMd, fontWeight: font.weightSemibold, color: color.text, margin: 0, marginBottom: space.sm }}>
              {a11yIssueCount} accessibility issue{a11yIssueCount !== 1 ? 's' : ''} detected
            </p>
            <div style={{ display: 'flex', gap: space.lg, flexWrap: 'wrap', marginBottom: space.sm }}>
              {a11yCats.critical.length > 0 && (
                <div>
                  <span style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightBold, color: '#EF4444' }}>
                    {a11yCats.critical.length} Critical
                  </span>
                  <ul style={{ margin: `${space.xxs} 0 0 0`, paddingLeft: space.md, listStyle: 'disc' }}>
                    {a11yCats.critical.map((t, i) => <li key={i} style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted }}>{t}</li>)}
                  </ul>
                </div>
              )}
              {a11yCats.moderate.length > 0 && (
                <div>
                  <span style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightBold, color: '#F59E0B' }}>
                    {a11yCats.moderate.length} Moderate
                  </span>
                  <ul style={{ margin: `${space.xxs} 0 0 0`, paddingLeft: space.md, listStyle: 'disc' }}>
                    {a11yCats.moderate.map((t, i) => <li key={i} style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted }}>{t}</li>)}
                  </ul>
                </div>
              )}
              {a11yCats.minor.length > 0 && (
                <div>
                  <span style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightBold, color: '#6B7280' }}>
                    {a11yCats.minor.length} Minor
                  </span>
                  <ul style={{ margin: `${space.xxs} 0 0 0`, paddingLeft: space.md, listStyle: 'disc' }}>
                    {a11yCats.minor.map((t, i) => <li key={i} style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted }}>{t}</li>)}
                  </ul>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Technical Details (collapsed) */}
      <div style={{ marginTop: space.lg }}>
        <button
          onClick={() => setTechDetailsOpen(!techDetailsOpen)}
          style={{
            display: 'flex', alignItems: 'center', gap: space.sm, background: 'none',
            border: `1px solid ${color.border}`, borderRadius: radius.lg,
            padding: `${space.sm} ${space.md}`, cursor: 'pointer', fontFamily: font.family,
            fontSize: font.sizeSm, fontWeight: font.weightSemibold, color: color.text,
            width: '100%', justifyContent: 'space-between',
          }}
        >
          <span>Technical Details — Core Web Vitals Reference</span>
          <span style={{ fontSize: font.sizeXs, color: color.textMuted }}>{techDetailsOpen ? '▲ Collapse' : '▼ Expand'}</span>
        </button>
        {techDetailsOpen && (
          <div style={{ marginTop: space.md }}>
            <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, margin: `0 0 ${space.md} 0` }}>
              Raw Core Web Vitals metrics used by Google to evaluate page experience.
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: space.md }} className="mobile-grid-1">
              {cwvMetrics.map((m) => {
                const level = cwvStatus(m.thresholdKey, m.value);
                const cwvItem = cwvInterps?.[CWV_INTERP_MAP[m.key]] as { what?: string; why?: string; where?: string } | undefined;
                return (
                  <div key={m.key} style={s.metricCard}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
                      <span style={statusDot(level)} />
                      <span style={{ ...s.metricLabel, flex: 1 }}>{m.label} ({m.techLabel})</span>
                      <Tooltip text={CWV_TOOLTIPS[m.key]} />
                    </div>
                    <div style={s.metricValue}>{m.format(m.value)}</div>
                    {m.desktopValue !== null && <div style={s.desktopNote}>Desktop: {m.format(m.desktopValue)}</div>}
                    <p style={{ ...s.metricInterpretation, fontStyle: 'italic' as const }}>{m.explanation}</p>
                    {cwvItem?.what && <p style={s.metricInterpretation}>{cwvItem.what}</p>}
                    {cwvItem?.why && <p style={{ ...s.metricInterpretation, color: color.textMuted }}>{cwvItem.why}</p>}
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Technology Stack */}
      {Object.keys(groups).length > 0 && (
        <>
          <h3 style={s.sectionTitle}>Technology Stack</h3>
          <div style={s.card}>
            {Object.entries(groups).map(([label, names], i, arr) => (
              <div key={label} style={{
                display: 'flex', gap: space.md, padding: `${space.sm} 0`,
                borderBottom: i === arr.length - 1 ? 'none' : `1px solid ${color.border}`,
                alignItems: 'center',
              }}>
                <span style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightSemibold, color: color.textDim, textTransform: 'uppercase' as const, letterSpacing: '0.04em', width: 90, flexShrink: 0 }}>{label}</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {names.map((name) => (
                    <span key={name} style={{ display: 'inline-block', padding: '3px 10px', borderRadius: radius.pill, fontSize: font.sizeXs, fontWeight: font.weightMedium, background: color.bgPage, color: color.text, border: `1px solid ${color.border}` }}>{name}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Observations */}
      {narrative && (
        <>
          <h3 style={s.sectionTitle}>Observations &amp; Findings</h3>
          <div style={{ ...s.card, borderLeft: `4px solid ${lensColor}` }}>
            <span style={s.interpLabel}>RETINA ANALYSIS</span>
            {narrative.split('\n\n').map((para, i) => (
              <p key={i} style={s.interpText}>{para}</p>
            ))}
          </div>
        </>
      )}
    </>
  );
}

/* ══════════════════════════════════════════════════════
   SEO SECTION — read-only mirror
   ══════════════════════════════════════════════════════ */

function SharedSeoSection({ lens }: { lens: SharedLensData }) {
  const lhData = lens.lighthouse_data as Record<string, Record<string, unknown>> || {};
  const mobile = lhData.mobile || {};
  const audits = ((mobile.audits || []) as Array<{ id: string; score: number | null; title: string; category: string; description?: string }>);
  const lensColor = lens.lens_color;

  const priorityIds = [
    'meta-description', 'document-title', 'image-alt', 'robots-txt',
    'canonical', 'hreflang', 'structured-data', 'crawlable-anchors',
    'link-text', 'is-crawlable', 'http-status-code',
  ];
  const seoAudits = audits.filter((a) => a.category === 'seo');
  const ordered: typeof seoAudits = [];
  const seen = new Set<string>();
  for (const id of priorityIds) {
    const a = seoAudits.find((x) => x.id === id);
    if (a) { ordered.push(a); seen.add(a.id); }
  }
  for (const a of seoAudits) { if (!seen.has(a.id)) ordered.push(a); }

  const seoInterp = lens.interpretations.seo as Record<string, unknown> | undefined;
  const narrative = seoInterp?.section_narrative as string | undefined;
  const auditInterps = seoInterp?.audits as Record<string, { what?: string }> | undefined;

  return (
    <>
      <h3 style={s.sectionTitle}>SEO Health Checks</h3>
      <div style={s.card}>
        {ordered.length === 0 ? (
          <p style={{ ...s.interpText, color: color.textMuted }}>No SEO audits available</p>
        ) : (
          ordered.map((audit, i) => {
            const passed = audit.score === 1 || audit.score === null;
            const isCriticalFail = !passed && (audit.id === 'robots-txt' || audit.id === 'meta-description' || audit.id === 'is-crawlable');
            return (
              <div key={audit.id} style={{
                display: 'flex', gap: space.sm, padding: `${space.sm} ${space.sm}`,
                borderBottom: i === ordered.length - 1 ? 'none' : `1px solid ${color.border}`,
                alignItems: 'flex-start',
                ...(isCriticalFail ? { backgroundColor: '#FEF3C7' } : {}),
              }}>
                <span style={{ fontSize: '1rem', flexShrink: 0, width: 24, textAlign: 'center' }}>
                  {passed ? '✅' : '❌'}
                </span>
                <div style={{ flex: 1 }}>
                  <span style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightSemibold, color: color.text }}>{audit.title}</span>
                  {audit.description && (
                    <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, margin: `${space.xxs} 0 0`, lineHeight: 1.5 }}>
                      {audit.description.replace(/\[.*?\]\(.*?\)/g, '').trim().slice(0, 140)}
                    </p>
                  )}
                  {!passed && auditInterps?.[audit.id]?.what && (
                    <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.accent, margin: `${space.xxs} 0 0`, lineHeight: 1.5, fontStyle: 'italic' }}>{auditInterps[audit.id].what}</p>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* AI Visibility Note */}
      <h3 style={s.sectionTitle}>AI Visibility</h3>
      <div style={{ ...s.card, backgroundColor: '#F0FDF4', borderLeft: `4px solid ${lensColor}` }}>
        <span style={{ ...s.interpLabel, color: lensColor }}>ABOUT AI VISIBILITY</span>
        <p style={s.interpText}>
          AI Visibility measures how well your site's content structure, metadata, and semantic markup
          make it readable and citable by AI tools like ChatGPT and Perplexity.
        </p>
      </div>

      {/* Observations */}
      {narrative && (
        <>
          <h3 style={s.sectionTitle}>Observations &amp; Findings</h3>
          <div style={{ ...s.card, borderLeft: `4px solid ${lensColor}` }}>
            <span style={s.interpLabel}>RETINA ANALYSIS</span>
            {narrative.split('\n\n').map((para, i) => (
              <p key={i} style={s.interpText}>{para}</p>
            ))}
          </div>
        </>
      )}
    </>
  );
}

/* ══════════════════════════════════════════════════════
   ANALYST LENS SECTION (Brand, Experience, Conversion)
   — read-only mirror
   ══════════════════════════════════════════════════════ */

function SharedAnalystSection({ lens }: { lens: SharedLensData }) {
  const maxScores = SUB_DIM_MAX[lens.lens_id] || {};
  const entries = Object.entries(lens.analyst_sub_scores);

  // Observations text
  const rawNarrative = lens.interpretations.analyst_narrative;
  let aiText = lens.analyst_observations || '';
  if (!aiText && typeof rawNarrative === 'string') {
    aiText = rawNarrative;
  } else if (!aiText && rawNarrative && typeof rawNarrative === 'object') {
    const narr = rawNarrative as Record<string, unknown>;
    const parts: string[] = [];
    if (narr.orientation) parts.push(String(narr.orientation));
    if (narr.what_good_looks_like) parts.push(String(narr.what_good_looks_like));
    aiText = parts.join('\n\n');
  }
  const displayText = lens.user_observations ?? aiText;

  return (
    <>
      {/* Overall Observations */}
      {displayText && (
        <div style={{ ...s.card, borderLeft: `4px solid ${lens.lens_color}`, marginTop: space.lg }}>
          <h3 style={{ ...s.sectionTitle, margin: 0, marginBottom: space.md }}>Overall Observations</h3>
          {displayText.split('\n\n').map((para, i) => (
            <p key={i} style={s.interpText}>{para}</p>
          ))}
        </div>
      )}

      {/* Sub Dimensions */}
      {entries.length > 0 && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: space.xl, marginBottom: space.md }}>
            <h3 style={{ ...s.sectionTitle, margin: 0 }}>Sub Dimensions</h3>
            <span style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textDim }}>
              4–5: Best in class · 3–3.5: Solid · 1.5–2.5: Notable gaps · 0.5–1: Critical
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: space.md }} className="mobile-grid-1">
            {entries.map(([key, val]) => {
              const maxScore = maxScores[key] ?? 5;
              return (
                <div key={key} style={s.card}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: space.md }}>
                    <span style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightBold, color: color.text }}>
                      {humanizeKey(key)}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: space.md, alignItems: 'flex-start' }}>
                    <LensDonut score={val.score} maxScore={maxScore} lensColor={lens.lens_color} diameter={56} />
                    <p style={{
                      margin: 0, fontFamily: font.family, fontSize: font.sizeSm,
                      color: val.observation ? color.text : color.textMuted,
                      lineHeight: 1.6, flex: 1,
                      fontStyle: val.observation ? 'normal' : 'italic',
                    }}>
                      {val.observation || 'Awaiting analysis'}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Artifacts */}
      {lens.artifacts.length > 0 && (
        <div style={{ marginTop: space.lg }}>
          <h3 style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: font.sizeLg, color: color.text, margin: `0 0 ${space.md} 0` }}>Artifacts</h3>
          <div style={{ display: 'flex', gap: space.md, flexWrap: 'wrap' }}>
            {lens.artifacts.map((a) => (
              <div key={a.id} style={{ position: 'relative' as const, width: 120, height: 120, borderRadius: radius.lg, overflow: 'hidden', border: `1px solid ${color.border}`, backgroundColor: color.bgPage }}>
                <img src={a.file_url} alt={a.file_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

/* ══════════════════════════════════════════════════════
   RECOMMENDATIONS — read-only (from Report.tsx)
   ══════════════════════════════════════════════════════ */

function SharedRecommendationsCard({ recommendations }: { recommendations: RecommendationQuadrant[] }) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    recommendations.forEach((r) => { initial[r.quadrant] = r.items.length > 0; });
    return initial;
  });

  return (
    <div style={s.card}>
      <h2 style={{ ...s.cardTitle, marginBottom: space.md }}>Recommendations</h2>
      {recommendations.map((rec) => (
        <div key={rec.quadrant} style={{ borderBottom: `1px solid ${color.border}`, paddingBottom: space.sm, marginBottom: space.sm }}>
          <button
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              width: '100%', background: 'none', border: 'none', cursor: 'pointer',
              padding: `${space.sm} 0`, fontFamily: font.family, fontSize: font.sizeSm,
              fontWeight: font.weightSemibold, color: color.text, textAlign: 'left' as const,
            }}
            onClick={() => setExpanded((prev) => ({ ...prev, [rec.quadrant]: !prev[rec.quadrant] }))}
          >
            <span>{rec.quadrant}</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="2"
              style={{ transform: expanded[rec.quadrant] ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
          {expanded[rec.quadrant] && (
            <div style={{ paddingTop: space.xs }}>
              {rec.items.length === 0 ? (
                <p style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.textMuted, fontStyle: 'italic', margin: 0 }}>None yet</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: space.xs }}>
                  {rec.items.map((item, i) => {
                    const obj = normalizeItem(item);
                    return (
                      <div key={i} style={{ padding: space.sm, backgroundColor: color.bgPage, borderRadius: radius.md }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: space.sm }}>
                          <strong style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.text }}>{obj.title}</strong>
                          {obj.lens && <span style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.accent, background: color.accentLight, padding: '2px 8px', borderRadius: radius.pill }}>{obj.lens}</span>}
                        </div>
                        {obj.description && (
                          <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, margin: `${space.xxs} 0 0`, lineHeight: 1.5 }}>{obj.description}</p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   REPORT VIEWER — full analyst experience, read-only
   ══════════════════════════════════════════════════════ */

function ReportViewer({ data }: { data: SharedProjectData }) {
  const { project, lenses } = data;
  const [activeLens, setActiveLens] = useState<string | null>(null);
  const isMobile = useIsMobile();

  const activeLensData = lenses.find((l) => l.lens_id === activeLens);

  const logoBlock = (
    <>
      <svg width="36" height="36" viewBox="0 0 664 664" fill="none">
        <path
          d="M332 20C149 20 0 169 0 352h87c0-135 110-245 245-245s245 110 245 245h87C664 169 515 20 332 20Zm101 332c0-56-45-101-101-101s-101 45-101 101 45 101 101 101 101-45 101-101Zm87 0c0 104-85 188-188 188S144 456 144 352s85-188 188-188 188 85 188 188Zm-130 0c0 32-26 58-58 58s-58-26-58-58 26-58 58-58 58 26 58 58Z"
          fill={color.text}
        />
      </svg>
      <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
        <span style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: font.sizeMd, color: color.text }}>Matic</span>
        <span style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: font.sizeMd, color: color.text }}>Retina</span>
      </div>
    </>
  );

  return (
    <div style={s.layout}>
      {isMobile ? (
        /* Mobile: fixed top bar instead of sidebar */
        <header style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 20,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: `${space.sm} ${space.md}`,
          backgroundColor: sidebarToken.bgColor,
          borderBottom: `1px solid ${color.border}`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.xs }}>{logoBlock}</div>
          <div style={s.sidebarBadge}>Shared Report</div>
        </header>
      ) : (
        /* Desktop: fixed sidebar */
        <aside style={s.sidebar}>
          <div style={s.sidebarLogo}>{logoBlock}</div>
          <div style={s.sidebarBadge}>Shared Report</div>
        </aside>
      )}

      <main style={s.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
        {/* ── PAGE HEADER ─────────────────────────────── */}
        <div style={s.pageHeader}>
          <h1 style={s.pageTitle}>
            <span style={{ color: color.textMuted }}>Project</span>
            <span style={{ color: color.textDim, fontWeight: font.weightRegular }}> | </span>
            <span
              style={{ fontWeight: font.weightRegular, cursor: activeLens ? 'pointer' : 'default', textDecoration: activeLens ? 'underline' : 'none' }}
              onClick={() => activeLens && setActiveLens(null)}
            >{project.name}</span>
          </h1>
        </div>

        {/* ── LENS NAVIGATION BAR ─────────────────────── */}
        <div style={s.lensBar} className={isMobile ? 'mobile-scroll-x' : ''}>
          {project.lens_scores.map((lens) => {
            const isActive = activeLens === lens.lens_id;
            return (
              <button
                key={lens.lens_id}
                style={{
                  ...s.lensTab,
                  ...(isActive ? { borderBottom: `3px solid ${LENS_COLORS[lens.lens_id] || color.accent}`, opacity: 1 } : {}),
                  ...(isMobile ? { minWidth: 100, flex: 'none' } : {}),
                }}
                onClick={() => setActiveLens(isActive ? null : lens.lens_id)}
              >
                <img src={LENS_ICONS[lens.lens_id]} alt="" style={s.lensIcon} />
                <span style={s.lensTabName}>{lens.lens_name}</span>
              </button>
            );
          })}
        </div>

        {/* ── LENS DETAIL VIEW ────────────────────────── */}
        {activeLens && activeLensData && (
          <div style={{ marginBottom: space.xl }}>
            {/* Lens Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: space.md, marginBottom: space.lg }}>
              <LensDonut score={activeLensData.lens_score} maxScore={activeLensData.max_score} lensColor={activeLensData.lens_color} diameter={80} />
              <div>
                <h2 style={{ margin: 0, fontFamily: font.family, fontWeight: font.weightBold, fontSize: font.sizeXl, color: color.text }}>
                  {activeLensData.lens_name}
                </h2>
                <p style={{ margin: 0, fontFamily: font.family, fontSize: font.sizeSm, color: color.textMuted }}>
                  {LENS_DEFINITIONS[activeLensData.lens_id] ?? ''}
                </p>
              </div>
            </div>

            {/* Lens Content */}
            {activeLensData.lens_id === 'performance_technical_health' && (
              <SharedPerformanceSection lens={activeLensData} />
            )}
            {activeLensData.lens_id === 'seo_ai_visibility' && (
              <SharedSeoSection lens={activeLensData} />
            )}
            {(activeLensData.lens_id === 'brand_messaging' || activeLensData.lens_id === 'experience_design' || activeLensData.lens_id === 'conversion_strategy') && (
              <SharedAnalystSection lens={activeLensData} />
            )}
          </div>
        )}

        {/* ── SUMMARY CONTENT (visible when no lens is active) ── */}
        {!activeLens && (
          <div style={s.summaryGrid} className={isMobile ? 'mobile-grid-1' : ''}>
            {/* LEFT COLUMN */}
            <div style={s.column}>
              {/* Project Overview */}
              <div style={s.card}>
                <h2 style={s.projectNameText}>{project.name}</h2>
                <a href={project.primary_url} target="_blank" rel="noopener noreferrer" style={s.projectUrl}>
                  {project.primary_url}
                </a>
                {project.screenshot_url && (
                  <div style={s.screenshotWrap}>
                    <img src={project.screenshot_url} alt={`${project.name} screenshot`} style={s.screenshotImg} />
                  </div>
                )}
              </div>

              {/* Technology Stack */}
              {project.tech_stack && Object.keys(project.tech_stack).length > 0 && (
                <div style={s.card}>
                  <h2 style={s.cardTitle}>Technology Stack</h2>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: space.sm }}>
                    {(['cms', 'analytics', 'crm'] as const).map((cat) => {
                      const items = (project.tech_stack as TechStack)?.[cat];
                      if (!items || items.length === 0) return null;
                      const labels: Record<string, string> = { cms: 'CMS', analytics: 'Analytics', crm: 'CRM' };
                      return (
                        <div key={cat}>
                          <p style={{ margin: 0, fontSize: font.sizeXs, fontWeight: font.weightSemibold, color: color.textDim, textTransform: 'uppercase' as const, letterSpacing: '0.04em', marginBottom: space.xxs }}>
                            {labels[cat]}
                          </p>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {items.map((tech) => (
                              <span key={tech} style={{
                                display: 'inline-block', padding: '3px 10px', borderRadius: radius.pill,
                                fontSize: font.sizeXs, fontWeight: font.weightMedium, background: color.bgPage,
                                color: color.text, border: `1px solid ${color.border}`,
                              }}>{tech}</span>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Competitors */}
              {project.competitors.length > 0 && (
                <div style={s.card}>
                  <h2 style={s.cardTitle}>Competitors</h2>
                  {project.competitors.map((comp, i) => (
                    <div key={comp.url} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      padding: `${space.sm} 0`,
                      borderBottom: i < project.competitors.length - 1 ? `1px solid ${color.border}` : 'none',
                    }}>
                      <span style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.text }}>{comp.url}</span>
                      <span style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.textMuted }}>
                        {comp.retina_score !== null ? `${Math.round(comp.retina_score)}/20` : '—/20'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* RIGHT COLUMN */}
            <div style={s.column}>
              {/* Score Summary */}
              <div style={s.card}>
                <h2 style={s.cardTitle}>Score Summary</h2>
                <div style={{ display: 'flex', gap: space.lg, alignItems: 'flex-start' }} className={isMobile ? 'mobile-stack' : ''}>
                  <div style={{ textAlign: 'center' as const, ...(isMobile ? { alignSelf: 'center' } : {}) }}>
                    <span style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.textMuted }}>Retina</span>
                    <ScoreDonut lensScores={project.lens_scores} retinaScore={project.retina_score} />
                  </div>
                  <div style={{ flex: 1 }}>
                    {project.lens_scores.map((lens, i) => (
                      <div key={lens.lens_id} style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        padding: `${space.sm} 0`,
                        borderBottom: i < project.lens_scores.length - 1 ? `1px solid ${color.border}` : 'none',
                      }}>
                        <span style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.text }}>{lens.lens_name}</span>
                        <span style={{ fontFamily: font.family, fontSize: font.sizeSm }}>
                          {lens.score !== null ? (
                            <>
                              <span style={{ fontWeight: font.weightBold, color: LENS_COLORS[lens.lens_id] || color.text }}>
                                {lens.score % 1 === 0 ? lens.score : lens.score.toFixed(1)}
                              </span>
                              <span style={{ color: color.textDim }}>/20</span>
                            </>
                          ) : (
                            <span style={{ color: color.textDim }}>—/20</span>
                          )}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              {project.recommendations.length > 0 && (
                <SharedRecommendationsCard recommendations={project.recommendations} />
              )}
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{ textAlign: 'center' as const, padding: `${space.xl} 0` }}>
          <span style={{ color: color.textDim, fontFamily: font.family, fontSize: font.sizeSm }}>
            Generated by Matic Retina
          </span>
        </div>
      </main>
    </div>
  );
}

/* ── Shared Styles ────────────────────────────────── */

const s: Record<string, React.CSSProperties> = {
  layout: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: color.bgPage,
  },
  sidebar: {
    width: sidebarToken.width,
    minHeight: '100vh',
    backgroundColor: sidebarToken.bgColor,
    display: 'flex',
    flexDirection: 'column',
    padding: `${space.lg} ${space.md}`,
    boxSizing: 'border-box',
    borderRight: `1px solid ${color.border}`,
    position: 'fixed',
    left: 0,
    top: 0,
    bottom: 0,
    zIndex: 10,
    alignItems: 'center',
    gap: space.lg,
  },
  sidebarLogo: {
    display: 'flex',
    alignItems: 'center',
    gap: space.xs,
  },
  sidebarBadge: {
    padding: '4px 10px',
    borderRadius: radius.pill,
    backgroundColor: color.accentLight,
    color: color.accent,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightSemibold,
  },
  main: {
    flex: 1,
    marginLeft: sidebarToken.width,
    padding: `${space.xl} ${space.xxl}`,
    maxWidth: 1100,
  },
  pageHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: space.lg,
    gap: space.md,
  },
  pageTitle: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.size2xl,
    color: color.text,
  },
  lensBar: {
    display: 'flex',
    gap: 0,
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    boxShadow: color.shadow,
    padding: `${space.sm} 0 0 0`,
    marginBottom: space.xl,
    overflow: 'hidden',
  },
  lensTab: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.xs,
    padding: `${space.sm} ${space.xs}`,
    border: 'none',
    borderBottom: '2px solid transparent',
    background: 'none',
    cursor: 'pointer',
    fontFamily: font.family,
    fontSize: '0.875rem',
    fontWeight: font.weightMedium,
    color: color.text,
    textAlign: 'center',
    transition: 'border-color 0.15s',
    opacity: 1,
    minWidth: 0,
  },
  lensIcon: {
    width: 36,
    height: 36,
    flexShrink: 0,
  },
  lensTabName: {
    lineHeight: 1.3,
    display: 'block',
    width: '100%',
    textAlign: 'center',
    wordBreak: 'keep-all' as const,
    overflowWrap: 'break-word' as const,
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: space.lg,
    alignItems: 'start',
  },
  column: {
    display: 'flex',
    flexDirection: 'column',
    gap: space.lg,
  },
  card: {
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    padding: space.xl,
    boxShadow: color.shadow,
  },
  cardTitle: {
    margin: 0,
    marginBottom: space.md,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeLg,
    color: color.text,
  },
  projectNameText: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeXl,
    color: color.text,
  },
  projectUrl: {
    display: 'block',
    marginTop: space.xxs,
    marginBottom: space.md,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
    textDecoration: 'none',
  },
  screenshotWrap: {
    width: '100%',
    aspectRatio: '16 / 9',
    borderRadius: radius.lg,
    overflow: 'hidden',
    backgroundColor: '#E0E0E0',
    position: 'relative' as const,
  },
  screenshotImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const,
  },
  sectionTitle: {
    fontFamily: font.family,
    fontWeight: font.weightBold,
    fontSize: font.sizeLg,
    color: color.text,
    margin: `${space.lg} 0 ${space.md} 0`,
  },
  metricCard: {
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    padding: space.md,
    boxShadow: color.shadow,
  },
  metricLabel: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightSemibold,
    color: color.textDim,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.03em',
  },
  metricValue: {
    fontFamily: font.family,
    fontSize: font.sizeXl,
    fontWeight: font.weightBold,
    color: color.text,
    margin: `${space.xs} 0`,
  },
  metricInterpretation: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    margin: `${space.xxs} 0 0`,
    lineHeight: 1.5,
  },
  desktopNote: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textDim,
    marginBottom: space.xs,
  },
  interpLabel: {
    display: 'block',
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightBold,
    letterSpacing: '0.06em',
    color: color.textDim,
    marginBottom: space.sm,
    textTransform: 'uppercase' as const,
  },
  interpText: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.text,
    lineHeight: 1.7,
    margin: `0 0 ${space.sm} 0`,
  },
};

/* ── Main Export ──────────────────────────────────── */

export function SharedReport() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<SharedProjectData | null>(null);

  if (!token) {
    return (
      <div style={gateStyles.page}>
        <div style={gateStyles.card}>
          <h1 style={gateStyles.heading}>Invalid share link</h1>
        </div>
      </div>
    );
  }

  if (!data) {
    return <PasswordGate token={token} onVerified={setData} />;
  }

  return <ReportViewer data={data} />;
}
