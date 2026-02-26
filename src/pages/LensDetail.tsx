import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getLensDetail, saveLensObservations, updateSubDimension, uploadArtifact, deleteArtifact, startPdfExport, getExportStatus } from '../api';
import type { LensDetailData, Artifact, ExportStatusResponse } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import { Sidebar } from '../components/Sidebar';
import { NAV_ITEMS } from './Dashboard';

import { CopilotPanel } from '../components/CopilotPanel';
import type { CopilotMessage } from '../components/CopilotPanel';
import { sendCopilotMessage } from '../api';
import performanceIcon from '../assets/performance_icon.svg';
import seoIcon from '../assets/seo_icon.svg';
import brandIcon from '../assets/brand_icon.svg';
import experienceIcon from '../assets/experience_icon.svg';
import conversionIcon from '../assets/conversion_icon.svg';

/* ── Constants ────────────────────────────────────── */

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

/* ── Small Helpers ────────────────────────────────── */

function ArrowCircleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginLeft: 4 }}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8l4 4-4 4M8 12h8" />
    </svg>
  );
}

function SparkleIcon({ size = 18, color: c = color.textMuted }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3v2m0 14v2M5.636 5.636l1.414 1.414m9.9 9.9l1.414 1.414M3 12h2m14 0h2M5.636 18.364l1.414-1.414m9.9-9.9l1.414-1.414" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function PencilIcon({ size = 16, color: c = color.textMuted }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
    </svg>
  );
}

function Toast({ message, onDone }: { message: string; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2500);
    return () => clearTimeout(t);
  }, [onDone]);
  return <div style={styles.toast}>{message}</div>;
}

/* ── Lens Score Donut (single-lens, /20) ──────────── */

function LensDonut({ score, maxScore, lensColor, diameter = 100 }: { score: number | null; maxScore: number; lensColor: string; diameter?: number }) {
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
        <circle
          cx={diameter / 2} cy={diameter / 2} r={r} fill="none"
          stroke={lensColor} strokeWidth={strokeWidth}
          strokeDasharray={`${filledLength} ${circumference - filledLength}`}
          strokeDashoffset={circumference * 0.25}
          strokeLinecap="round"
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

/* ── Status helpers ───────────────────────────────── */

type StatusLevel = 'good' | 'warning' | 'poor';

function statusDot(level: StatusLevel): React.CSSProperties {
  const colors = { good: '#22C55E', warning: '#F59E0B', poor: '#EF4444' };
  return { width: 10, height: 10, borderRadius: '50%', backgroundColor: colors[level], display: 'inline-block', flexShrink: 0 };
}

function cwvStatus(metric: string, value: number | null): StatusLevel {
  if (value === null) return 'poor';
  const thresholds: Record<string, [number, number]> = {
    lcp: [2500, 4000],
    fcp: [1800, 3000],
    cls: [0.1, 0.25],
    tbt: [200, 600],
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

function humanizeKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/* ══════════════════════════════════════════════════════
   SECTION COMPONENTS — one per lens
   ══════════════════════════════════════════════════════ */

/* ── Tooltip Component ────────────────────────────── */

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
          position: 'absolute',
          bottom: 'calc(100% + 8px)',
          left: '50%',
          transform: 'translateX(-50%)',
          background: '#1a1a1a',
          color: '#fff',
          padding: `${space.xs} ${space.sm}`,
          borderRadius: radius.md,
          fontSize: font.sizeXs,
          fontFamily: font.family,
          lineHeight: 1.4,
          width: 220,
          zIndex: 100,
          pointerEvents: 'none',
          whiteSpace: 'normal',
          boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
        }}>
          {text}
        </div>
      )}
    </span>
  );
}

/* ── Metric Tooltip Content ──────────────────────── */

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

/* ── Observations & Findings Card ─────────────────── */

function ObservationsCard({
  projectId,
  lensId,
  lensColor,
  aiText,
  userText,
  onSaved,
}: {
  projectId: string;
  lensId: string;
  lensColor: string;
  aiText: string;
  userText: string | null;
  onSaved?: (text: string | null) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(userText ?? aiText);
  const [saving, setSaving] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);

  const displayText = userText ?? aiText;
  const isUserEdited = userText !== null && userText !== aiText;

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveLensObservations(projectId, lensId, draft);
      onSaved?.(draft);
      setEditing(false);
    } catch {
      // stay in edit mode on error
    }
    setSaving(false);
  };

  const handleReset = async () => {
    setSaving(true);
    try {
      await saveLensObservations(projectId, lensId, aiText);
      onSaved?.(null);
      setDraft(aiText);
      setEditing(false);
      setConfirmReset(false);
    } catch {
      // stay in edit mode on error
    }
    setSaving(false);
  };

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={styles.sectionTitle}>Observations &amp; Findings</h3>
        {!editing && (
          <button
            style={styles.editObsBtn}
            onClick={() => { setDraft(displayText); setEditing(true); }}
          >
            Edit
          </button>
        )}
      </div>
      <div style={{ ...styles.card, borderLeft: `4px solid ${lensColor}` }}>
        {editing ? (
          <>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              style={styles.obsTextarea}
              rows={8}
            />
            <div style={styles.obsActions}>
              <button style={styles.obsSaveBtn} onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button style={styles.obsCancelBtn} onClick={() => setEditing(false)}>Cancel</button>
              {isUserEdited && !confirmReset && (
                <button style={styles.obsResetLink} onClick={() => setConfirmReset(true)}>
                  Reset to AI version
                </button>
              )}
              {confirmReset && (
                <span style={styles.obsResetConfirm}>
                  Revert to AI text?{' '}
                  <button style={styles.obsResetLink} onClick={handleReset}>Yes</button>{' '}
                  <button style={styles.obsResetLink} onClick={() => setConfirmReset(false)}>No</button>
                </span>
              )}
            </div>
          </>
        ) : (
          <>
            <span style={styles.interpLabel}>RETINA ANALYSIS</span>
            {displayText.split('\n\n').map((para, i) => (
              <p key={i} style={styles.interpText}>{para}</p>
            ))}
            {isUserEdited && (
              <span style={styles.obsEditedBadge}>Edited</span>
            )}
          </>
        )}
      </div>
    </>
  );
}

/* ── Score interpretation helpers ─────────────────── */

function scoreInterpretation(score: number): string {
  if (score >= 90) return 'Strong performance';
  if (score >= 70) return 'Solid, with room to improve';
  if (score >= 50) return 'Needs improvement';
  return 'Needs significant improvement';
}

/* ── Performance & Platform ──────────────────────── */

function PerformanceSection({ data }: { data: LensDetailData }) {
  const [techDetailsOpen, setTechDetailsOpen] = useState(false);
  const mobile = data.lighthouse_data.mobile || {};
  const desktop = data.lighthouse_data.desktop || {};
  const cwv = mobile.core_web_vitals || {};
  const desktopCwv = desktop.core_web_vitals || {};
  const lhScores = mobile.lighthouse_scores || {};
  const desktopLhScores = desktop.lighthouse_scores || {};
  const lensColor = data.lens_color;

  // Tech stack by tag
  const techs = data.builtwith_data.technologies || [];
  const TAG_LABELS: Record<string, string> = {
    cms: 'CMS', framework: 'Framework', analytics: 'Analytics', cdn: 'CDN',
    cdns: 'CDN', hosting: 'Hosting', javascript: 'JavaScript', ssl: 'SSL',
    widgets: 'Widgets', mx: 'Email', ns: 'DNS', ads: 'Advertising',
    mobile: 'Mobile', payment: 'Payment', robots: 'Robots / AI',
    link: 'Social Links',
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
  const perfInterp = data.interpretations.performance as Record<string, unknown> | undefined;
  const narrative = perfInterp?.section_narrative as string | undefined;

  // CWV interpretations (what/why/where three-part structure)
  const cwvInterps = perfInterp?.cwv as Record<string, { what?: string; why?: string; where?: string }> | undefined;
  const CWV_INTERP_MAP: Record<string, string> = {
    lcp: 'largest_contentful_paint_ms',
    fcp: 'first_contentful_paint_ms',
    cls: 'cumulative_layout_shift',
    tbt: 'total_blocking_time_ms',
  };

  // Top 4 headline score cards
  const headlineScores: { key: string; label: string; tooltip: string }[] = [
    { key: 'performance', label: 'Performance Score', tooltip: LIGHTHOUSE_TOOLTIPS.performance },
    { key: 'accessibility', label: 'Accessibility Score', tooltip: LIGHTHOUSE_TOOLTIPS.accessibility },
    { key: 'seo', label: 'SEO Score', tooltip: LIGHTHOUSE_TOOLTIPS.seo },
    { key: 'best_practices', label: 'Best Practices Score', tooltip: LIGHTHOUSE_TOOLTIPS.best_practices },
  ];

  // Accessibility audit analysis
  const mobileAudits = mobile.audits || [];
  const a11yAudits = mobileAudits.filter((a: { category: string; score: number | null }) => a.category === 'accessibility' && a.score !== null && a.score < 1);
  const a11yIssueCount = a11yAudits.length;

  // Categorize accessibility issues
  const a11yCats = { critical: [] as string[], moderate: [] as string[], minor: [] as string[] };
  const CRITICAL_A11Y = ['aria-required-attr', 'aria-valid-attr', 'aria-roles', 'button-name', 'input-image-alt', 'label', 'form-field-multiple-labels'];
  const MINOR_A11Y = ['image-alt', 'link-name', 'meta-viewport', 'tabindex'];
  for (const a of a11yAudits) {
    const audit = a as { id: string; title: string; score: number | null };
    if (CRITICAL_A11Y.includes(audit.id)) {
      a11yCats.critical.push(audit.title);
    } else if (MINOR_A11Y.includes(audit.id)) {
      a11yCats.minor.push(audit.title);
    } else {
      a11yCats.moderate.push(audit.title);
    }
  }

  // CWV metrics for Technical Details (collapsed section)
  const cwvMetrics: { key: string; label: string; techLabel: string; value: number | null; desktopValue: number | null; format: (v: number | null) => string; thresholdKey: string; explanation: string }[] = [
    { key: 'lcp', label: 'Largest Contentful Paint', techLabel: 'LCP', value: cwv.largest_contentful_paint_ms ?? null, desktopValue: desktopCwv.largest_contentful_paint_ms ?? null, format: formatMs, thresholdKey: 'lcp', explanation: 'Time for the largest visible element (image/text block) to render. Under 2.5s is good.' },
    { key: 'fcp', label: 'First Contentful Paint', techLabel: 'FCP', value: cwv.first_contentful_paint_ms ?? null, desktopValue: desktopCwv.first_contentful_paint_ms ?? null, format: formatMs, thresholdKey: 'fcp', explanation: 'Time until the first text or image appears on screen. Under 1.8s is good.' },
    { key: 'cls', label: 'Cumulative Layout Shift', techLabel: 'CLS', value: cwv.cumulative_layout_shift ?? null, desktopValue: desktopCwv.cumulative_layout_shift ?? null, format: formatCLS, thresholdKey: 'cls', explanation: 'Measures visual stability — how much the page layout shifts during loading. Under 0.1 is good.' },
    { key: 'tbt', label: 'Total Blocking Time', techLabel: 'TBT', value: cwv.total_blocking_time_ms ?? null, desktopValue: desktopCwv.total_blocking_time_ms ?? null, format: formatMs, thresholdKey: 'tbt', explanation: 'Total time the page is unresponsive to user input. Under 200ms is good.' },
  ];

  return (
    <>
      {/* ── TOP ROW: Headline Score Cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: space.md, marginTop: space.md }}>
        {headlineScores.map((cat) => {
          const score = Math.round(lhScores[cat.key] ?? 0);
          const bg = lighthouseScoreColor(score);
          const interp = scoreInterpretation(score);
          return (
            <div key={cat.key} style={{
              backgroundColor: color.bgCard,
              borderRadius: radius.xl,
              padding: space.lg,
              boxShadow: color.shadow,
              textAlign: 'center' as const,
              borderTop: `3px solid ${bg}`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: space.xs, marginBottom: space.sm }}>
                <span style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightSemibold, color: color.text }}>{cat.label}</span>
                <Tooltip text={cat.tooltip} />
              </div>
              <div style={{
                fontFamily: font.family,
                fontSize: '2.5rem',
                fontWeight: font.weightBold,
                color: bg,
                lineHeight: 1,
              }}>
                {score}
              </div>
              <div style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, marginTop: space.xs }}>
                {interp}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── SECTION 1: Site Speed Overview ── */}
      <h3 style={styles.sectionTitle}>Site Speed Overview</h3>
      <div style={{ ...styles.metricGrid, gridTemplateColumns: '1fr 1fr 1fr' }}>
        {/* Desktop Load Time */}
        <div style={styles.metricCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
            <span style={statusDot(cwvStatus('lcp', desktopCwv.largest_contentful_paint_ms ?? null))} />
            <span style={styles.metricLabel}>Desktop Load Time</span>
          </div>
          <div style={styles.metricValue}>{formatMs(desktopCwv.largest_contentful_paint_ms ?? null)}</div>
          <p style={styles.metricInterpretation}>How quickly the main content loads on desktop devices</p>
        </div>
        {/* Mobile Load Time */}
        <div style={styles.metricCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
            <span style={statusDot(cwvStatus('lcp', cwv.largest_contentful_paint_ms ?? null))} />
            <span style={styles.metricLabel}>Mobile Load Time</span>
          </div>
          <div style={styles.metricValue}>{formatMs(cwv.largest_contentful_paint_ms ?? null)}</div>
          <p style={styles.metricInterpretation}>How quickly the main content loads on mobile devices</p>
        </div>
        {/* Time to Interactive */}
        <div style={styles.metricCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
            <span style={statusDot(cwvStatus('tbt', cwv.total_blocking_time_ms ?? null))} />
            <span style={styles.metricLabel}>Time to Interactive</span>
          </div>
          <div style={styles.metricValue}>{formatMs(cwv.total_blocking_time_ms ?? null)}</div>
          <p style={styles.metricInterpretation}>How long before visitors can click, scroll, and interact</p>
        </div>
      </div>
      {/* Speed Index row */}
      {(cwv.speed_index_ms || desktopCwv.speed_index_ms) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: space.md, marginTop: space.md }}>
          <div style={styles.metricCard}>
            <span style={styles.metricLabel}>Desktop Speed Index</span>
            <div style={styles.metricValue}>{formatMs(desktopCwv.speed_index_ms ?? null)}</div>
            <p style={styles.metricInterpretation}>How quickly visible content populates the page on desktop</p>
          </div>
          <div style={styles.metricCard}>
            <span style={styles.metricLabel}>Mobile Speed Index</span>
            <div style={styles.metricValue}>{formatMs(cwv.speed_index_ms ?? null)}</div>
            <p style={styles.metricInterpretation}>How quickly visible content populates the page on mobile</p>
          </div>
        </div>
      )}

      {/* ── SECTION 2: Accessibility Overview ── */}
      <h3 style={styles.sectionTitle}>Accessibility Overview</h3>
      <div style={{
        backgroundColor: color.bgCard,
        borderRadius: radius.xl,
        padding: space.lg,
        boxShadow: color.shadow,
      }}>
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
                    {a11yCats.critical.map((t, i) => (
                      <li key={i} style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted }}>{t}</li>
                    ))}
                  </ul>
                </div>
              )}
              {a11yCats.moderate.length > 0 && (
                <div>
                  <span style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightBold, color: '#F59E0B' }}>
                    {a11yCats.moderate.length} Moderate
                  </span>
                  <ul style={{ margin: `${space.xxs} 0 0 0`, paddingLeft: space.md, listStyle: 'disc' }}>
                    {a11yCats.moderate.map((t, i) => (
                      <li key={i} style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted }}>{t}</li>
                    ))}
                  </ul>
                </div>
              )}
              {a11yCats.minor.length > 0 && (
                <div>
                  <span style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightBold, color: '#6B7280' }}>
                    {a11yCats.minor.length} Minor
                  </span>
                  <ul style={{ margin: `${space.xxs} 0 0 0`, paddingLeft: space.md, listStyle: 'disc' }}>
                    {a11yCats.minor.map((t, i) => (
                      <li key={i} style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted }}>{t}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, margin: 0 }}>
              {a11yCats.critical.length > 0
                ? 'Critical issues may prevent some visitors from using the site — addressing these first will have the most impact on WCAG AA compliance.'
                : 'No critical issues found. Addressing moderate and minor issues will improve overall accessibility and WCAG compliance.'}
            </p>
          </>
        )}
      </div>

      {/* ── SECTION 3: Technical Details (collapsed by default) ── */}
      <div style={{ marginTop: space.lg }}>
        <button
          onClick={() => setTechDetailsOpen(!techDetailsOpen)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: space.sm,
            background: 'none',
            border: `1px solid ${color.border}`,
            borderRadius: radius.lg,
            padding: `${space.sm} ${space.md}`,
            cursor: 'pointer',
            fontFamily: font.family,
            fontSize: font.sizeSm,
            fontWeight: font.weightSemibold,
            color: color.text,
            width: '100%',
            justifyContent: 'space-between',
          }}
        >
          <span>Technical Details — Core Web Vitals Reference</span>
          <span style={{ fontSize: font.sizeXs, color: color.textMuted }}>
            {techDetailsOpen ? '▲ Collapse' : '▼ Expand'}
          </span>
        </button>
        {techDetailsOpen && (
          <div style={{ marginTop: space.md }}>
            <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, margin: `0 0 ${space.md} 0` }}>
              These are the raw Core Web Vitals metrics used by Google to evaluate page experience. They are included here for technical reference.
            </p>
            <div style={styles.metricGrid}>
              {cwvMetrics.map((m) => {
                const level = cwvStatus(m.thresholdKey, m.value);
                const cwvItem = cwvInterps?.[CWV_INTERP_MAP[m.key]] as { what?: string; why?: string; where?: string } | undefined;
                return (
                  <div key={m.key} style={styles.metricCard}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: space.xs, marginBottom: space.xs }}>
                      <span style={statusDot(level)} />
                      <span style={{ ...styles.metricLabel, flex: 1 }}>{m.label} ({m.techLabel})</span>
                      <Tooltip text={CWV_TOOLTIPS[m.key]} />
                    </div>
                    <div style={styles.metricValue}>{m.format(m.value)}</div>
                    {m.desktopValue !== null && (
                      <div style={styles.desktopNote}>Desktop: {m.format(m.desktopValue)}</div>
                    )}
                    <p style={{ ...styles.metricInterpretation, fontStyle: 'italic' as const }}>{m.explanation}</p>
                    {cwvItem?.what && <p style={styles.metricInterpretation}>{cwvItem.what}</p>}
                    {cwvItem?.why && <p style={styles.metricWhy}>{cwvItem.why}</p>}
                    {cwvItem?.where && <p style={styles.metricWhere}>{cwvItem.where}</p>}
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
          <h3 style={styles.sectionTitle}>Technology Stack</h3>
          <div style={styles.card}>
            {Object.entries(groups).map(([label, names], i, arr) => (
              <div key={label} style={{
                ...styles.techRow,
                ...(i === arr.length - 1 ? { borderBottom: 'none' } : {}),
              }}>
                <span style={styles.techLabel}>{label}</span>
                <div style={styles.techTags}>
                  {names.map((name) => (
                    <span key={name} style={styles.techTag}>{name}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Observations & Findings */}
      {narrative && (
        <ObservationsCard
          projectId={data.project_id}
          lensId={data.lens_id}
          lensColor={lensColor}
          aiText={narrative}
          userText={data.user_observations}
        />
      )}
    </>
  );
}

/* ── SEO & AI Visibility ──────────────────────────── */

function SeoSection({ data }: { data: LensDetailData }) {
  const mobile = data.lighthouse_data.mobile || {};
  const audits = mobile.audits || [];
  const lensColor = data.lens_color;

  // Priority SEO audit IDs
  const priorityIds = [
    'meta-description', 'document-title', 'image-alt', 'robots-txt',
    'canonical', 'hreflang', 'structured-data', 'crawlable-anchors',
    'link-text', 'is-crawlable', 'http-status-code',
  ];

  const seoAudits = audits.filter((a) => a.category === 'seo');
  // Priority audits first, then rest
  const ordered: typeof seoAudits = [];
  const seen = new Set<string>();
  for (const id of priorityIds) {
    const a = seoAudits.find((x) => x.id === id);
    if (a) { ordered.push(a); seen.add(a.id); }
  }
  for (const a of seoAudits) {
    if (!seen.has(a.id)) ordered.push(a);
  }

  // SEO interpretation
  const seoInterp = data.interpretations.seo as Record<string, unknown> | undefined;
  const narrative = seoInterp?.section_narrative as string | undefined;
  const auditInterps = seoInterp?.audits as Record<string, { what?: string; why?: string }> | undefined;

  return (
    <>
      {/* SEO Health Checks */}
      <h3 style={styles.sectionTitle}>SEO Health Checks</h3>
      <div style={styles.card}>
        {ordered.length === 0 ? (
          <p style={{ ...styles.interpText, color: color.textMuted }}>No SEO audits available</p>
        ) : (
          ordered.map((audit, i) => {
            const passed = audit.score === 1 || audit.score === null;
            const isCriticalFail = !passed && (audit.id === 'robots-txt' || audit.id === 'meta-description' || audit.id === 'is-crawlable');
            return (
              <div key={audit.id} style={{
                ...styles.auditRow,
                ...(isCriticalFail ? { backgroundColor: '#FEF3C7' } : {}),
                ...(i === ordered.length - 1 ? { borderBottom: 'none' } : {}),
              }}>
                <span style={{ fontSize: '1rem', flexShrink: 0, width: 24, textAlign: 'center' }}>
                  {passed ? '✅' : '❌'}
                </span>
                <div style={{ flex: 1 }}>
                  <span style={styles.auditName}>{audit.title}</span>
                  {audit.description && (
                    <p style={styles.auditDesc}>
                      {audit.description.replace(/\[.*?\]\(.*?\)/g, '').trim().slice(0, 140)}
                    </p>
                  )}
                  {/* Show AI insight for failed audits */}
                  {!passed && auditInterps?.[audit.id]?.what && (
                    <p style={styles.auditInsight}>{auditInterps[audit.id].what}</p>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* AI Visibility Note */}
      <h3 style={styles.sectionTitle}>AI Visibility</h3>
      <div style={{ ...styles.card, backgroundColor: '#F0FDF4', borderLeft: `4px solid ${lensColor}` }}>
        <span style={{ ...styles.interpLabel, color: lensColor }}>ABOUT AI VISIBILITY</span>
        <p style={styles.interpText}>
          AI Visibility measures how well your site's content structure, metadata, and semantic markup
          make it readable and citable by AI tools like ChatGPT and Perplexity. Strong schema markup,
          clear heading hierarchies, and descriptive meta content help AI models accurately reference
          and recommend your site. This is an emerging dimension that Retina tracks alongside
          traditional SEO.
        </p>
      </div>

      {/* Observations & Findings */}
      {narrative && (
        <ObservationsCard
          projectId={data.project_id}
          lensId={data.lens_id}
          lensColor={lensColor}
          aiText={narrative}
          userText={data.user_observations}
        />
      )}
    </>
  );
}

/* ── Overall Observations Card (Brand, Experience, Conversion) ── */

function OverallObservationsCard({
  projectId,
  lensId,
  lensColor,
  data,
  onOpenCopilot,
}: {
  projectId: string;
  lensId: string;
  lensColor: string;
  data: LensDetailData;
  onOpenCopilot: () => void;
}) {
  // Merge observation sources: user edits > analyst observations > AI narrative
  const rawNarrative = data.interpretations.analyst_narrative;
  let aiText = data.analyst_observations || '';
  if (!aiText && typeof rawNarrative === 'string') {
    aiText = rawNarrative;
  } else if (!aiText && rawNarrative && typeof rawNarrative === 'object') {
    const narr = rawNarrative as Record<string, unknown>;
    const parts: string[] = [];
    if (narr.orientation) parts.push(String(narr.orientation));
    if (narr.what_good_looks_like) parts.push(String(narr.what_good_looks_like));
    aiText = parts.join('\n\n');
  }

  const displayText = data.user_observations ?? aiText;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(displayText);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await saveLensObservations(projectId, lensId, draft);
      setEditing(false);
    } catch { /* stay in edit mode */ }
    setSaving(false);
  };

  return (
    <>
      <div style={{ ...styles.card, borderLeft: `4px solid ${lensColor}`, marginTop: space.lg }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: space.md }}>
          <h3 style={{ ...styles.sectionTitle, margin: 0 }}>Overall Observations</h3>
          {!editing && (
            <div style={{ display: 'flex', gap: space.sm }}>
              <button
                style={styles.iconBtn}
                title="Retina Copilot"
                onClick={onOpenCopilot}
              >
                <SparkleIcon size={18} color={color.accent} />
              </button>
              <button
                style={styles.iconBtn}
                title="Edit observations"
                onClick={() => { setDraft(displayText); setEditing(true); }}
              >
                <PencilIcon size={16} />
              </button>
            </div>
          )}
        </div>

        {editing ? (
          <>
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              style={styles.obsTextarea}
              rows={8}
            />
            <div style={styles.obsActions}>
              <button style={styles.obsSaveBtn} onClick={handleSave} disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </button>
              <button style={styles.obsCancelBtn} onClick={() => setEditing(false)}>Cancel</button>
            </div>
          </>
        ) : (
          displayText ? (
            displayText.split('\n\n').map((para, i) => (
              <p key={i} style={styles.interpText}>{para}</p>
            ))
          ) : (
            <p style={{ ...styles.interpText, color: color.textMuted, fontStyle: 'italic' }}>
              No observations recorded yet. Click the pencil icon to add observations, or use Retina Copilot to generate them.
            </p>
          )
        )}
      </div>
    </>
  );
}

/* ── Analyst Lens Section (Brand, Experience, Conversion) ── */

function AnalystLensSection({ data, onOpenCopilot, onRefresh }: {
  data: LensDetailData;
  onOpenCopilot: () => void;
  onRefresh: () => void;
}) {
  return (
    <>
      {/* Overall Observations */}
      <OverallObservationsCard
        projectId={data.project_id}
        lensId={data.lens_id}
        lensColor={data.lens_color}
        data={data}
        onOpenCopilot={onOpenCopilot}
      />

      {/* Sub Dimensions Grid */}
      <SubDimensionGrid
        data={data}
        projectId={data.project_id}
        lensId={data.lens_id}
        onUpdated={onRefresh}
      />

      {/* Artifacts */}
      <ArtifactsRow
        artifacts={data.artifacts || []}
        projectId={data.project_id}
        lensId={data.lens_id}
        onUpdate={onRefresh}
      />
    </>
  );
}

/* ── Sub-dimension descriptions per analyst lens ──── */

const BRAND_DESCRIPTIONS: Record<string, string> = {
  brand_visual_language: 'Cohesion of logo, colors, typography, and imagery across all pages',
  brand_voice_messaging: 'Consistency and audience-appropriateness of written tone and messaging',
  value_proposition: 'Clarity and immediacy of what the company does and who it serves',
  brand_differentiation: 'How distinctly the brand stands apart from competitors visually and verbally',
};

const EXPERIENCE_DESCRIPTIONS: Record<string, string> = {
  interface_design: 'Overall aesthetic quality, polish, and modernity of the visual design',
  content_taxonomy: 'Organization of content with clear categories, labels, and hierarchy',
  navigation_architecture: 'Intuitiveness of site structure, menus, and findability within 2-3 clicks',
  responsiveness: 'Quality of the experience across mobile, tablet, and desktop devices',
};

const CONVERSION_DESCRIPTIONS: Record<string, string> = {
  call_to_action_logic: 'Clarity, visibility, and strategic placement of calls to action',
  lead_capture_form_design: 'Optimization of forms for completion — length, fields, progressive disclosure',
  trust_signals: 'Presence and effectiveness of testimonials, case studies, logos, and certifications',
  funnel_design: 'How naturally the path from awareness to conversion flows without dead ends',
};

const LENS_DESCRIPTIONS: Record<string, Record<string, string>> = {
  brand_messaging: BRAND_DESCRIPTIONS,
  experience_design: EXPERIENCE_DESCRIPTIONS,
  conversion_strategy: CONVERSION_DESCRIPTIONS,
};

/* ── Sub-dimension max scores per lens ──── */

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

/* ── Contextual placeholders per sub-dimension ──── */

const SUB_DIM_PLACEHOLDERS: Record<string, string> = {
  // Brand
  brand_visual_language: 'How consistently does the site communicate brand identity through color, typography, imagery, and layout across all pages?',
  brand_voice_messaging: 'Does the written content speak to the right audience with the right tone? Is the voice consistent and differentiated?',
  value_proposition: 'How clearly and compellingly does the site communicate what makes this company different and worth choosing?',
  brand_differentiation: 'What sets this brand apart visually and strategically from competitors? Could this site belong to anyone else?',
  // Experience
  interface_design: 'Assess the overall aesthetic quality, polish, and modernity of the visual design — layout, spacing, and visual hierarchy.',
  content_taxonomy: 'Is content well-organized with clear categories, logical grouping, and an intuitive information structure?',
  navigation_architecture: 'How intuitive is the site navigation? Can visitors find what they need within 2-3 clicks?',
  responsiveness: 'How well does the site adapt across desktop, tablet, and mobile device sizes? Any layout breaks or friction?',
  // Conversion
  call_to_action_logic: 'Are calls to action clear, visible, compelling, and strategically placed throughout the site?',
  lead_capture_form_design: 'Are lead capture forms well-designed, minimal, and user-friendly? Do they reduce friction?',
  trust_signals: 'Are there effective trust badges, testimonials, case studies, certifications, or social proof elements?',
  funnel_design: 'How well does the site guide visitors from awareness through consideration to conversion or contact?',
};

/* ── Sub Dimension Card Component ──── */

function SubDimensionCard({
  dimKey,
  score,
  maxScore,
  observation,
  lensColor,
  projectId,
  lensId,
  onUpdated,
}: {
  dimKey: string;
  score: number;
  maxScore: number;
  observation: string;
  lensColor: string;
  projectId: string;
  lensId: string;
  onUpdated: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draftScore, setDraftScore] = useState(score);
  const [draftObs, setDraftObs] = useState(observation);
  const [saving, setSaving] = useState(false);

  const placeholder = SUB_DIM_PLACEHOLDERS[dimKey] || 'Add observations for this sub-dimension…';

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateSubDimension(projectId, lensId, dimKey, draftScore, draftObs);
      setEditing(false);
      onUpdated();
    } catch { /* stay in edit mode */ }
    setSaving(false);
  };

  return (
    <div style={styles.card}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: space.md }}>
        <span style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightBold, color: color.text }}>
          {humanizeKey(dimKey)}
        </span>
        {!editing && (
          <button
            style={styles.iconBtn}
            title="Edit"
            onClick={() => { setDraftScore(score); setDraftObs(observation); setEditing(true); }}
          >
            <PencilIcon size={14} />
          </button>
        )}
      </div>

      {editing ? (
        <>
          {/* Score slider */}
          <div style={{ marginBottom: space.md }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: space.xxs }}>
              <span style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted }}>Score</span>
              <span style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightBold, color: lensColor }}>
                {draftScore.toFixed(1)} / {maxScore}
              </span>
            </div>
            <input
              type="range"
              min={0}
              max={maxScore}
              step={0.5}
              value={draftScore}
              onChange={(e) => setDraftScore(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: lensColor }}
            />
          </div>
          {/* Observation textarea */}
          <textarea
            value={draftObs}
            onChange={(e) => setDraftObs(e.target.value)}
            placeholder={placeholder}
            style={{ ...styles.obsTextarea, minHeight: 80 }}
            rows={3}
          />
          <div style={{ display: 'flex', gap: space.sm, marginTop: space.sm }}>
            <button style={styles.obsSaveBtn} onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button style={styles.obsCancelBtn} onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </>
      ) : (
        <div style={{ display: 'flex', gap: space.md, alignItems: 'flex-start' }}>
          <LensDonut score={score} maxScore={maxScore} lensColor={lensColor} diameter={56} />
          <p style={{
            margin: 0,
            fontFamily: font.family,
            fontSize: font.sizeSm,
            color: observation ? color.text : color.textMuted,
            lineHeight: 1.6,
            flex: 1,
            fontStyle: observation ? 'normal' : 'italic',
          }}>
            {observation || 'Awaiting analysis — click the pencil icon to add observations'}
          </p>
        </div>
      )}
    </div>
  );
}

/* ── Sub Dimension Grid ──── */

function SubDimensionGrid({
  data,
  projectId,
  lensId,
  onUpdated,
}: {
  data: LensDetailData;
  projectId: string;
  lensId: string;
  onUpdated: () => void;
}) {
  const maxScores = SUB_DIM_MAX[lensId] || {};
  const entries = Object.entries(data.analyst_sub_scores);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: space.xl, marginBottom: space.md }}>
        <h3 style={{ ...styles.sectionTitle, margin: 0 }}>Sub Dimensions</h3>
        <span style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textDim }}>
          4–5: Best in class · 3–3.5: Solid · 1.5–2.5: Notable gaps · 0.5–1: Critical
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: space.md }}>
        {entries.length === 0 ? (
          // Fallback: show expected sub-dimension structure with placeholders
          Object.entries(maxScores).map(([key, max]) => (
            <SubDimensionCard
              key={key}
              dimKey={key}
              score={0}
              maxScore={max}
              observation=""
              lensColor={data.lens_color}
              projectId={projectId}
              lensId={lensId}
              onUpdated={onUpdated}
            />
          ))
        ) : (
          entries.map(([key, val]) => (
            <SubDimensionCard
              key={key}
              dimKey={key}
              score={val.score}
              maxScore={maxScores[key] ?? 5}
              observation={val.observation || ''}
              lensColor={data.lens_color}
              projectId={projectId}
              lensId={lensId}
              onUpdated={onUpdated}
            />
          ))
        )}
      </div>
    </>
  );
}

/* ── Artifacts Row ───────────────────────────────── */

function ArtifactsRow({
  artifacts,
  projectId,
  lensId,
  onUpdate,
}: {
  artifacts: Artifact[];
  projectId: string;
  lensId: string;
  onUpdate: () => void;
}) {
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadArtifact(projectId, lensId, file);
      onUpdate();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Upload failed');
    }
    setUploading(false);
    e.target.value = '';
  };

  const handleDelete = async (artifactId: string) => {
    try {
      await deleteArtifact(projectId, lensId, artifactId);
      onUpdate();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  return (
    <div style={artifactStyles.wrapper}>
      <h3 style={artifactStyles.heading}>Artifacts</h3>
      <div style={artifactStyles.row}>
        {artifacts.map((a) => (
          <div key={a.id} style={artifactStyles.slot}>
            <img src={a.file_url} alt={a.file_name} style={artifactStyles.img} />
            <button
              style={artifactStyles.deleteBtn}
              onClick={() => handleDelete(a.id)}
              title="Remove artifact"
            >
              ×
            </button>
          </div>
        ))}
        {artifacts.length < 5 && (
          <label style={artifactStyles.uploadSlot}>
            <input
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              onChange={handleUpload}
              disabled={uploading}
            />
            {uploading ? (
              <span style={{ color: color.textMuted, fontSize: font.sizeXs }}>Uploading…</span>
            ) : (
              <>
                <span style={{ fontSize: '1.5rem', color: color.textDim }}>+</span>
                <span style={{ fontSize: font.sizeXs, color: color.textMuted }}>Upload</span>
              </>
            )}
          </label>
        )}
      </div>
    </div>
  );
}

const artifactStyles: Record<string, React.CSSProperties> = {
  wrapper: {
    marginTop: space.lg,
  },
  heading: {
    fontFamily: font.family,
    fontWeight: font.weightBold,
    fontSize: font.sizeLg,
    color: color.text,
    margin: `0 0 ${space.md} 0`,
  },
  row: {
    display: 'flex',
    gap: space.md,
    flexWrap: 'wrap',
  },
  slot: {
    position: 'relative',
    width: 120,
    height: 120,
    borderRadius: radius.lg,
    overflow: 'hidden',
    border: `1px solid ${color.border}`,
    backgroundColor: color.bgPage,
  } as React.CSSProperties,
  img: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  deleteBtn: {
    position: 'absolute',
    top: 4,
    right: 4,
    width: 24,
    height: 24,
    borderRadius: '50%',
    border: 'none',
    backgroundColor: 'rgba(0,0,0,0.6)',
    color: '#fff',
    fontSize: '14px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    lineHeight: 1,
  } as React.CSSProperties,
  uploadSlot: {
    width: 120,
    height: 120,
    borderRadius: radius.lg,
    border: `2px dashed ${color.border}`,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    gap: space.xs,
    backgroundColor: color.bgCard,
    transition: 'border-color 0.15s',
  } as React.CSSProperties,
};

/* ══════════════════════════════════════════════════════
   MAIN PAGE COMPONENT
   ══════════════════════════════════════════════════════ */

export function LensDetail() {
  const { projectId, lensId } = useParams<{ projectId: string; lensId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState<LensDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [copilotOpen, setCopilotOpen] = useState(false);

  // ── Export state ──
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [exportStatus, setExportStatus] = useState<ExportStatusResponse['status']>('none');
  const [exportUrl, setExportUrl] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const exportPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopExportPoll = useCallback(() => {
    if (exportPollRef.current) {
      clearInterval(exportPollRef.current);
      exportPollRef.current = null;
    }
  }, []);

  useEffect(() => () => stopExportPoll(), [stopExportPoll]);

  useEffect(() => {
    if (!projectId || !lensId) return;
    setLoading(true);
    setError(null);
    getLensDetail(projectId, lensId)
      .then(setData)
      .catch((err) => setError(err.message ?? 'Failed to load lens data'))
      .finally(() => setLoading(false));
  }, [projectId, lensId]);

  const sidebarUser = {
    id: user?.id ?? '',
    name: user?.name ?? 'User',
    role: user?.role ?? '',
  };

  const dismissToast = useCallback(() => setToastMsg(null), []);
  const handleShare = () => setToastMsg('Share Project — coming soon');

  const handleExport = async () => {
    if (!projectId) return;
    setExportModalOpen(true);
    setExportStatus('pending');
    setExportUrl(null);
    setExportError(null);

    try {
      await startPdfExport(projectId);
      exportPollRef.current = setInterval(async () => {
        try {
          const status = await getExportStatus(projectId);
          setExportStatus(status.status);
          if (status.status === 'complete') {
            setExportUrl(status.download_url);
            stopExportPoll();
          } else if (status.status === 'error') {
            setExportError(status.error || 'Export failed');
            stopExportPoll();
          }
        } catch {
          // keep polling on transient errors
        }
      }, 3000);
    } catch (err) {
      setExportStatus('error');
      setExportError(err instanceof Error ? err.message : 'Failed to start export');
    }
  };

  const handleExportRetry = () => {
    stopExportPoll();
    handleExport();
  };

  const closeExportModal = () => {
    stopExportPoll();
    setExportModalOpen(false);
  };

  if (loading) {
    return (
      <div style={styles.layout}>
        <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
        <main style={styles.main}>
          <p style={styles.loadingText}>Loading lens data…</p>
        </main>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={styles.layout}>
        <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
        <main style={styles.main}>
          <div style={styles.errorBanner}>{error ?? 'Lens data not found'}</div>
          <button style={styles.backBtn} onClick={() => navigate(`/projects/${projectId}`)}>
            ← Back to Summary
          </button>
        </main>
      </div>
    );
  }

  return (
    <div style={styles.layout}>
      <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />

      <main style={styles.main}>
        {/* ── PAGE HEADER ─────────────────────────────── */}
        <div style={styles.pageHeader}>
          <h1 style={styles.pageTitle}>
            <span style={styles.pageTitlePrefix}>Project</span>
            <span style={styles.pageTitleDivider}> | </span>
            <span
              style={styles.pageTitleName}
              onClick={() => navigate(`/projects/${projectId}`)}
            >
              {data.project_name}
            </span>
          </h1>
          <div style={styles.headerActions}>
            <button style={styles.secondaryBtn} onClick={handleShare}>
              Share Project <ArrowCircleIcon />
            </button>
            <button style={styles.primaryBtn} onClick={handleExport}>
              Export Report <ArrowCircleIcon />
            </button>
          </div>
        </div>

        {/* ── LENS NAVIGATION BAR ─────────────────────── */}
        <div style={styles.lensBar}>
          {data.lens_scores.map((lens) => {
            const isActive = lens.lens_id === lensId;
            return (
              <button
                key={lens.lens_id}
                style={{
                  ...styles.lensTab,
                  ...(isActive ? styles.lensTabActive : {}),
                }}
                onClick={() => {
                  if (isActive) {
                    navigate(`/projects/${projectId}`);
                  } else {
                    navigate(`/projects/${projectId}/lens/${lens.lens_id}`);
                  }
                }}
              >
                <img src={LENS_ICONS[lens.lens_id]} alt="" style={styles.lensIcon} />
                <span style={styles.lensTabName}>{lens.lens_name}</span>
              </button>
            );
          })}
        </div>

        {/* ── LENS HEADER ROW ─────────────────────────── */}
        <div style={styles.titleRow}>
          <LensDonut score={data.lens_score} maxScore={data.max_score} lensColor={data.lens_color} diameter={80} />
          <div>
            <h2 style={styles.lensTitle}>{data.lens_name}</h2>
            <p style={styles.lensDefinition}>{LENS_DEFINITIONS[data.lens_id] ?? ''}</p>
          </div>
        </div>

        {/* ── LENS CONTENT ────────────────────────────── */}
        <div style={styles.contentArea}>
          {data.lens_id === 'performance_technical_health' && (
            <PerformanceSection data={data} />
          )}
          {data.lens_id === 'seo_ai_visibility' && (
            <SeoSection data={data} />
          )}
          {(data.lens_id === 'brand_messaging' || data.lens_id === 'experience_design' || data.lens_id === 'conversion_strategy') && (
            <AnalystLensSection
              data={data}
              onOpenCopilot={() => setCopilotOpen(true)}
              onRefresh={() => {
                if (projectId && lensId) {
                  getLensDetail(projectId, lensId).then(setData);
                }
              }}
            />
          )}
        </div>
      </main>

      {/* Copilot Panel */}
      <CopilotPanel
        open={copilotOpen}
        onClose={() => setCopilotOpen(false)}
        lensName={data.lens_name}
        currentObservations={data.user_observations ?? data.analyst_observations ?? ''}
        onCommit={async (text) => {
          await saveLensObservations(data.project_id, data.lens_id, text);
          if (projectId && lensId) {
            const fresh = await getLensDetail(projectId, lensId);
            setData(fresh);
          }
        }}
        onSend={async (message: string, history: CopilotMessage[]) => {
          const result = await sendCopilotMessage(
            data.project_id,
            data.lens_id,
            message,
            history,
            {
              project_name: data.project_name,
              site_url: '', // filled from project context
              lens_name: data.lens_name,
              lens_definition: LENS_DEFINITIONS[data.lens_id] ?? '',
              sub_scores: data.analyst_sub_scores,
              current_observations: data.user_observations ?? data.analyst_observations ?? '',
            },
          );
          return result.response;
        }}
      />

      {/* Export Modal */}
      {exportModalOpen && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 9999,
        }} onClick={closeExportModal}>
          <div style={{
            background: '#fff', borderRadius: 12, padding: '32px 36px',
            width: 420, maxWidth: '90vw', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
          }} onClick={(e) => e.stopPropagation()}>

            {exportStatus === 'complete' && exportUrl ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>✓</div>
                <h3 style={{ fontSize: 18, fontWeight: 600, color: '#0A0A2E', marginBottom: 8 }}>
                  Your report is ready
                </h3>
                <a
                  href={exportUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: 'inline-block', marginTop: 16, padding: '10px 28px',
                    background: '#076EFF', color: '#fff', borderRadius: 20,
                    fontWeight: 600, fontSize: 14, textDecoration: 'none',
                  }}
                >
                  Download Report
                </a>
                <div style={{ marginTop: 16 }}>
                  <button onClick={closeExportModal} style={{
                    background: 'none', border: 'none', color: '#6B7280',
                    fontSize: 13, cursor: 'pointer',
                  }}>Close</button>
                </div>
              </div>
            ) : exportStatus === 'error' ? (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>⚠</div>
                <h3 style={{ fontSize: 18, fontWeight: 600, color: '#0A0A2E', marginBottom: 8 }}>
                  Export Failed
                </h3>
                <p style={{ color: '#EF4444', fontSize: 13, marginBottom: 16 }}>
                  {exportError || 'An unexpected error occurred'}
                </p>
                <button onClick={handleExportRetry} style={{
                  padding: '10px 28px', background: '#076EFF', color: '#fff',
                  borderRadius: 20, fontWeight: 600, fontSize: 14, border: 'none',
                  cursor: 'pointer',
                }}>Try Again</button>
                <div style={{ marginTop: 12 }}>
                  <button onClick={closeExportModal} style={{
                    background: 'none', border: 'none', color: '#6B7280',
                    fontSize: 13, cursor: 'pointer',
                  }}>Close</button>
                </div>
              </div>
            ) : (
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 600, color: '#0A0A2E', marginBottom: 20 }}>
                  Generating Report
                </h3>
                {[
                  { label: 'Gathering report data', done: exportStatus !== 'pending' },
                  { label: 'Building charts', done: exportStatus === 'generating' || exportStatus === 'complete' },
                  { label: 'Assembling pages', done: exportStatus === 'generating' || exportStatus === 'complete' },
                  { label: 'Finalizing PDF', done: false },
                ].map((step, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', padding: '8px 0',
                    color: step.done ? '#0A0A2E' : '#6B7280',
                  }}>
                    <span style={{
                      width: 24, height: 24, borderRadius: '50%', marginRight: 12,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 13, flexShrink: 0,
                      background: step.done ? '#076EFF' : 'transparent',
                      color: step.done ? '#fff' : '#6B7280',
                      border: step.done ? 'none' : '2px solid #E2E8F0',
                      animation: (!step.done && i === (exportStatus === 'pending' ? 0 : 2)) ? 'spin 1s linear infinite' : 'none',
                    }}>
                      {step.done ? '✓' : ''}
                    </span>
                    <span style={{ fontSize: 14 }}>{step.label}</span>
                  </div>
                ))}
                <p style={{ fontSize: 12, color: '#6B7280', marginTop: 16 }}>
                  This usually takes 15–30 seconds
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {toastMsg && <Toast message={toastMsg} onDone={dismissToast} />}
    </div>
  );
}

/* ══════════════════════════════════════════════════════
   STYLES
   ══════════════════════════════════════════════════════ */

const styles: Record<string, React.CSSProperties> = {
  layout: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: color.bgPage,
  },
  main: {
    flex: 1,
    marginLeft: sidebarToken.width,
    padding: `${space.xl} ${space.xxl}`,
    maxWidth: 1100,
  },
  loadingText: {
    fontFamily: font.family,
    fontSize: font.sizeMd,
    color: color.textMuted,
    padding: space.xl,
  },
  errorBanner: {
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: '#FEE2E2',
    color: color.error,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    textAlign: 'center',
    marginBottom: space.md,
  },
  backBtn: {
    padding: `${space.sm} ${space.md}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.pill,
    backgroundColor: 'transparent',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.text,
    cursor: 'pointer',
  },

  /* Page header */
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
  pageTitlePrefix: { color: color.textMuted },
  pageTitleDivider: { color: color.textDim, fontWeight: font.weightRegular },
  pageTitleName: {
    fontWeight: font.weightRegular,
    cursor: 'pointer',
    transition: 'opacity 0.15s',
  } as React.CSSProperties,
  headerActions: { display: 'flex', gap: space.sm, flexShrink: 0 },
  secondaryBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: `${space.sm} ${space.lg}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.pill,
    backgroundColor: color.bgCard,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    color: color.text,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  primaryBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: `${space.sm} ${space.lg}`,
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },

  /* Lens bar */
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
  lensTabActive: {
    borderBottom: '2px solid #076EFF',
  },
  lensIcon: { width: 36, height: 36, flexShrink: 0 },
  lensTabName: {
    lineHeight: 1.3,
    display: 'block',
    width: '100%',
    textAlign: 'center',
    wordBreak: 'keep-all' as const,
    overflowWrap: 'break-word' as const,
  },

  /* Title row */
  titleRow: {
    display: 'flex',
    alignItems: 'center',
    marginBottom: space.xl,
    gap: space.lg,
  },
  lensTitle: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightBold,
    fontSize: '1.75rem',
    color: color.text,
  },
  lensDefinition: {
    margin: 0,
    marginTop: space.xxs,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },

  /* Content area */
  contentArea: {
    display: 'flex',
    flexDirection: 'column',
    gap: 0,
  },

  /* Section titles */
  sectionTitle: {
    margin: 0,
    marginBottom: space.md,
    marginTop: space.lg,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeLg,
    color: color.text,
  },

  /* CWV metric cards */
  metricGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: space.md,
  },
  metricCard: {
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    padding: space.lg,
    boxShadow: color.shadow,
  },
  metricLabel: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    color: color.text,
  },
  metricValue: {
    fontFamily: font.family,
    fontSize: font.size2xl,
    fontWeight: font.weightBold,
    color: color.text,
    marginTop: space.xs,
  },
  desktopNote: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    marginTop: space.xxs,
  },
  metricInterpretation: {
    margin: 0,
    marginTop: space.sm,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.text,
    lineHeight: 1.5,
  },
  metricWhy: {
    margin: 0,
    marginTop: space.xxs,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    lineHeight: 1.5,
  },
  metricWhere: {
    margin: 0,
    marginTop: space.xxs,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.accent,
    fontStyle: 'italic',
    lineHeight: 1.5,
  },
  divergenceNote: {
    color: '#E74C3C',
    fontWeight: font.weightMedium,
  },

  /* Lighthouse score pills */
  pillRow: {
    display: 'flex',
    gap: space.sm,
    flexWrap: 'wrap',
  },
  scorePill: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: `${space.xs} ${space.md}`,
    borderRadius: radius.pill,
    color: '#FFFFFF',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    whiteSpace: 'nowrap',
  },

  lighthouseHelper: {
    margin: 0,
    marginTop: space.xs,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textDim,
    fontStyle: 'italic',
  },

  /* Card (shared) */
  card: {
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    padding: space.xl,
    boxShadow: color.shadow,
  },

  /* Tech stack */
  techRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: space.md,
    padding: `${space.sm} 0`,
    borderBottom: `1px solid ${color.border}`,
  },
  techLabel: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    color: color.text,
    minWidth: 100,
    flexShrink: 0,
    paddingTop: space.xxs,
  },
  techTags: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: space.xs,
    flex: 1,
  },
  techTag: {
    display: 'inline-block',
    padding: `${space.xxs} ${space.sm}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.pill,
    backgroundColor: color.bgCard,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.text,
    whiteSpace: 'nowrap',
  },

  /* Interpretation card */
  interpLabel: {
    display: 'block',
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightSemibold,
    color: color.textMuted,
    letterSpacing: '0.05em',
    marginBottom: space.sm,
  },
  interpText: {
    margin: 0,
    marginBottom: space.xs,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.text,
    lineHeight: 1.7,
  },
  editObsBtn: {
    padding: `${space.xxs} ${space.sm}`,
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    background: 'none',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
    flexShrink: 0,
  } as React.CSSProperties,
  obsTextarea: {
    width: '100%',
    minHeight: 160,
    padding: space.sm,
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    lineHeight: 1.7,
    color: color.text,
    resize: 'vertical' as const,
    boxSizing: 'border-box' as const,
    outline: 'none',
  },
  obsActions: {
    display: 'flex',
    gap: space.sm,
    alignItems: 'center',
    marginTop: space.sm,
    flexWrap: 'wrap' as const,
  },
  obsSaveBtn: {
    padding: `${space.xxs} ${space.md}`,
    borderRadius: 999,
    border: 'none',
    background: color.accent,
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
  } as React.CSSProperties,
  obsCancelBtn: {
    padding: `${space.xxs} ${space.md}`,
    borderRadius: 999,
    border: `1px solid ${color.border}`,
    background: 'none',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    cursor: 'pointer',
  } as React.CSSProperties,
  obsResetLink: {
    background: 'none',
    border: 'none',
    color: color.textDim,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    cursor: 'pointer',
    textDecoration: 'underline',
    padding: 0,
  } as React.CSSProperties,
  obsResetConfirm: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textDim,
  },
  obsEditedBadge: {
    display: 'inline-block',
    marginTop: space.xs,
    padding: `1px ${space.xs}`,
    borderRadius: radius.sm,
    backgroundColor: '#EBF5FF',
    color: color.accent,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightMedium,
  } as React.CSSProperties,

  /* SEO audit rows */
  auditRow: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: space.sm,
    padding: `${space.sm} ${space.xs}`,
    borderBottom: `1px solid ${color.border}`,
    borderRadius: radius.sm,
  },
  auditName: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    color: color.text,
    display: 'block',
  },
  auditDesc: {
    margin: 0,
    marginTop: 2,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    lineHeight: 1.4,
  },
  auditInsight: {
    margin: 0,
    marginTop: space.xxs,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.accent,
    fontStyle: 'italic',
    lineHeight: 1.4,
  },

  /* Sub-score bars (analyst lenses) */
  subScoreRow: {
    padding: `${space.sm} 0`,
    borderBottom: `1px solid ${color.border}`,
  },
  subScoreName: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    color: color.text,
  },
  subScoreValue: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    color: color.textMuted,
  },
  barTrack: {
    width: '100%',
    height: 8,
    borderRadius: radius.pill,
    backgroundColor: '#E5E7EB',
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: radius.pill,
    transition: 'width 0.5s ease',
  },
  barHelper: {
    margin: 0,
    marginTop: space.xxs,
    fontFamily: font.family,
    fontSize: '0.65rem',
    color: color.textDim,
  },
  tooltipIcon: {
    marginLeft: space.xxs,
    fontSize: font.sizeXs,
    color: color.textDim,
    cursor: 'help',
  },

  /* Icon button (sparkle, pencil) */
  iconBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 32,
    height: 32,
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    background: 'none',
    cursor: 'pointer',
    padding: 0,
    transition: 'background 0.15s',
  } as React.CSSProperties,

  /* Toast */
  toast: {
    position: 'fixed',
    bottom: space.xl,
    left: '50%',
    transform: 'translateX(-50%)',
    padding: `${space.sm} ${space.xl}`,
    borderRadius: radius.pill,
    backgroundColor: color.text,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
    zIndex: 9999,
  },
};
