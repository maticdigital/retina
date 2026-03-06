import { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getProjectSummary, getProject, generateRecommendations, saveRecommendations, addCompetitor, removeCompetitor, refreshProject, uploadScreenshot, deleteScreenshot, startPdfExport, getExportStatus } from '../api';
import type { ProjectSummary, LensScore, RecommendationQuadrant, RecommendationItem, QuadrantData, ExportStatusResponse } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import { Sidebar } from '../components/Sidebar';
import { MobileDrawer } from '../components/MobileDrawer';
import { useIsMobile } from '../hooks/useIsMobile';
import { ShareModal } from '../components/ShareModal';
import { NAV_ITEMS } from './Dashboard';

import { LensIcon } from '../components/LensIcons';

/* ── Constants ────────────────────────────────────── */

const LENS_COLORS: Record<string, string> = {
  performance_technical_health: '#076EFF',
  seo_ai_visibility: '#00C864',
  brand_messaging: '#9B59B6',
  experience_design: '#E74C3C',
  conversion_strategy: '#FF8C00',
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

const QUADRANT_LABEL_MAP: Record<string, string> = {
  'No Brainers': 'no_brainers',
  'Quick Wins': 'quick_wins',
  'Growth Moves': 'growth_moves',
  'Transformational': 'transformational',
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

function UploadIcon({ size = 28, col = color.textDim }: { size?: number; col?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={col} strokeWidth="1.5">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

function TrashIcon({ size = 16, col = '#fff' }: { size?: number; col?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={col} strokeWidth="2">
      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" />
      <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
    </svg>
  );
}

function ReplaceIcon({ size = 16, col = '#fff' }: { size?: number; col?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={col} strokeWidth="2">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  );
}

/* ── Main Report Page ─────────────────────────────── */

export function Report() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const isMobile = useIsMobile();
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

  // Screenshot upload state
  const screenshotInputRef = useRef<HTMLInputElement>(null);
  const [ssHover, setSsHover] = useState(false);
  const [ssUploading, setSsUploading] = useState(false);
  const [ssConfirmDelete, setSsConfirmDelete] = useState(false);

  const handleScreenshotUpload = async (file: File) => {
    if (!projectId || ssUploading) return;
    setSsUploading(true);
    try {
      const resp = await uploadScreenshot(projectId, file);
      setSummary((prev) => prev ? { ...prev, screenshot_url: resp.screenshot_url } : prev);
      setToastMsg('Screenshot uploaded');
    } catch (err: unknown) {
      setToastMsg(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setSsUploading(false);
      if (screenshotInputRef.current) screenshotInputRef.current.value = '';
    }
  };

  const handleScreenshotDelete = async () => {
    if (!projectId) return;
    setSsConfirmDelete(false);
    try {
      await deleteScreenshot(projectId);
      setSummary((prev) => prev ? { ...prev, screenshot_url: null } : prev);
      setToastMsg('Screenshot removed');
    } catch (err: unknown) {
      setToastMsg(err instanceof Error ? err.message : 'Failed to remove screenshot');
    }
  };

  const onScreenshotFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleScreenshotUpload(file);
  };

  // SHARE — modal state
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [isShared, setIsShared] = useState(false);
  const [shareToken, setShareToken] = useState<string | null>(null);

  const handleShare = async () => {
    // Fetch current share status before opening modal
    try {
      const proj = await getProject(projectId!);
      setIsShared(proj.is_shared ?? false);
      setShareToken(proj.share_token ?? null);
    } catch {
      // Fall back to current state if fetch fails
    }
    setShareModalOpen(true);
  };

  const handleShareUpdate = (shared: boolean, token: string | null) => {
    setIsShared(shared);
    setShareToken(token);
  };

  // PDF EXPORT — modal state
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

  const handleExport = async () => {
    if (!projectId) return;
    setExportModalOpen(true);
    setExportStatus('pending');
    setExportUrl(null);
    setExportError(null);

    try {
      await startPdfExport(projectId);

      // Poll for status
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
          // Keep polling on transient errors
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

  // Clean up poll on unmount
  useEffect(() => () => stopExportPoll(), [stopExportPoll]);

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

  const navContent = isMobile
    ? <MobileDrawer navItems={NAV_ITEMS} user={sidebarUser} />
    : <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />;

  if (loading) {
    return (
      <div style={styles.layout}>
        {navContent}
        <main style={styles.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
          <p style={styles.loadingText}>Loading project…</p>
        </main>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div style={styles.layout}>
        {navContent}
        <main style={styles.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
          <div style={styles.errorBanner}>{error ?? 'Project not found'}</div>
          <button style={styles.backBtn} onClick={() => navigate('/')}>← Back to Dashboard</button>
        </main>
      </div>
    );
  }

  return (
    <div style={styles.layout}>
      {navContent}

      <main style={styles.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
        {/* ── SECTION 1: PAGE HEADER ───────────────────── */}
        <div style={styles.pageHeader} className={isMobile ? 'mobile-stack' : ''}>
          <div style={{ display: 'flex', alignItems: 'center', gap: space.sm }}>
            <h1 style={styles.pageTitle}>
              <span style={styles.pageTitlePrefix}>Project</span>
              <span style={styles.pageTitleDivider}> | </span>
              <span style={styles.pageTitleName}>{summary.name}</span>
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
          <div style={styles.headerActions} className={isMobile ? 'mobile-full' : ''}>
            <button style={{...styles.secondaryBtn, ...(isMobile ? { flex: 1 } : {})}} onClick={handleShare}>
              Share Project <ArrowCircleIcon />
            </button>
            <button style={{...styles.primaryBtn, ...(isMobile ? { flex: 1 } : {})}} onClick={handleExport}>
              Export Report <ArrowCircleIcon />
            </button>
          </div>
        </div>

        {/* ── SECTION 2: LENS NAVIGATION BAR ───────────── */}
        <div style={styles.lensBar} className={isMobile ? 'mobile-scroll-x' : ''}>
          {summary.lens_scores.map((lens) => (
            <button
              key={lens.lens_id}
              style={{...styles.lensTab, ...(isMobile ? { minWidth: 100, flex: 'none' } : {})}}
              onClick={() => navigate(`/projects/${projectId}/lens/${lens.lens_id}`)}
            >
              <LensIcon lensId={lens.lens_id} color={LENS_COLORS[lens.lens_id] || color.text} />
              <span style={styles.lensTabName}>{lens.lens_name}</span>
            </button>
          ))}
        </div>

        {/* ── SECTION 3: SUMMARY CONTENT ───────────────── */}
        <div style={styles.summaryGrid} className={isMobile ? 'mobile-grid-1' : ''}>
          {/* LEFT COLUMN */}
          <div style={styles.column}>
            {/* Card 1 — Project Overview */}
            <div style={styles.card}>
              <h2 style={styles.projectName}>{summary.name}</h2>
              <a href={summary.primary_url} target="_blank" rel="noopener noreferrer" style={styles.projectUrl}>
                {summary.primary_url}
              </a>
              {/* Hidden file input for screenshot upload */}
              <input
                ref={screenshotInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                style={{ display: 'none' }}
                onChange={onScreenshotFileChange}
              />

              <div
                style={styles.screenshotWrap}
                onMouseEnter={() => setSsHover(true)}
                onMouseLeave={() => { setSsHover(false); setSsConfirmDelete(false); }}
              >
                {summary.screenshot_url ? (
                  /* ── State 2: Screenshot present ── */
                  <>
                    <img src={summary.screenshot_url} alt={`${summary.name} screenshot`} style={styles.screenshotImg} />
                    {ssHover && !ssUploading && (
                      <div style={styles.ssOverlay}>
                        {ssConfirmDelete ? (
                          <div style={styles.ssConfirmBox}>
                            <span style={styles.ssConfirmText}>Remove this screenshot?</span>
                            <div style={styles.ssConfirmActions}>
                              <button style={styles.ssConfirmYes} onClick={handleScreenshotDelete}>Confirm</button>
                              <button style={styles.ssConfirmNo} onClick={() => setSsConfirmDelete(false)}>Cancel</button>
                            </div>
                          </div>
                        ) : (
                          <div style={styles.ssOverlayActions}>
                            <button
                              style={styles.ssOverlayBtn}
                              onClick={() => screenshotInputRef.current?.click()}
                              title="Replace screenshot"
                            >
                              <ReplaceIcon size={18} />
                              <span style={styles.ssOverlayLabel}>Replace</span>
                            </button>
                            <button
                              style={styles.ssOverlayBtn}
                              onClick={() => setSsConfirmDelete(true)}
                              title="Delete screenshot"
                            >
                              <TrashIcon size={18} />
                              <span style={styles.ssOverlayLabel}>Delete</span>
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                    {ssUploading && (
                      <div style={styles.ssOverlay}>
                        <SmallSpinner />
                        <span style={{ color: '#fff', fontFamily: font.family, fontSize: font.sizeSm, marginTop: 6 }}>Uploading…</span>
                      </div>
                    )}
                  </>
                ) : (
                  /* ── State 1: No screenshot — upload zone ── */
                  <div
                    style={styles.ssUploadZone}
                    onClick={() => !ssUploading && screenshotInputRef.current?.click()}
                  >
                    {ssUploading ? (
                      <>
                        <SmallSpinner />
                        <span style={styles.ssUploadLabel}>Uploading…</span>
                      </>
                    ) : (
                      <>
                        <UploadIcon size={28} col={color.textDim} />
                        <span style={styles.ssUploadLabel}>Add Screenshot</span>
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Card 2 — Technology Stack */}
            {summary.tech_stack && Object.keys(summary.tech_stack).length > 0 && (
              <div style={styles.card}>
                <h2 style={styles.cardTitle}>Technology Stack</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: space.sm }}>
                  {(['cms', 'analytics', 'crm'] as const).map((cat) => {
                    const items = summary.tech_stack?.[cat];
                    if (!items || items.length === 0) return null;
                    const labels: Record<string, string> = {
                      cms: 'CMS',
                      analytics: 'Analytics',
                      crm: 'CRM',
                    };
                    return (
                      <div key={cat}>
                        <p style={{ margin: 0, fontSize: '0.75rem', fontWeight: 600, color: color.textDim, textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '0.25rem' }}>
                          {labels[cat]}
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {items.map((tech) => (
                            <span key={tech} style={{
                              display: 'inline-block',
                              padding: '3px 10px',
                              borderRadius: '999px',
                              fontSize: '0.78rem',
                              fontWeight: 500,
                              background: color.bgPage,
                              color: color.text,
                              border: `1px solid ${color.border}`,
                            }}>
                              {tech}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Card 3 — Competitors */}
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
            {/* Card 3 — Retina Score */}
            <div style={styles.card}>
              <h2 style={styles.cardTitle}>Retina Score</h2>
              <div style={styles.scoreLayout} className={isMobile ? 'mobile-stack' : ''}>
                <div style={{...styles.donutWrap, ...(isMobile ? { alignSelf: 'center' } : {})}}>
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
                            <span style={{ ...styles.scoreNum, color: LENS_COLORS[lens.lens_id] || color.accent }}>{lens.score % 1 === 0 ? lens.score : lens.score.toFixed(1)}</span>
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

      {/* Share Modal */}
      {shareModalOpen && (
        <ShareModal
          projectId={projectId!}
          isShared={isShared}
          shareToken={shareToken}
          onClose={() => setShareModalOpen(false)}
          onUpdate={handleShareUpdate}
        />
      )}

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
              /* ── Complete ── */
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
              /* ── Error ── */
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
              /* ── Generating ── */
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
  pageTitleName: {
    fontWeight: font.weightRegular,
  } as React.CSSProperties,
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
    position: 'relative' as const,
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
  ssUploadZone: {
    width: '100%',
    height: '100%',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    gap: space.xs,
    transition: 'background-color 0.15s',
  },
  ssUploadLabel: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textDim,
    fontWeight: font.weightMedium,
  },
  ssOverlay: {
    position: 'absolute' as const,
    inset: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.sm,
    borderRadius: radius.lg,
  },
  ssOverlayActions: {
    display: 'flex',
    gap: space.lg,
    alignItems: 'center',
  },
  ssOverlayBtn: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    gap: 4,
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: space.sm,
    borderRadius: radius.md,
    transition: 'background-color 0.15s',
  },
  ssOverlayLabel: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: '#fff',
    fontWeight: font.weightMedium,
  },
  ssConfirmBox: {
    display: 'flex',
    flexDirection: 'column' as const,
    alignItems: 'center',
    gap: space.sm,
  },
  ssConfirmText: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: '#fff',
    fontWeight: font.weightMedium,
  },
  ssConfirmActions: {
    display: 'flex',
    gap: space.sm,
  },
  ssConfirmYes: {
    padding: `${space.xxs} ${space.md}`,
    borderRadius: radius.pill,
    border: 'none',
    backgroundColor: '#E74C3C',
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
  } as React.CSSProperties,
  ssConfirmNo: {
    padding: `${space.xxs} ${space.md}`,
    borderRadius: radius.pill,
    border: '1px solid rgba(255,255,255,0.5)',
    backgroundColor: 'transparent',
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    cursor: 'pointer',
  } as React.CSSProperties,

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
