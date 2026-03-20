import { useEffect, useState, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchAllStandards, fetchStandardsSummary, createStandard, updateStandard } from '../api';
import type { Standard, StandardsSummary } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import { Sidebar } from '../components/Sidebar';
import { MobileDrawer } from '../components/MobileDrawer';
import { useIsMobile } from '../hooks/useIsMobile';
import { NAV_ITEMS } from './Dashboard';

const LENS_OPTIONS = ['performance', 'seo', 'brand', 'experience', 'conversion'] as const;

const LENS_COLORS: Record<string, string> = {
  performance: color.lensPerformance,
  seo: color.lensSeo,
  brand: color.lensBrand,
  experience: color.lensExperience,
  conversion: color.lensConversion,
};

/* ── Edit / Create Modal ─────────────────────────── */

function StandardModal({
  open,
  existing,
  onClose,
  onSave,
}: {
  open: boolean;
  existing: Standard | null;
  onClose: () => void;
  onSave: (data: Omit<Standard, 'id' | 'is_active' | 'created_at' | 'updated_at'>) => Promise<void>;
}) {
  const [lens, setLens] = useState('performance');
  const [category, setCategory] = useState('');
  const [principle, setPrinciple] = useState('');
  const [source, setSource] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [evalCriteria, setEvalCriteria] = useState('');
  const [scoringGuidance, setScoringGuidance] = useState('');
  const [appliesToCohort, setAppliesToCohort] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (existing) {
      setLens(existing.lens);
      setCategory(existing.category);
      setPrinciple(existing.principle);
      setSource(existing.source);
      setSourceUrl(existing.source_url || '');
      setEvalCriteria(existing.evaluation_criteria);
      setScoringGuidance(existing.scoring_guidance);
      setAppliesToCohort(existing.applies_to_cohort);
    } else {
      setLens('performance');
      setCategory('');
      setPrinciple('');
      setSource('');
      setSourceUrl('');
      setEvalCriteria('');
      setScoringGuidance('');
      setAppliesToCohort(true);
    }
    setError(null);
  }, [existing, open]);

  if (!open) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!category.trim() || !principle.trim() || !source.trim() || !evalCriteria.trim() || !scoringGuidance.trim()) {
      setError('All required fields must be filled.');
      return;
    }
    setSubmitting(true);
    try {
      await onSave({
        lens,
        category: category.trim(),
        principle: principle.trim(),
        source: source.trim(),
        source_url: sourceUrl.trim() || null,
        evaluation_criteria: evalCriteria.trim(),
        scoring_guidance: scoringGuidance.trim(),
        applies_to_cohort: appliesToCohort,
      });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={modalStyles.overlay} onClick={onClose}>
      <div style={{ ...modalStyles.modal, maxWidth: 600, maxHeight: '90vh', overflow: 'auto' }} onClick={(e) => e.stopPropagation()}>
        <div style={modalStyles.header}>
          <h2 style={modalStyles.title}>{existing ? 'Edit Standard' : 'Add Standard'}</h2>
          <button style={modalStyles.closeBtn} onClick={onClose}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && <div style={modalStyles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={modalStyles.form}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: space.md }}>
            <label style={modalStyles.label}>
              Lens *
              <select value={lens} onChange={(e) => setLens(e.target.value)} style={modalStyles.input}>
                {LENS_OPTIONS.map((l) => <option key={l} value={l}>{l}</option>)}
              </select>
            </label>
            <label style={modalStyles.label}>
              Category *
              <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. core_web_vitals" style={modalStyles.input} />
            </label>
          </div>
          <label style={modalStyles.label}>
            Principle *
            <textarea value={principle} onChange={(e) => setPrinciple(e.target.value)} rows={3} style={{ ...modalStyles.input, resize: 'vertical' }} placeholder="The research-backed principle or standard..." />
          </label>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: space.md }}>
            <label style={modalStyles.label}>
              Source *
              <input type="text" value={source} onChange={(e) => setSource(e.target.value)} placeholder="e.g. Nielsen Norman Group" style={modalStyles.input} />
            </label>
            <label style={modalStyles.label}>
              Source URL
              <input type="url" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://..." style={modalStyles.input} />
            </label>
          </div>
          <label style={modalStyles.label}>
            Evaluation Criteria *
            <textarea value={evalCriteria} onChange={(e) => setEvalCriteria(e.target.value)} rows={3} style={{ ...modalStyles.input, resize: 'vertical' }} placeholder="How to evaluate this standard..." />
          </label>
          <label style={modalStyles.label}>
            Scoring Guidance *
            <textarea value={scoringGuidance} onChange={(e) => setScoringGuidance(e.target.value)} rows={2} style={{ ...modalStyles.input, resize: 'vertical' }} placeholder="How to score: good, needs improvement, poor..." />
          </label>
          <label style={{ ...modalStyles.label, flexDirection: 'row', alignItems: 'center', gap: space.sm }}>
            <input type="checkbox" checked={appliesToCohort} onChange={(e) => setAppliesToCohort(e.target.checked)} />
            Applies to cohort reports
          </label>

          <div style={modalStyles.actions}>
            <button type="button" onClick={onClose} style={modalStyles.cancelBtn}>Cancel</button>
            <button type="submit" disabled={submitting} style={modalStyles.submitBtn}>
              {submitting ? 'Saving...' : existing ? 'Save Changes' : 'Add Standard'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Standards Page ───────────────────────────────── */

export function Standards() {
  const { user } = useAuth();
  const isMobile = useIsMobile();
  const [standards, setStandards] = useState<Standard[]>([]);
  const [summary, setSummary] = useState<StandardsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterLens, setFilterLens] = useState<string>('all');
  const [filterActive, setFilterActive] = useState<string>('active');
  const [showModal, setShowModal] = useState(false);
  const [editingStandard, setEditingStandard] = useState<Standard | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const isAdmin = user?.role === 'owner' || user?.role === 'admin';

  useEffect(() => {
    if (!isAdmin) return;
    Promise.all([fetchAllStandards(), fetchStandardsSummary()])
      .then(([s, sum]) => { setStandards(s); setSummary(sum); })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [isAdmin]);

  const filtered = useMemo(() => {
    return standards.filter((s) => {
      if (filterLens !== 'all' && s.lens !== filterLens) return false;
      if (filterActive === 'active' && !s.is_active) return false;
      if (filterActive === 'inactive' && s.is_active) return false;
      return true;
    });
  }, [standards, filterLens, filterActive]);

  const handleCreate = async (data: Omit<Standard, 'id' | 'is_active' | 'created_at' | 'updated_at'>) => {
    const created = await createStandard(data);
    setStandards((prev) => [...prev, created]);
    // Refresh summary
    fetchStandardsSummary().then(setSummary).catch(() => {});
  };

  const handleUpdate = async (data: Omit<Standard, 'id' | 'is_active' | 'created_at' | 'updated_at'>) => {
    if (!editingStandard) return;
    const updated = await updateStandard(editingStandard.id, data);
    setStandards((prev) => prev.map((s) => s.id === updated.id ? updated : s));
    setEditingStandard(null);
  };

  const handleToggleActive = async (std: Standard) => {
    setTogglingId(std.id);
    try {
      const updated = await updateStandard(std.id, { is_active: !std.is_active });
      setStandards((prev) => prev.map((s) => s.id === updated.id ? updated : s));
      fetchStandardsSummary().then(setSummary).catch(() => {});
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to toggle');
    } finally {
      setTogglingId(null);
    }
  };

  const sidebarUser = {
    id: user?.id ?? '',
    name: user?.name ?? 'User',
    role: user?.role ?? '',
  };

  const navContent = isMobile
    ? <MobileDrawer navItems={NAV_ITEMS} user={sidebarUser} />
    : <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />;

  if (!isAdmin) {
    return (
      <div style={styles.layout}>
        {navContent}
        <main style={styles.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
          <h1 style={styles.heading}>Standards Library</h1>
          <p style={styles.accessDenied}>You do not have permission to access this page.</p>
        </main>
      </div>
    );
  }

  return (
    <div style={styles.layout}>
      {navContent}

      <main style={styles.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
        <div style={styles.headerRow}>
          <h1 style={styles.heading}>Standards Library</h1>
          <button style={styles.addBtn} onClick={() => { setEditingStandard(null); setShowModal(true); }}>
            + Add Standard
          </button>
        </div>

        {/* Summary chips */}
        {summary && (
          <div style={{ display: 'flex', gap: space.sm, flexWrap: 'wrap', marginBottom: space.lg }}>
            {LENS_OPTIONS.map((lens) => {
              const c = summary.counts[lens];
              return (
                <div
                  key={lens}
                  style={{
                    padding: `${space.xxs} ${space.md}`,
                    borderRadius: radius.pill,
                    backgroundColor: filterLens === lens ? LENS_COLORS[lens] : color.bgCard,
                    color: filterLens === lens ? '#fff' : color.text,
                    fontFamily: font.family,
                    fontSize: font.sizeXs,
                    fontWeight: font.weightMedium,
                    cursor: 'pointer',
                    border: `1px solid ${filterLens === lens ? LENS_COLORS[lens] : color.border}`,
                    transition: 'all 0.15s',
                  }}
                  onClick={() => setFilterLens(filterLens === lens ? 'all' : lens)}
                >
                  {lens} ({c ? c.active : 0})
                </div>
              );
            })}
            <div
              style={{
                padding: `${space.xxs} ${space.md}`,
                borderRadius: radius.pill,
                backgroundColor: filterLens === 'all' ? color.accent : color.bgCard,
                color: filterLens === 'all' ? '#fff' : color.textMuted,
                fontFamily: font.family,
                fontSize: font.sizeXs,
                fontWeight: font.weightMedium,
                cursor: 'pointer',
                border: `1px solid ${filterLens === 'all' ? color.accent : color.border}`,
              }}
              onClick={() => setFilterLens('all')}
            >
              All ({summary.total})
            </div>
            <select
              value={filterActive}
              onChange={(e) => setFilterActive(e.target.value)}
              style={{
                marginLeft: 'auto',
                padding: `${space.xxs} ${space.sm}`,
                border: `1px solid ${color.border}`,
                borderRadius: radius.md,
                fontFamily: font.family,
                fontSize: font.sizeXs,
                color: color.text,
                backgroundColor: color.bgCard,
              }}
            >
              <option value="all">All statuses</option>
              <option value="active">Active only</option>
              <option value="inactive">Inactive only</option>
            </select>
          </div>
        )}

        {error && <div style={styles.errorBanner}>{error}</div>}

        {loading ? (
          <p style={styles.loadingText}>Loading standards...</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: space.md }}>
            {filtered.length === 0 && (
              <p style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.textMuted, textAlign: 'center', padding: space.xxl }}>
                No standards found for the selected filters.
              </p>
            )}
            {filtered.map((std) => (
              <div
                key={std.id}
                style={{
                  backgroundColor: color.bgCard,
                  borderRadius: radius.lg,
                  padding: space.lg,
                  boxShadow: color.shadow,
                  borderLeft: `4px solid ${LENS_COLORS[std.lens] || color.border}`,
                  opacity: std.is_active ? 1 : 0.55,
                  transition: 'opacity 0.15s',
                }}
              >
                {/* Header row */}
                <div style={{ display: 'flex', alignItems: 'center', gap: space.sm, marginBottom: space.sm }}>
                  <span style={{
                    padding: `2px ${space.xs}`,
                    borderRadius: radius.pill,
                    backgroundColor: LENS_COLORS[std.lens] + '18',
                    color: LENS_COLORS[std.lens],
                    fontFamily: font.family,
                    fontSize: font.sizeXs,
                    fontWeight: font.weightSemibold,
                    textTransform: 'uppercase' as const,
                  }}>
                    {std.lens}
                  </span>
                  <span style={{
                    fontFamily: font.family,
                    fontSize: font.sizeXs,
                    color: color.textMuted,
                  }}>
                    {std.category.replace(/_/g, ' ')}
                  </span>
                  <span style={{
                    marginLeft: 'auto',
                    fontFamily: font.family,
                    fontSize: font.sizeXs,
                    color: color.textDim,
                    fontStyle: 'italic',
                  }}>
                    {std.source}
                  </span>
                  {!std.is_active && (
                    <span style={{
                      padding: `2px ${space.xs}`,
                      borderRadius: radius.pill,
                      backgroundColor: '#FEE2E2',
                      color: color.error,
                      fontFamily: font.family,
                      fontSize: font.sizeXs,
                      fontWeight: font.weightMedium,
                    }}>
                      Inactive
                    </span>
                  )}
                </div>

                {/* Principle */}
                <p style={{ fontFamily: font.family, fontSize: font.sizeSm, color: color.text, lineHeight: 1.6, margin: `0 0 ${space.sm}` }}>
                  {std.principle}
                </p>

                {/* Evaluation & Scoring (collapsed) */}
                <details style={{ marginBottom: space.sm }}>
                  <summary style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.textMuted, cursor: 'pointer', userSelect: 'none' }}>
                    Evaluation criteria & scoring guidance
                  </summary>
                  <div style={{ marginTop: space.xs, padding: space.sm, backgroundColor: color.bgPage, borderRadius: radius.md }}>
                    <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.text, lineHeight: 1.5, margin: `0 0 ${space.xs}` }}>
                      <strong>Evaluate:</strong> {std.evaluation_criteria}
                    </p>
                    <p style={{ fontFamily: font.family, fontSize: font.sizeXs, color: color.text, lineHeight: 1.5, margin: 0 }}>
                      <strong>Scoring:</strong> {std.scoring_guidance}
                    </p>
                  </div>
                </details>

                {/* Actions */}
                <div style={{ display: 'flex', gap: space.xs }}>
                  <button
                    style={styles.editBtn}
                    onClick={() => { setEditingStandard(std); setShowModal(true); }}
                  >
                    Edit
                  </button>
                  <button
                    style={{
                      ...styles.editBtn,
                      color: std.is_active ? color.error : color.success,
                      borderColor: std.is_active ? '#FEE2E2' : '#DCFCE7',
                    }}
                    onClick={() => handleToggleActive(std)}
                    disabled={togglingId === std.id}
                  >
                    {togglingId === std.id ? '...' : std.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      <StandardModal
        open={showModal}
        existing={editingStandard}
        onClose={() => { setShowModal(false); setEditingStandard(null); }}
        onSave={editingStandard ? handleUpdate : handleCreate}
      />
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
    maxWidth: 1000,
  },
  headerRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: space.lg,
  },
  heading: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.size2xl,
    color: color.text,
  },
  addBtn: {
    padding: `${space.sm} ${space.lg}`,
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    cursor: 'pointer',
  },
  errorBanner: {
    padding: space.sm,
    marginBottom: space.md,
    borderRadius: radius.md,
    backgroundColor: '#FEE2E2',
    color: color.error,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    textAlign: 'center',
  },
  loadingText: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },
  accessDenied: {
    fontFamily: font.family,
    fontSize: font.sizeMd,
    color: color.textMuted,
    textAlign: 'center',
    padding: space.xxl,
  },
  editBtn: {
    padding: `${space.xxs} ${space.sm}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    backgroundColor: 'transparent',
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightMedium,
    color: color.text,
    cursor: 'pointer',
  },
};

const modalStyles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modal: {
    width: '100%',
    maxWidth: 460,
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    padding: space.xl,
    boxShadow: '0 8px 32px rgba(0,0,0,0.16)',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: space.lg,
  },
  title: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeLg,
    color: color.text,
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: color.textMuted,
    padding: space.xxs,
    borderRadius: radius.sm,
    display: 'flex',
  },
  error: {
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
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: space.sm,
    marginTop: space.sm,
  },
  cancelBtn: {
    padding: `${space.sm} ${space.lg}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.pill,
    backgroundColor: 'transparent',
    fontFamily: font.family,
    fontSize: font.sizeBase,
    fontWeight: font.weightMedium,
    color: color.textMuted,
    cursor: 'pointer',
  },
  submitBtn: {
    padding: `${space.sm} ${space.lg}`,
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
