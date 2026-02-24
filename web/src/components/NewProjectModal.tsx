import { useState } from 'react';
import { color, font, space, radius } from '../tokens';

interface NewProjectModalProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { name: string; primary_url: string; competitor_urls: string[] }) => Promise<void>;
}

export function NewProjectModal({ open, onClose, onSubmit }: NewProjectModalProps) {
  const [name, setName] = useState('');
  const [primaryUrl, setPrimaryUrl] = useState('');
  const [competitorInput, setCompetitorInput] = useState('');
  const [competitors, setCompetitors] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setName('');
    setPrimaryUrl('');
    setCompetitorInput('');
    setCompetitors([]);
    setError(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const addCompetitor = () => {
    const url = competitorInput.trim();
    if (!url) return;
    if (competitors.includes(url)) return;
    setCompetitors((prev) => [...prev, url]);
    setCompetitorInput('');
  };

  const removeCompetitor = (url: string) => {
    setCompetitors((prev) => prev.filter((c) => c !== url));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addCompetitor();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('Project name is required.');
      return;
    }
    if (!primaryUrl.trim()) {
      setError('Primary URL is required.');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        name: name.trim(),
        primary_url: primaryUrl.trim(),
        competitor_urls: competitors,
      });
      reset();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create project';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={handleClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>New Analysis</h2>
          <button style={styles.closeBtn} onClick={handleClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Error */}
        {error && <div style={styles.error}>{error}</div>}

        {/* Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Project Name
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Acme Corp Audit"
              style={styles.input}
              autoFocus
            />
          </label>

          <label style={styles.label}>
            Primary URL
            <input
              type="url"
              value={primaryUrl}
              onChange={(e) => setPrimaryUrl(e.target.value)}
              placeholder="https://example.com"
              style={styles.input}
            />
          </label>

          <label style={styles.label}>
            Competitor URLs
            <span style={styles.hint}>Press Enter or click Add to add each URL</span>
            <div style={styles.competitorRow}>
              <input
                type="url"
                value={competitorInput}
                onChange={(e) => setCompetitorInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="https://competitor.com"
                style={{ ...styles.input, flex: 1 }}
              />
              <button type="button" onClick={addCompetitor} style={styles.addBtn}>
                Add
              </button>
            </div>
          </label>

          {/* Competitor chips */}
          {competitors.length > 0 && (
            <div style={styles.chips}>
              {competitors.map((url) => (
                <span key={url} style={styles.chip}>
                  {url}
                  <button
                    type="button"
                    onClick={() => removeCompetitor(url)}
                    style={styles.chipRemove}
                    aria-label={`Remove ${url}`}
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Actions */}
          <div style={styles.actions}>
            <button type="button" onClick={handleClose} style={styles.cancelBtn}>
              Cancel
            </button>
            <button type="submit" disabled={submitting} style={styles.submitBtn}>
              {submitting ? 'Starting…' : 'Start Analysis'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Styles ───────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
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
    maxWidth: 500,
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
    alignItems: 'center',
    justifyContent: 'center',
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
  hint: {
    fontWeight: font.weightRegular,
    fontSize: font.sizeXs,
    color: color.textDim,
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
  competitorRow: {
    display: 'flex',
    gap: space.xs,
  },
  addBtn: {
    padding: `${space.sm} ${space.md}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    backgroundColor: color.bgPage,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    color: color.text,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
  },
  chips: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: space.xs,
  },
  chip: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: space.xxs,
    padding: `${space.xxs} ${space.sm}`,
    borderRadius: radius.pill,
    backgroundColor: color.accentLight,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.accent,
  },
  chipRemove: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    color: color.accent,
    fontSize: font.sizeMd,
    lineHeight: 1,
    padding: 0,
    display: 'flex',
    alignItems: 'center',
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
    transition: 'background-color 0.15s',
  },
};
