import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { resetPassword } from '../api';
import { color, font, space, radius } from '../tokens';

export function ResetPassword() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extract access_token from URL hash on mount
  // Supabase redirects with: /reset-password#access_token=...&type=recovery
  useEffect(() => {
    const hash = window.location.hash.substring(1); // remove '#'
    const params = new URLSearchParams(hash);
    const token = params.get('access_token');
    const type = params.get('type');

    if (token && type === 'recovery') {
      setAccessToken(token);
    } else if (hash) {
      // Hash present but missing expected params
      setError('Invalid reset link. Please request a new one.');
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!accessToken) {
      setError('Missing reset token. Please use the link from your email.');
      return;
    }

    setSubmitting(true);
    try {
      await resetPassword(accessToken, newPassword);
      setSuccess(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setSubmitting(false);
    }
  };

  // No token in URL — show a helpful message
  if (!accessToken && !error) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>
          <Logo />
          <h1 style={styles.heading}>Reset your password</h1>
          <div style={styles.warning}>
            No reset token found. Please use the link from your email, or request a new one.
          </div>
          <Link to="/forgot-password" style={styles.backLink}>
            Request a new reset link
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <Logo />
        <h1 style={styles.heading}>
          {success ? 'Password updated' : 'Set a new password'}
        </h1>

        {success && (
          <>
            <div style={styles.success}>
              Your password has been updated successfully.
            </div>
            <Link to="/login" style={styles.button as React.CSSProperties}>
              Sign in
            </Link>
          </>
        )}

        {error && <div style={styles.error}>{error}</div>}

        {!success && (
          <form onSubmit={handleSubmit} style={styles.form}>
            <label style={styles.label}>
              New password
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={8}
                style={styles.input}
              />
            </label>

            <label style={styles.label}>
              Confirm password
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                required
                minLength={8}
                style={styles.input}
              />
            </label>

            <button type="submit" disabled={submitting} style={styles.button}>
              {submitting ? 'Updating…' : 'Update Password'}
            </button>
          </form>
        )}

        {!success && (
          <Link to="/login" style={styles.backLink}>
            ← Back to sign in
          </Link>
        )}
      </div>
    </div>
  );
}

/* ── Shared logo component ─────────────────────────── */

function Logo() {
  return (
    <div style={styles.logoWrap}>
      <svg width="40" height="40" viewBox="0 0 664 664" fill="none">
        <path
          d="M332 20C149 20 0 169 0 352h87c0-135 110-245 245-245s245 110 245 245h87C664 169 515 20 332 20Zm101 332c0-56-45-101-101-101s-101 45-101 101 45 101 101 101 101-45 101-101Zm87 0c0 104-85 188-188 188S144 456 144 352s85-188 188-188 188 85 188 188Zm-130 0c0 32-26 58-58 58s-58-26-58-58 26-58 58-58 58 26 58 58Z"
          fill={color.text}
        />
      </svg>
      <div style={styles.logoText}>
        <span style={styles.logoLine}>Matic</span>
        <span style={styles.logoLine}>Retina</span>
      </div>
    </div>
  );
}

/* ── Styles ───────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
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
  },
  success: {
    width: '100%',
    padding: space.sm,
    marginBottom: space.md,
    borderRadius: radius.md,
    backgroundColor: '#DCFCE7',
    color: '#166534',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    textAlign: 'center',
  },
  warning: {
    width: '100%',
    padding: space.sm,
    marginBottom: space.md,
    borderRadius: radius.md,
    backgroundColor: '#FEF3C7',
    color: '#92400E',
    fontFamily: font.family,
    fontSize: font.sizeSm,
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
    transition: 'background-color 0.15s',
    textAlign: 'center',
    textDecoration: 'none',
    display: 'inline-block',
  },
  backLink: {
    marginTop: space.md,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.accent,
    textDecoration: 'none',
  },
};
