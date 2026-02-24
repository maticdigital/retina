import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getProjectSummary, generateRecommendations, saveRecommendations, addCompetitor, removeCompetitor, refreshProject } from '../api';
import type { ProjectSummary, LensScore, RecommendationQuadrant, RecommendationItem, QuadrantData } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import { Sidebar } from '../components/Sidebar';
import { NAV_ITEMS } from './Dashboard';

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

/* ── Toast ────────────────────────────────────────── */

function Toast({ message, onDone }: { message: string; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2500);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <div style={styles.toast}>
      {message}
    </div>
  );
}

/* ── Donut Chart ──────────────────────────────────── */

function ScoreDonut({ lensScores, retinaScore }: { lensScores: LensScore[]; retinaScore: number | null }) {
  const size = 180;
  const strokeWidth = 22;
  const r = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * r;

  const totalMax = lensScores.reduce((s, l) => s + l.max_score, 0);
  let offset = 0;

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Background ring */}
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#E5E7EB" strokeWidth={strokeWidth} />
      {/* Lens arcs */}
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
          <circle
            key={lens.lens_id}
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={lens.score !== null ? LENS_COLORS[lens.lens_id] || color.textDim : '#E5E7EB'}
            strokeWidth={strokeWidth}
            strokeDasharray={dashArray}
            strokeDashoffset={dashOffset}
            strokeLinecap="round"
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dasharray 0.6s ease' }}
          />
        );
      })}
      {/* Center text */}
      <text x={size / 2} y={size / 2 - 6} textAnchor="middle" style={{ fontFamily: font.family, fontWeight: font.weightBold, fontSize: '2rem' }} fill={color.text}>
        {retinaScore !== null ? Math.round(retinaScore) : '—'}
      </text>
      <text x={size / 2} y={size / 2 + 16} textAnchor="middle" style={{ fontFamily: font.family, fontSize: font.sizeSm }} fill={color.textMuted}>
        /100
      </text>
    </svg>
  );
}

/* ── Recommendations Section ──────────────────────── */

const QUADRANT_IDS = ['no_brainers', 'quick_wins', 'growth_moves', 'transformational'] as const;
const QUADRANT_LABEL_MAP: Record<string, string> = {
  'No Brainers': 'no_brainers',
  'Quick Wins': 'quick_wins',
  'Growth Moves': 'growth_moves',
  'Transformational': 'transformational',
};
const QUADRANT_ID_LABEL: Record<string, string> = {
  no_brainers: 'No Brainers',
  quick_wins: 'Quick Wins',
  growth_moves: 'Growth Moves',
  transformational: 'Transformational',
};

const LENS_OPTIONS = [
  'Performance & Platform',
  'SEO & AI Visibility',
  'Brand & Messaging',
  'Experience & Design',
  'Conversion & Strategy',
];

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

interface RecCardProps {
  recommendations: RecommendationQuadrant[];
  projectId: string;
  onRegenerate?: () => void;
  regenerating?: boolean;
  onSaved?: () => void;
}

function RecommendationsCard({ recommendations, projectId, onRegenerate, regenerating, onSaved }: RecCardProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    recommendations.forEach((r) => { initial[r.quadrant] = r.items.length > 0; });
    return initial;
  });
  const [editing, setEditing] = useState<string | null>(null); // quadrant label being edited
  const [editItems, setEditItems] = useState<RecommendationItem[]>([]);
  const [saving, setSaving] = useState(false);

  const toggle = (q: string) => {
    if (editing === q) return; // Don't collapse while editing
    setExpanded((prev) => ({ ...prev, [q]: !prev[q] }));
  };

  const hasAnyRecs = recommendations.some((r) => r.items.length > 0);

  const startEdit = (quadrantLabel: string, items: (string | RecommendationItem)[]) => {
    setEditing(quadrantLabel);
    setEditItems(items.map(normalizeItem));
    setExpanded((prev) => ({ ...prev, [quadrantLabel]: true }));
  };

  const cancelEdit = () => {
    setEditing(null);
    setEditItems([]);
  };

  const updateField = (idx: number, field: keyof RecommendationItem, value: string) => {
    setEditItems((prev) => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  };

  const removeItem = (idx: number) => {
    setEditItems((prev) => prev.filter((_, i) => i !== idx));
  };

  const addItem = () => {
    setEditItems((prev) => [...prev, { title: '', description: '', lens: LENS_OPTIONS[0] }]);
  };

  const handleSave = async () => {
    if (!editing) return;
    setSaving(true);
    try {
      // Build full quadrant data from current recommendations + edited quadrant
      const data: QuadrantData = { no_brainers: [], quick_wins: [], growth_moves: [], transformational: [] };
      for (const rec of recommendations) {
        const qid = QUADRANT_LABEL_MAP[rec.quadrant] as keyof QuadrantData;
        if (!qid) continue;
        if (rec.quadrant === editing) {
          data[qid] = editItems.filter((it) => it.title.trim());
        } else {
          data[qid] = rec.items.map(normalizeItem);
        }
      }
      await saveRecommendations(projectId, data);
      setEditing(null);
      setEditItems([]);
      onSaved?.();
    } catch (err) {
      console.error('Failed to save recommendations', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.card}>
      <div style={styles.cardHeaderRow}>
        <h2 style={{ ...styles.cardTitle, marginBottom: 0 }}>Recommendations</h2>
        <button
          style={styles.regenBtn}
          onClick={onRegenerate}
          disabled={regenerating || !!editing}
          title={hasAnyRecs ? 'Regenerate Recommendations' : 'Generate Recommendations'}
        >
          {regenerating ? <SpinnerSmall /> : <RefreshIcon />}
          <span>{regenerating ? 'Generating…' : hasAnyRecs ? 'Regenerate' : 'Generate'}</span>
        </button>
      </div>
      {recommendations.map((rec) => {
        const isEditing = editing === rec.quadrant;
        return (
          <div key={rec.quadrant} style={styles.recSection}>
            <div style={styles.recHeader}>
              <button style={{ ...styles.recHeaderBtn, flex: 1 }} onClick={() => toggle(rec.quadrant)}>
                <span style={styles.recQuadrantName}>{rec.quadrant}</span>
              </button>
              <span style={styles.recHeaderIcons}>
                {!isEditing ? (
                  <button
                    style={styles.iconBtnSmall}
                    onClick={(e) => { e.stopPropagation(); startEdit(rec.quadrant, rec.items); }}
                    title="Edit recommendations"
                  >
                    <PencilIcon />
                  </button>
                ) : (
                  <span style={styles.editActions}>
                    <button style={styles.saveBtnSmall} onClick={handleSave} disabled={saving}>
                      {saving ? 'Saving…' : 'Save'}
                    </button>
                    <button style={styles.cancelBtnSmall} onClick={cancelEdit}>Cancel</button>
                  </span>
                )}
                <button
                  style={styles.iconBtnSmall}
                  onClick={() => toggle(rec.quadrant)}
                >
                  <ChevronDownIcon open={!!expanded[rec.quadrant]} />
                </button>
              </span>
            </div>
            {expanded[rec.quadrant] && (
              <div style={styles.recBody}>
                {isEditing ? (
                  /* ── Edit Mode ── */
                  <div style={styles.recItemList}>
                    {editItems.map((item, i) => (
                      <div key={i} style={styles.recEditCard}>
                        <input
                          style={styles.recEditInput}
                          value={item.title}
                          onChange={(e) => updateField(i, 'title', e.target.value)}
                          placeholder="Recommendation title"
                        />
                        <textarea
                          style={styles.recEditTextarea}
                          value={item.description || ''}
                          onChange={(e) => updateField(i, 'description', e.target.value)}
                          placeholder="Description (optional)"
                          rows={2}
                        />
                        <div style={styles.recEditFooter}>
                          <select
                            style={styles.recEditSelect}
                            value={item.lens || LENS_OPTIONS[0]}
                            onChange={(e) => updateField(i, 'lens', e.target.value)}
                          >
                            {LENS_OPTIONS.map((l) => (
                              <option key={l} value={l}>{l}</option>
                            ))}
                          </select>
                          <button style={styles.recDeleteBtn} onClick={() => removeItem(i)} title="Remove">
                            <DeleteSmallIcon />
                          </button>
                        </div>
                      </div>
                    ))}
                    <button style={styles.addRecBtn} onClick={addItem}>
                      + Add Recommendation
                    </button>
                  </div>
                ) : (
                  /* ── View Mode ── */
                  rec.items.length === 0 ? (
                    <p style={styles.recEmpty}>None yet</p>
                  ) : (
                    <div style={styles.recItemList}>
                      {rec.items.map((item, i) => {
                        const obj = normalizeItem(item);
                        return (
                          <div key={i} style={styles.recItemCard}>
                            <div style={styles.recItemHeader}>
                              <strong style={styles.recItemTitle}>{obj.title}</strong>
                              {obj.lens && <span style={styles.recLensTag}>{obj.lens}</span>}
                            </div>
                            {obj.description && (
                              <p style={styles.recItemDesc}>{obj.description}</p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ── Mini Icons ───────────────────────────────────── */

function PencilIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="2">
      <path d="M17 3a2.83 2.83 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
    </svg>
  );
}

function ChevronDownIcon({ open }: { open: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="2"
      style={{ transform: open ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

function DeleteSmallIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" />
      <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
    </svg>
  );
}

function RefreshIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 4 }}>
      <path d="M23 4v6h-6M1 20v-6h6" />
      <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
    </svg>
  );
}

function SpinnerSmall() {
  return (
    <svg width="14" height="14" viewBox="0 0 20 20" style={{ animation: 'spin 1s linear infinite', marginRight: 4 }}>
      <circle cx="10" cy="10" r="8" stroke={color.border} strokeWidth="2.5" fill="none" />
      <path d="M10 2 A8 8 0 0 1 18 10" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  );
}

function ImagePlaceholderIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="1.5">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M3 16l5-5 4 4 4-4 5 5" />
      <circle cx="8.5" cy="8.5" r="1.5" />
    </svg>
  );
}

function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="2">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <line x1="12" y1="8" x2="12" y2="16" />
      <line x1="8" y1="12" x2="16" y2="12" />
    </svg>
  );
}

function CloseSmallIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="2.5">
      <line x1="6" y1="6" x2="18" y2="18" />
      <line x1="18" y1="6" x2="6" y2="18" />
    </svg>
  );
}

function SmallSpinner() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.accent} strokeWidth="2.5" style={{ animation: 'spin 1s linear infinite' }}>
      <path d="M12 2a10 10 0 0 1 10 10" />
    </svg>
  );
}

function ArrowCircleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginLeft: 4 }}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8l4 4-4 4M8 12h8" />
    </svg>
  );
}

/* ── Main Report Page ─────────────────────────────── */

export function Report() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [summary, setSummary] = useState<ProjectSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    getProjectSummary(projectId)
      .then(setSummary)
      .catch((err) => setError(err.message ?? 'Failed to load project'))
      .finally(() => setLoading(false));
  }, [projectId]);

  const sidebarUser = {
    id: user?.id ?? '',
    name: user?.name ?? 'User',
    role: user?.role ?? '',
  };

  const [regenerating, setRegenerating] = useState(false);
  const dismissToast = useCallback(() => setToastMsg(null), []);

  // Competitor management state
  const [showAddComp, setShowAddComp] = useState(false);
  const [compUrl, setCompUrl] = useState('');
  const [addingComp, setAddingComp] = useState(false);
  const [processingComps, setProcessingComps] = useState<Set<string>>(new Set());
  const [confirmRemoveIdx, setConfirmRemoveIdx] = useState<number | null>(null);

  // Refresh analysis state
  const [showRefreshConfirm, setShowRefreshConfirm] = useState(false);

  // SHARE + EXPORT — UI PLACEHOLDERS, wire in later phase
  const handleShare = () => setToastMsg('Share Project — coming soon');
  const handleExport = () => setToastMsg('Export Report — coming soon');

  const handleRegenerate = async () => {
    if (!projectId || regenerating) return;
    setRegenerating(true);
    setToastMsg('Generating recommendations…');
    try {
      await generateRecommendations(projectId);
      // Wait a moment for background task to complete, then refresh
      setTimeout(async () => {
        try {
          const updated = await getProjectSummary(projectId);
          setSummary(updated);
          setToastMsg('Recommendations updated!');
        } catch {
          setToastMsg('Check back shortly — recommendations are generating');
        }
        setRegenerating(false);
      }, 8000);
    } catch (err: unknown) {
      setToastMsg(err instanceof Error ? err.message : 'Failed to generate');
      setRegenerating(false);
    }
  };

  const handleRefreshAnalysis = async () => {
    if (!projectId) return;
    setShowRefreshConfirm(false);
    try {
      await refreshProject(projectId);
      navigate(`/projects/${projectId}/status`);
    } catch (err: unknown) {
      setToastMsg(err instanceof Error ? err.message : 'Failed to start refresh');
    }
  };

  const handleAddCompetitor = async () => {
    if (!projectId || !compUrl.trim() || addingComp) return;
    setAddingComp(true);
    try {
      const resp = await addCompetitor(projectId, compUrl.trim());
      // Add to local state immediately with processing status
      setProcessingComps((prev) => new Set(prev).add(resp.url));
      setSummary((prev) => prev ? {
        ...prev,
        competitors: [...prev.competitors, { url: resp.url, retina_score: null, status: 'processing' as const }],
      } : prev);
      setCompUrl('');
      setShowAddComp(false);
      setToastMsg('Competitor added — analyzing…');
      // Poll for completion (simple approach: refresh after delay)
      setTimeout(async () => {
        try {
          const updated = await getProjectSummary(projectId);
          setSummary(updated);
          setProcessingComps((prev) => { const n = new Set(prev); n.delete(resp.url); return n; });
        } catch { /* ignore */ }
      }, 30000);
    } catch (err: unknown) {
      setToastMsg(err instanceof Error ? err.message : 'Failed to add competitor');
    }
    setAddingComp(false);
  };

  const handleRemoveCompetitor = async (index: number) => {
    if (!projectId) return;
    try {
      await removeCompetitor(projectId, index);
      setSummary((prev) => prev ? {
        ...prev,
        competitors: prev.competitors.filter((_, i) => i !== index),
      } : prev);
      setConfirmRemoveIdx(null);
      setToastMsg('Competitor removed');
    } catch (err: unknown) {
      setToastMsg(err instanceof Error ? err.message : 'Failed to remove competitor');
    }
  };

  if (loading) {
    return (
      <div style={styles.layout}>
        <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
        <main style={styles.main}>
          <p style={styles.loadingText}>Loading project…</p>
        </main>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div style={styles.layout}>
        <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
        <main style={styles.main}>
          <div style={styles.errorBanner}>{error ?? 'Project not found'}</div>
          <button style={styles.backBtn} onClick={() => navigate('/')}>← Back to Dashboard</button>
        </main>
      </div>
    );
  }

  return (
    <div style={styles.layout}>
      <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />

      <main style={styles.main}>
        {/* ── SECTION 1: PAGE HEADER ───────────────────── */}
        <div style={styles.pageHeader}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.sm }}>
            <h1 style={styles.pageTitle}>
              <span style={styles.pageTitlePrefix}>Project</span>
              <span style={styles.pageTitleDivider}> | </span>
              {summary.name}
            </h1>
            <button
              style={styles.refreshBtn}
              onClick={() => setShowRefreshConfirm(true)}
              aria-label="Refresh analysis"
              title="Refresh Analysis"
            >
              <RefreshIcon />
            </button>
          </div>

          {/* Refresh confirmation dialog */}
          {showRefreshConfirm && (
            <div style={styles.refreshConfirmOverlay}>
              <div style={styles.refreshConfirmBox}>
                <p style={styles.refreshConfirmText}>
                  Re-run analysis for <strong>{summary.name}</strong>? This will update all scores and insights with fresh data.
                </p>
                <div style={styles.refreshConfirmActions}>
                  <button style={styles.primaryBtn} onClick={handleRefreshAnalysis}>Confirm</button>
                  <button style={styles.secondaryBtn} onClick={() => setShowRefreshConfirm(false)}>Cancel</button>
                </div>
              </div>
            </div>
          )}
          <div style={styles.headerActions}>
            <button style={styles.secondaryBtn} onClick={handleShare}>
              Share Project <ArrowCircleIcon />
            </button>
            <button style={styles.primaryBtn} onClick={handleExport}>
              Export Report <ArrowCircleIcon />
            </button>
          </div>
        </div>

        {/* ── SECTION 2: LENS NAVIGATION BAR ───────────── */}
        <div style={styles.lensBar}>
          {summary.lens_scores.map((lens) => (
            <button
              key={lens.lens_id}
              style={styles.lensTab}
              onClick={() => navigate(`/projects/${projectId}/lens/${lens.lens_id}`)}
            >
              <img src={LENS_ICONS[lens.lens_id]} alt="" style={styles.lensIcon} />
              <span style={styles.lensTabName}>{lens.lens_name}</span>
            </button>
          ))}
        </div>

        {/* ── SECTION 3: SUMMARY CONTENT ───────────────── */}
        <div style={styles.summaryGrid}>
          {/* LEFT COLUMN */}
          <div style={styles.column}>
            {/* Card 1 — Project Overview */}
            <div style={styles.card}>
              <h2 style={styles.projectName}>{summary.name}</h2>
              <a href={summary.primary_url} target="_blank" rel="noopener noreferrer" style={styles.projectUrl}>
                {summary.primary_url}
              </a>
              <div style={styles.screenshotWrap}>
                {summary.screenshot_url ? (
                  <img src={summary.screenshot_url} alt={`${summary.name} screenshot`} style={styles.screenshotImg} />
                ) : (
                  <div style={styles.screenshotPlaceholder}>
                    <ImagePlaceholderIcon />
                  </div>
                )}
              </div>
            </div>

            {/* Card 2 — Competitors */}
            <div style={styles.card}>
              <div style={styles.cardHeaderRow}>
                <h2 style={{ ...styles.cardTitle, marginBottom: 0 }}>Competitors</h2>
                <button style={styles.iconBtn} aria-label="Add competitor" onClick={() => setShowAddComp(!showAddComp)}>
                  <PlusIcon />
                </button>
              </div>

              {/* Add competitor inline form */}
              {showAddComp && (
                <div style={styles.addCompForm}>
                  <input
                    type="url"
                    placeholder="https://competitor.com"
                    value={compUrl}
                    onChange={(e) => setCompUrl(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddCompetitor()}
                    style={styles.addCompInput}
                    autoFocus
                  />
                  <div style={styles.addCompActions}>
                    <button
                      style={styles.addCompBtn}
                      onClick={handleAddCompetitor}
                      disabled={addingComp || !compUrl.trim()}
                    >
                      {addingComp ? 'Adding…' : 'Add Competitor'}
                    </button>
                    <button style={styles.addCompCancel} onClick={() => { setShowAddComp(false); setCompUrl(''); }}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {summary.competitors.length === 0 && !showAddComp ? (
                <p style={styles.emptyText}>No competitors added</p>
              ) : (
                <div>
                  {summary.competitors.map((comp, i) => (
                    <div key={comp.url} style={{
                      ...styles.competitorRow,
                      ...(i < summary.competitors.length - 1 ? { borderBottom: `1px solid ${color.border}` } : {}),
                      position: 'relative' as const,
                    }}>
                      {confirmRemoveIdx === i ? (
                        /* Remove confirmation */
                        <div style={styles.compConfirm}>
                          <span style={styles.compConfirmText}>Remove {comp.url}?</span>
                          <button style={styles.compConfirmYes} onClick={() => handleRemoveCompetitor(i)}>Confirm</button>
                          <button style={styles.compConfirmNo} onClick={() => setConfirmRemoveIdx(null)}>Cancel</button>
                        </div>
                      ) : (
                        <>
                          <span style={styles.competitorUrl}>{comp.url}</span>
                          <span style={{ display: 'flex', alignItems: 'center', gap: space.sm }}>
                            {processingComps.has(comp.url) ? (
                              <SmallSpinner />
                            ) : (
                              <span style={styles.competitorScore}>
                                {comp.retina_score !== null ? (
                                  <>
                                    <span style={styles.scoreNum}>{Math.round(comp.retina_score)}</span>/20
                                  </>
                                ) : (
                                  <span style={styles.scoreDash}>—/20</span>
                                )}
                              </span>
                            )}
                            <button
                              style={styles.compRemoveBtn}
                              onClick={() => setConfirmRemoveIdx(i)}
                              aria-label={`Remove ${comp.url}`}
                            >
                              <CloseSmallIcon />
                            </button>
                          </span>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div style={styles.column}>
            {/* Card 3 — Score Summary */}
            <div style={styles.card}>
              <h2 style={styles.cardTitle}>Score Summary</h2>
              <div style={styles.scoreLayout}>
                <div style={styles.donutWrap}>
                  <span style={styles.donutLabel}>Retina</span>
                  <ScoreDonut lensScores={summary.lens_scores} retinaScore={summary.retina_score} />
                </div>
                <div style={styles.lensScoreList}>
                  {summary.lens_scores.map((lens, i) => (
                    <div key={lens.lens_id} style={{
                      ...styles.lensScoreRow,
                      ...(i < summary.lens_scores.length - 1 ? { borderBottom: `1px solid ${color.border}` } : {}),
                    }}>
                      <span style={styles.lensScoreLabel}>{lens.lens_name}</span>
                      <span style={styles.lensScoreValue}>
                        {lens.score !== null ? (
                          <>
                            <span style={styles.scoreNum}>{lens.score % 1 === 0 ? lens.score : lens.score.toFixed(1)}</span>
                            <span style={styles.scoreMax}>/20</span>
                          </>
                        ) : (
                          <span style={styles.scoreDash}>—/20</span>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Card 4 — Recommendations */}
            <RecommendationsCard
              recommendations={summary.recommendations}
              projectId={projectId!}
              onRegenerate={handleRegenerate}
              regenerating={regenerating}
              onSaved={() => {
                getProjectSummary(projectId!).then(setSummary).catch(() => {});
                setToastMsg('Recommendations saved!');
              }}
            />
          </div>
        </div>
      </main>

      {/* Toast */}
      {toastMsg && <Toast message={toastMsg} onDone={dismissToast} />}

      {/* Spin animation for regenerate spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

/* ── Styles ───────────────────────────────────────── */

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
  pageTitlePrefix: {
    color: color.textMuted,
  },
  pageTitleDivider: {
    color: color.textDim,
    fontWeight: font.weightRegular,
  },
  refreshBtn: {
    background: 'none',
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    cursor: 'pointer',
    padding: space.xxs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 32,
    height: 32,
    color: color.textMuted,
    transition: 'background 0.15s',
  } as React.CSSProperties,
  refreshConfirmOverlay: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.35)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  refreshConfirmBox: {
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    padding: space.xl,
    maxWidth: 420,
    width: '90%',
    boxShadow: '0 4px 24px rgba(0,0,0,0.15)',
  } as React.CSSProperties,
  refreshConfirmText: {
    fontFamily: font.family,
    fontSize: font.sizeMd,
    color: color.text,
    margin: 0,
    marginBottom: space.md,
    lineHeight: 1.5,
  },
  refreshConfirmActions: {
    display: 'flex',
    gap: space.sm,
    justifyContent: 'flex-end',
  },
  headerActions: {
    display: 'flex',
    gap: space.sm,
    flexShrink: 0,
  },
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
    padding: `${space.sm} 0`,
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
    background: 'none',
    cursor: 'pointer',
    fontFamily: font.family,
    fontSize: '0.875rem',  // 14px (was 12px)
    fontWeight: font.weightMedium,
    color: color.text,
    textAlign: 'center',
    transition: 'opacity 0.15s',
    opacity: 0.5,
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

  /* Summary grid */
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

  /* Cards */
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
  cardHeaderRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: space.md,
  },

  /* Project overview card */
  projectName: {
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
  },
  screenshotImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  screenshotPlaceholder: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  /* Competitors */
  emptyText: {
    margin: 0,
    marginTop: space.sm,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textDim,
  },
  iconBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: space.xxs,
    display: 'flex',
    alignItems: 'center',
  },
  competitorRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `${space.sm} 0`,
  },
  competitorUrl: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },
  competitorScore: {
    fontFamily: font.family,
    fontSize: font.sizeMd,
    color: color.textMuted,
  },
  compRemoveBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: 2,
    display: 'flex',
    alignItems: 'center',
    opacity: 0.4,
    transition: 'opacity 0.15s',
  } as React.CSSProperties,
  addCompForm: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: space.xs,
    padding: `${space.sm} 0`,
    borderBottom: `1px solid ${color.border}`,
  },
  addCompInput: {
    width: '100%',
    padding: `${space.xs} ${space.sm}`,
    borderRadius: radius.md,
    border: `1px solid ${color.border}`,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    outline: 'none',
    boxSizing: 'border-box' as const,
  },
  addCompActions: {
    display: 'flex',
    gap: space.xs,
    alignItems: 'center',
  },
  addCompBtn: {
    padding: `${space.xxs} ${space.sm}`,
    borderRadius: 999,
    border: 'none',
    background: color.accent,
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
  } as React.CSSProperties,
  addCompCancel: {
    padding: `${space.xxs} ${space.sm}`,
    borderRadius: 999,
    border: `1px solid ${color.border}`,
    background: 'none',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    cursor: 'pointer',
  } as React.CSSProperties,
  compConfirm: {
    display: 'flex',
    alignItems: 'center',
    gap: space.xs,
    width: '100%',
    flexWrap: 'wrap' as const,
  },
  compConfirmText: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
    flex: 1,
    minWidth: 0,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  compConfirmYes: {
    padding: `2px ${space.sm}`,
    borderRadius: 999,
    border: 'none',
    background: '#E74C3C',
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    cursor: 'pointer',
  } as React.CSSProperties,
  compConfirmNo: {
    padding: `2px ${space.sm}`,
    borderRadius: 999,
    border: `1px solid ${color.border}`,
    background: 'none',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    cursor: 'pointer',
  } as React.CSSProperties,

  /* Score summary */
  scoreLayout: {
    display: 'flex',
    gap: space.lg,
    alignItems: 'flex-start',
  },
  donutWrap: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: space.xs,
    flexShrink: 0,
  },
  donutLabel: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },
  lensScoreList: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
  lensScoreRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `${space.sm} 0`,
  },
  lensScoreLabel: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
    flex: 1,
  },
  lensScoreValue: {
    fontFamily: font.family,
    fontSize: font.sizeMd,
    color: color.textMuted,
    textAlign: 'right',
    whiteSpace: 'nowrap',
  },
  scoreNum: {
    fontWeight: font.weightBold,
    fontSize: font.sizeLg,
    color: color.accent,
  },
  scoreMax: {
    fontWeight: font.weightRegular,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },
  scoreDash: {
    color: color.textDim,
    fontWeight: font.weightMedium,
  },

  /* Recommendations */
  recSection: {
    borderBottom: `1px solid ${color.border}`,
  },
  recHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    padding: `${space.sm} 0`,
  },
  recHeaderBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    fontFamily: font.family,
    textAlign: 'left' as const,
    padding: 0,
  },
  recQuadrantName: {
    fontWeight: font.weightSemibold,
    fontSize: font.sizeBase,
    color: color.text,
  },
  recHeaderIcons: {
    display: 'flex',
    alignItems: 'center',
    gap: space.sm,
  },
  recBody: {
    paddingBottom: space.md,
  },
  recEmpty: {
    margin: 0,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textDim,
    fontStyle: 'italic',
  },
  recList: {
    margin: 0,
    paddingLeft: space.lg,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.text,
    lineHeight: 1.6,
  },
  recItem: {
    marginBottom: space.xs,
  },
  regenBtn: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: `4px ${space.sm}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.pill,
    backgroundColor: 'transparent',
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    transition: 'background-color 0.15s, color 0.15s',
  },
  recItemList: {
    display: 'flex',
    flexDirection: 'column',
    gap: space.sm,
  },
  recItemCard: {
    padding: space.sm,
    borderRadius: radius.md,
    backgroundColor: color.bgPage,
    border: `1px solid ${color.border}`,
  },
  recItemHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space.sm,
    marginBottom: space.xxs,
  },
  recItemTitle: {
    margin: 0,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    color: color.text,
  },
  recLensTag: {
    padding: '2px 8px',
    borderRadius: radius.pill,
    backgroundColor: color.accentLight,
    fontFamily: font.family,
    fontSize: '0.625rem',
    fontWeight: font.weightMedium,
    color: color.accent,
    whiteSpace: 'nowrap',
    flexShrink: 0,
  },
  recItemDesc: {
    margin: 0,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    lineHeight: 1.5,
  },
  iconBtnSmall: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '2px',
    display: 'flex',
    alignItems: 'center',
  },
  editActions: {
    display: 'flex',
    gap: space.xxs,
    alignItems: 'center',
  },
  saveBtnSmall: {
    padding: '3px 10px',
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightSemibold,
    cursor: 'pointer',
  },
  cancelBtnSmall: {
    padding: '3px 10px',
    border: `1px solid ${color.border}`,
    borderRadius: radius.pill,
    backgroundColor: 'transparent',
    color: color.textMuted,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    cursor: 'pointer',
  },
  recEditCard: {
    padding: space.sm,
    borderRadius: radius.md,
    backgroundColor: color.bgPage,
    border: `1px solid ${color.border}`,
    display: 'flex',
    flexDirection: 'column',
    gap: space.xs,
  },
  recEditInput: {
    padding: '6px 8px',
    border: `1px solid ${color.border}`,
    borderRadius: radius.sm,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    color: color.text,
    outline: 'none',
  },
  recEditTextarea: {
    padding: '6px 8px',
    border: `1px solid ${color.border}`,
    borderRadius: radius.sm,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.text,
    resize: 'vertical' as const,
    outline: 'none',
    minHeight: 40,
  },
  recEditFooter: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space.sm,
  },
  recEditSelect: {
    padding: '4px 8px',
    border: `1px solid ${color.border}`,
    borderRadius: radius.sm,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textMuted,
    backgroundColor: '#fff',
    flex: 1,
  },
  recDeleteBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: color.error,
    padding: '2px',
    display: 'flex',
    alignItems: 'center',
  },
  addRecBtn: {
    padding: `${space.xs} ${space.sm}`,
    border: `1px dashed ${color.border}`,
    borderRadius: radius.md,
    backgroundColor: 'transparent',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
    cursor: 'pointer',
    textAlign: 'center',
    width: '100%',
  },

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
