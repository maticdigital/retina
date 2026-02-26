import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { verifyShareToken, ApiError } from '../api';
import type { SharedProjectData, SharedLensData, LensScore, RecommendationQuadrant, TechStack } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';

/* ── Constants ────────────────────────────────────── */

const LENS_ICONS: Record<string, string> = {
  performance_technical_health: 'P',
  seo_ai_visibility: 'S',
  brand_messaging: 'B',
  experience_design: 'E',
  conversion_strategy: 'C',
};

const SUB_DIM_LABELS: Record<string, string> = {
  brand_visual_language: 'Brand Visual Language',
  brand_voice_messaging: 'Brand Voice & Messaging',
  value_proposition: 'Value Proposition',
  brand_differentiation: 'Brand Differentiation',
  interface_design: 'Interface Design',
  content_taxonomy: 'Content Taxonomy',
  navigation_architecture: 'Navigation Architecture',
  responsiveness: 'Responsiveness',
  call_to_action_logic: 'Call-to-Action Logic',
  lead_capture_form_design: 'Lead Capture & Forms',
  trust_signals: 'Trust Signals',
  funnel_design: 'Funnel Design',
};

const QUADRANT_ICONS: Record<string, string> = {
  'No Brainers': '🎯',
  'Quick Wins': '⚡',
  'Growth Moves': '📈',
  'Transformational': '🚀',
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

/* ── Report Viewer ────────────────────────────────── */

function ReportViewer({ data }: { data: SharedProjectData }) {
  const { project, lenses } = data;

  return (
    <div style={viewStyles.layout}>
      {/* Sidebar — logo only */}
      <aside style={viewStyles.sidebar}>
        <div style={viewStyles.sidebarLogo}>
          <svg width="28" height="28" viewBox="0 0 664 664" fill="none">
            <path
              d="M332 20C149 20 0 169 0 352h87c0-135 110-245 245-245s245 110 245 245h87C664 169 515 20 332 20Zm101 332c0-56-45-101-101-101s-101 45-101 101 45 101 101 101 101-45 101-101Zm87 0c0 104-85 188-188 188S144 456 144 352s85-188 188-188 188 85 188 188Zm-130 0c0 32-26 58-58 58s-58-26-58-58 26-58 58-58 58 26 58 58Z"
              fill={color.text}
            />
          </svg>
          <div>
            <div style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: font.sizeBase, color: color.text, lineHeight: 1.15 }}>Matic</div>
            <div style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: font.sizeBase, color: color.text, lineHeight: 1.15 }}>Retina</div>
          </div>
        </div>
        <div style={viewStyles.sidebarBadge}>Shared Report</div>
      </aside>

      {/* Main content */}
      <main style={viewStyles.main}>
        {/* Header */}
        <div style={viewStyles.header}>
          <h1 style={viewStyles.projectName}>{project.name}</h1>
          <a href={project.primary_url} target="_blank" rel="noopener noreferrer" style={viewStyles.projectUrl}>
            {project.primary_url}
          </a>
        </div>

        {/* Retina Score + Lens Scores */}
        <div style={viewStyles.scoreSection}>
          <div style={viewStyles.retinaScoreCard}>
            <div style={viewStyles.retinaScoreValue}>
              {project.retina_score != null ? Math.round(project.retina_score) : '—'}
            </div>
            <div style={viewStyles.retinaScoreLabel}>Retina Score</div>
            <div style={viewStyles.retinaScoreMax}>/100</div>
          </div>
          <div style={viewStyles.lensScoreGrid}>
            {project.lens_scores.map((ls: LensScore) => (
              <LensScoreCard key={ls.lens_id} lens={ls} />
            ))}
          </div>
        </div>

        {/* Tech Stack */}
        {project.tech_stack && Object.keys(project.tech_stack).length > 0 && (
          <TechStackSection techStack={project.tech_stack} />
        )}

        {/* Lens Detail Sections */}
        {lenses.map((lens) => (
          <LensSection key={lens.lens_id} lens={lens} />
        ))}

        {/* Recommendations */}
        {project.recommendations.length > 0 && (
          <RecommendationsSection recommendations={project.recommendations} />
        )}

        {/* Footer */}
        <div style={viewStyles.footer}>
          <span style={{ color: color.textDim, fontFamily: font.family, fontSize: font.sizeSm }}>
            Generated by Matic Retina
          </span>
        </div>
      </main>
    </div>
  );
}

/* ── Sub-components ───────────────────────────────── */

function LensScoreCard({ lens }: { lens: LensScore }) {
  const lensColors: Record<string, string> = {
    performance_technical_health: '#076EFF',
    seo_ai_visibility: '#00C864',
    brand_messaging: '#9B59B6',
    experience_design: '#E74C3C',
    conversion_strategy: '#FF8C00',
  };
  const lc = lensColors[lens.lens_id] || color.accent;

  return (
    <div style={{ ...viewStyles.lensScoreItem, borderTop: `3px solid ${lc}` }}>
      <div style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.textMuted, marginBottom: 4 }}>
        {lens.lens_name}
      </div>
      <div style={{ fontFamily: font.family, fontSize: font.sizeXl, fontWeight: font.weightBold, color: lc }}>
        {lens.score != null ? lens.score : '—'}
      </div>
      <div style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textDim }}>
        /{lens.max_score}
      </div>
    </div>
  );
}

function TechStackSection({ techStack }: { techStack: TechStack }) {
  const labels: Record<string, string> = { cms: 'CMS', analytics: 'Analytics', crm: 'CRM', framework: 'Framework', hosting: 'Hosting', cdn: 'CDN' };
  const entries = Object.entries(techStack as Record<string, string[] | undefined>).filter(([, v]) => v && v.length > 0);
  if (entries.length === 0) return null;

  return (
    <div style={viewStyles.section}>
      <h2 style={viewStyles.sectionTitle}>Technology Stack</h2>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: space.lg }}>
        {entries.map(([key, items]) => (
          <div key={key}>
            <div style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightSemibold, color: color.textDim, textTransform: 'uppercase' as const, letterSpacing: '0.04em', marginBottom: 6 }}>
              {labels[key] || key}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {(items || []).map((t) => (
                <span key={t} style={viewStyles.techBadge}>{t}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LensSection({ lens }: { lens: SharedLensData }) {
  const subEntries = Object.entries(lens.analyst_sub_scores);
  const hasSubScores = subEntries.some(([, v]) => v.score > 0);
  const hasObservations = !!(lens.analyst_observations || lens.user_observations);
  const hasInterpretations = Object.keys(lens.interpretations).length > 0;

  if (!hasSubScores && !hasObservations && !hasInterpretations) return null;

  return (
    <div style={viewStyles.section}>
      <div style={{ display: 'flex', alignItems: 'center', gap: space.sm, marginBottom: space.md }}>
        <div style={{
          width: 36, height: 36, borderRadius: '50%',
          background: lens.lens_color, color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: font.family, fontWeight: font.weightBold, fontSize: font.sizeBase,
        }}>
          {LENS_ICONS[lens.lens_id] || '?'}
        </div>
        <div>
          <h2 style={{ ...viewStyles.sectionTitle, marginBottom: 0 }}>{lens.lens_name}</h2>
          {lens.lens_score != null && (
            <span style={{ fontFamily: font.family, fontSize: font.sizeSm, color: lens.lens_color, fontWeight: font.weightSemibold }}>
              {lens.lens_score} / {lens.max_score}
            </span>
          )}
        </div>
      </div>

      {/* Sub-dimension scores */}
      {hasSubScores && (
        <div style={viewStyles.subGrid}>
          {subEntries.map(([key, val]) => (
            <div key={key} style={viewStyles.subCard}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightMedium, color: color.text }}>
                  {SUB_DIM_LABELS[key] || key.replace(/_/g, ' ')}
                </span>
                <span style={{
                  fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightBold,
                  color: val.score >= 4 ? color.success : val.score >= 2.5 ? color.warning : color.error,
                }}>
                  {val.score}/5
                </span>
              </div>
              {/* Score bar */}
              <div style={{ height: 4, borderRadius: 2, background: color.bgPage, overflow: 'hidden' }}>
                <div style={{
                  height: '100%', borderRadius: 2,
                  width: `${(val.score / 5) * 100}%`,
                  background: val.score >= 4 ? color.success : val.score >= 2.5 ? color.warning : color.error,
                }} />
              </div>
              {val.observation && (
                <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, marginTop: 8, marginBottom: 0, lineHeight: 1.5 }}>
                  {val.observation}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Observations */}
      {(lens.user_observations || lens.analyst_observations) && (
        <div style={viewStyles.observationBox}>
          <div style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightSemibold, color: color.textDim, textTransform: 'uppercase' as const, letterSpacing: '0.04em', marginBottom: 8 }}>
            Observations
          </div>
          <p style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.text, lineHeight: 1.6, margin: 0, whiteSpace: 'pre-wrap' as const }}>
            {lens.user_observations || lens.analyst_observations}
          </p>
        </div>
      )}

      {/* Artifacts */}
      {lens.artifacts.length > 0 && (
        <div style={{ marginTop: space.md }}>
          <div style={{ fontFamily: font.family, fontSize: font.sizeXs, fontWeight: font.weightSemibold, color: color.textDim, textTransform: 'uppercase' as const, letterSpacing: '0.04em', marginBottom: 8 }}>
            Artifacts
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: space.xs }}>
            {lens.artifacts.map((a) => (
              <a key={a.id} href={a.file_url} target="_blank" rel="noopener noreferrer" style={viewStyles.artifactLink}>
                {a.file_name}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RecommendationsSection({ recommendations }: { recommendations: RecommendationQuadrant[] }) {
  const nonEmpty = recommendations.filter((r) => r.items.length > 0);
  if (nonEmpty.length === 0) return null;

  return (
    <div style={viewStyles.section}>
      <h2 style={viewStyles.sectionTitle}>Recommendations</h2>
      <div style={viewStyles.recGrid}>
        {nonEmpty.map((q) => (
          <div key={q.quadrant} style={viewStyles.recCard}>
            <div style={{ fontFamily: font.family, fontSize: font.sizeSm, fontWeight: font.weightSemibold, color: color.text, marginBottom: space.sm }}>
              {QUADRANT_ICONS[q.quadrant] || ''} {q.quadrant}
            </div>
            <ul style={{ margin: 0, paddingLeft: 18, listStyleType: 'disc' }}>
              {q.items.map((item, i) => {
                const title = typeof item === 'string' ? item : item.title;
                const desc = typeof item === 'string' ? null : item.description;
                return (
                  <li key={i} style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.text, marginBottom: 6, lineHeight: 1.5 }}>
                    <strong>{title}</strong>
                    {desc && <span style={{ color: color.textMuted }}> — {desc}</span>}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Viewer Styles ────────────────────────────────── */

const viewStyles: Record<string, React.CSSProperties> = {
  layout: {
    display: 'flex',
    minHeight: '100vh',
    backgroundColor: color.bgPage,
  },
  sidebar: {
    width: sidebarToken.width,
    minWidth: sidebarToken.width,
    backgroundColor: sidebarToken.bgColor,
    borderRight: `1px solid ${color.border}`,
    padding: `${space.lg} ${space.md}`,
    position: 'sticky' as const,
    top: 0,
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
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
    padding: `${space.xl} ${space.xxl}`,
    maxWidth: 960,
  },
  header: {
    marginBottom: space.xl,
  },
  projectName: {
    fontFamily: font.family,
    fontSize: font.size2xl,
    fontWeight: font.weightBold,
    color: color.text,
    margin: 0,
    marginBottom: space.xxs,
  },
  projectUrl: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.accent,
    textDecoration: 'none',
  },
  scoreSection: {
    display: 'flex',
    gap: space.lg,
    marginBottom: space.xl,
    alignItems: 'flex-start',
    flexWrap: 'wrap' as const,
  },
  retinaScoreCard: {
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    padding: space.lg,
    boxShadow: color.shadow,
    textAlign: 'center' as const,
    minWidth: 120,
  },
  retinaScoreValue: {
    fontFamily: font.family,
    fontSize: '2.5rem',
    fontWeight: font.weightBold,
    color: color.accent,
    lineHeight: 1,
  },
  retinaScoreLabel: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
    marginTop: 4,
  },
  retinaScoreMax: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textDim,
  },
  lensScoreGrid: {
    display: 'flex',
    gap: space.sm,
    flexWrap: 'wrap' as const,
    flex: 1,
  },
  lensScoreItem: {
    backgroundColor: color.bgCard,
    borderRadius: radius.md,
    padding: `${space.sm} ${space.md}`,
    boxShadow: color.shadow,
    textAlign: 'center' as const,
    flex: '1 1 100px',
    minWidth: 100,
  },
  section: {
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    padding: space.lg,
    boxShadow: color.shadow,
    marginBottom: space.lg,
  },
  sectionTitle: {
    fontFamily: font.family,
    fontSize: font.sizeLg,
    fontWeight: font.weightSemibold,
    color: color.text,
    margin: 0,
    marginBottom: space.md,
  },
  techBadge: {
    display: 'inline-block',
    padding: '3px 10px',
    borderRadius: radius.pill,
    fontSize: font.sizeXs,
    fontWeight: font.weightMedium,
    fontFamily: font.family,
    background: color.bgPage,
    color: color.text,
    border: `1px solid ${color.border}`,
  },
  subGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))',
    gap: space.sm,
    marginBottom: space.md,
  },
  subCard: {
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: color.bgPage,
  },
  observationBox: {
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: color.bgPage,
    marginTop: space.sm,
  },
  artifactLink: {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: radius.pill,
    fontSize: font.sizeXs,
    fontFamily: font.family,
    fontWeight: font.weightMedium,
    color: color.accent,
    background: color.accentLight,
    textDecoration: 'none',
  },
  recGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: space.md,
  },
  recCard: {
    padding: space.md,
    borderRadius: radius.md,
    backgroundColor: color.bgPage,
  },
  footer: {
    textAlign: 'center' as const,
    padding: `${space.xl} 0`,
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
