import { useState } from 'react';
import { enableSharing, disableSharing } from '../api';
import { color, font, space, radius } from '../tokens';

interface ShareModalProps {
  projectId: string;
  isShared: boolean;
  shareToken: string | null;
  onClose: () => void;
  onUpdate: (isShared: boolean, shareToken: string | null) => void;
}

export function ShareModal({ projectId, isShared, shareToken, onClose, onUpdate }: ShareModalProps) {
  const [password, setPassword] = useState('');
  const [updatePassword, setUpdatePassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [passwordUpdated, setPasswordUpdated] = useState(false);

  const shareUrl = shareToken ? `${window.location.origin}/shared/${shareToken}` : '';

  const handleEnable = async () => {
    if (password.length < 4) {
      setError('Password must be at least 4 characters');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await enableSharing(projectId, password);
      onUpdate(true, res.share_token);
      setPassword('');
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to enable sharing');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async () => {
    if (updatePassword.length < 4) {
      setError('Password must be at least 4 characters');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await enableSharing(projectId, updatePassword);
      setUpdatePassword('');
      setPasswordUpdated(true);
      setTimeout(() => setPasswordUpdated(false), 2500);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async () => {
    setLoading(true);
    setError(null);
    try {
      await disableSharing(projectId);
      onUpdate(false, shareToken);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to disable sharing');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
        {isShared && shareToken ? (
          /* ── State 2: Sharing enabled ── */
          <>
            <h3 style={styles.heading}>Report Sharing</h3>

            <div style={styles.badge}>Sharing enabled</div>

            <label style={styles.label}>Share URL</label>
            <div style={styles.urlRow}>
              <input
                type="text"
                readOnly
                value={shareUrl}
                style={styles.urlInput}
                onFocus={(e) => e.target.select()}
              />
              <button style={styles.copyBtn} onClick={handleCopy}>
                {copied ? 'Copied!' : 'Copy Link'}
              </button>
            </div>

            <div style={styles.divider} />

            <label style={styles.label}>Update Password</label>
            <div style={styles.urlRow}>
              <input
                type="password"
                placeholder="New password (min 4 chars)"
                value={updatePassword}
                onChange={(e) => setUpdatePassword(e.target.value)}
                style={styles.input}
                onKeyDown={(e) => e.key === 'Enter' && handleUpdatePassword()}
              />
              <button
                style={styles.secondaryBtn}
                onClick={handleUpdatePassword}
                disabled={loading || updatePassword.length < 4}
              >
                {passwordUpdated ? 'Updated!' : 'Update'}
              </button>
            </div>

            {error && <p style={styles.error}>{error}</p>}

            <div style={styles.divider} />

            <button
              style={styles.dangerBtn}
              onClick={handleDisable}
              disabled={loading}
            >
              Disable Sharing
            </button>
          </>
        ) : (
          /* ── State 1: Not shared ── */
          <>
            <h3 style={styles.heading}>Share Report</h3>
            <p style={styles.description}>
              Create a password-protected link to share this report with clients or stakeholders.
            </p>

            <label style={styles.label}>Password</label>
            <input
              type="password"
              placeholder="Minimum 4 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              onKeyDown={(e) => e.key === 'Enter' && handleEnable()}
              autoFocus
            />

            {error && <p style={styles.error}>{error}</p>}

            <button
              style={styles.primaryBtn}
              onClick={handleEnable}
              disabled={loading || password.length < 4}
            >
              {loading ? 'Enabling...' : 'Enable Sharing'}
            </button>
          </>
        )}

        <button style={styles.closeBtn} onClick={onClose}>
          Cancel
        </button>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9999,
  },
  modal: {
    background: '#fff',
    borderRadius: 12,
    padding: '32px 36px',
    width: 460,
    maxWidth: '90vw',
    boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
  },
  heading: {
    fontSize: 18,
    fontWeight: 600,
    color: '#0A0A2E',
    fontFamily: font.family,
    marginTop: 0,
    marginBottom: 8,
  },
  description: {
    fontSize: 13,
    color: color.textMuted,
    fontFamily: font.family,
    marginBottom: 20,
    lineHeight: 1.5,
  },
  badge: {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: radius.pill,
    backgroundColor: '#ECFDF5',
    color: '#059669',
    fontSize: 12,
    fontWeight: 600,
    fontFamily: font.family,
    marginBottom: 20,
  },
  label: {
    display: 'block',
    fontSize: 12,
    fontWeight: 600,
    color: color.textMuted,
    fontFamily: font.family,
    marginBottom: 6,
    textTransform: 'uppercase' as const,
    letterSpacing: '0.04em',
  },
  input: {
    flex: 1,
    padding: `${space.sm} ${space.md}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    fontSize: 14,
    fontFamily: font.family,
    color: color.text,
    outline: 'none',
    width: '100%',
    boxSizing: 'border-box' as const,
  },
  urlRow: {
    display: 'flex',
    gap: 8,
    marginBottom: 8,
  },
  urlInput: {
    flex: 1,
    padding: `${space.sm} ${space.md}`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    fontSize: 13,
    fontFamily: 'monospace',
    color: color.textMuted,
    background: color.bgPage,
    outline: 'none',
    boxSizing: 'border-box' as const,
  },
  copyBtn: {
    padding: `${space.sm} 16px`,
    border: `1px solid ${color.accent}`,
    borderRadius: radius.md,
    backgroundColor: color.accent,
    color: '#fff',
    fontSize: 13,
    fontWeight: 600,
    fontFamily: font.family,
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
  },
  primaryBtn: {
    display: 'block',
    width: '100%',
    padding: '10px 24px',
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: '#fff',
    fontSize: 14,
    fontWeight: 600,
    fontFamily: font.family,
    cursor: 'pointer',
    marginTop: 20,
  },
  secondaryBtn: {
    padding: `${space.sm} 16px`,
    border: `1px solid ${color.border}`,
    borderRadius: radius.md,
    backgroundColor: color.bgCard,
    color: color.text,
    fontSize: 13,
    fontWeight: 500,
    fontFamily: font.family,
    cursor: 'pointer',
    whiteSpace: 'nowrap' as const,
  },
  dangerBtn: {
    display: 'block',
    width: '100%',
    padding: '10px 24px',
    border: '1px solid #FEE2E2',
    borderRadius: radius.pill,
    backgroundColor: '#FEF2F2',
    color: '#DC2626',
    fontSize: 14,
    fontWeight: 600,
    fontFamily: font.family,
    cursor: 'pointer',
  },
  closeBtn: {
    display: 'block',
    width: '100%',
    padding: '10px 24px',
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: 'transparent',
    color: color.textMuted,
    fontSize: 13,
    fontFamily: font.family,
    cursor: 'pointer',
    marginTop: 8,
    textAlign: 'center' as const,
  },
  divider: {
    borderTop: `1px solid ${color.border}`,
    margin: '16px 0',
  },
  error: {
    color: '#DC2626',
    fontSize: 13,
    fontFamily: font.family,
    margin: '8px 0 0',
  },
};
