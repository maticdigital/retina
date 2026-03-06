import { useState } from 'react';
import { Link } from 'react-router-dom';
import { requestPasswordReset } from '../api';
import { color, font, space, radius } from '../tokens';

export function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ found: boolean; detail: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setSubmitting(true);
    try {
      const resp = await requestPasswordReset(email);
      setResult(resp);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        {/* Logo */}
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

        <h1 style={styles.heading}>Reset your password</h1>

        {/* Success state */}
        {result?.found && (
          <div style={styles.success}>{result.detail}</div>
        )}

        {/* Not-found state */}
        {result && !result.found && (
          <div style={styles.warning}>{result.detail}</div>
        )}

        {/* Error */}
        {error && <div style={styles.error}>{error}</div>}

        {/* Only show form if we haven't gotten a success response */}
        {!result?.found && (
          <form onSubmit={handleSubmit} style={styles.form}>
            <label style={styles.label}>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                style={styles.input}
              />
            </label>

            <button type="submit" disabled={submitting} style={styles.button}>
              {submitting ? 'Sending…' : 'Send Reset Link'}
            </button>
          </form>
        )}

        <Link to="/login" style={styles.backLink}>
          ← Back to sign in
        </Link>
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
  },
  backLink: {
    marginTop: space.md,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.accent,
    textDecoration: 'none',
  },
};
