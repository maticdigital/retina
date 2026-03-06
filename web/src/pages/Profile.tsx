import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { updateProfile, changePassword } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import { Sidebar } from '../components/Sidebar';
import { MobileDrawer } from '../components/MobileDrawer';
import { useIsMobile } from '../hooks/useIsMobile';
import { NAV_ITEMS } from './Dashboard';

export function Profile() {
  const { user, setUser } = useAuth();
  const isMobile = useIsMobile();

  /* ── Profile form ─────────────────────────────────── */
  const [name, setName] = useState(user?.name ?? '');
  const [profileMsg, setProfileMsg] = useState<string | null>(null);
  const [profileErr, setProfileErr] = useState<string | null>(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    setProfileErr(null);
    setSavingProfile(true);
    try {
      const updated = await updateProfile(name.trim());
      setUser(updated);
      setProfileMsg('Profile updated successfully.');
    } catch (err: unknown) {
      setProfileErr(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSavingProfile(false);
    }
  };

  /* ── Password form ────────────────────────────────── */
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [pwMsg, setPwMsg] = useState<string | null>(null);
  const [pwErr, setPwErr] = useState<string | null>(null);
  const [savingPw, setSavingPw] = useState(false);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMsg(null);
    setPwErr(null);

    if (newPw.length < 6) {
      setPwErr('New password must be at least 6 characters.');
      return;
    }
    if (newPw !== confirmPw) {
      setPwErr('Passwords do not match.');
      return;
    }

    setSavingPw(true);
    try {
      await changePassword(currentPw, newPw);
      setPwMsg('Password changed successfully.');
      setCurrentPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err: unknown) {
      setPwErr(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setSavingPw(false);
    }
  };

  const sidebarUser = {
    id: user?.id ?? '',
    name: user?.name ?? 'User',
    role: user?.role ?? '',
  };

  return (
    <div style={styles.layout}>
      {isMobile ? (
        <MobileDrawer navItems={NAV_ITEMS} user={sidebarUser} />
      ) : (
        <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
      )}

      <main style={styles.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
        <h1 style={styles.heading}>My Profile</h1>

        {/* ── Profile Section ─────────────────────────── */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>Account Details</h2>

          {profileMsg && <div style={styles.successBanner}>{profileMsg}</div>}
          {profileErr && <div style={styles.errorBanner}>{profileErr}</div>}

          <form onSubmit={handleUpdateProfile} style={styles.form}>
            <label style={styles.label}>
              Email
              <input type="email" value={user?.email ?? ''} disabled style={{ ...styles.input, ...styles.inputDisabled }} />
            </label>

            <label style={styles.label}>
              Role
              <input type="text" value={user?.role ?? ''} disabled style={{ ...styles.input, ...styles.inputDisabled }} />
            </label>

            <label style={styles.label}>
              Name
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                style={styles.input}
              />
            </label>

            <button type="submit" disabled={savingProfile} style={styles.btn}>
              {savingProfile ? 'Saving…' : 'Update Profile'}
            </button>
          </form>
        </section>

        {/* ── Password Section ────────────────────────── */}
        <section style={styles.card}>
          <h2 style={styles.sectionTitle}>Change Password</h2>

          {pwMsg && <div style={styles.successBanner}>{pwMsg}</div>}
          {pwErr && <div style={styles.errorBanner}>{pwErr}</div>}

          <form onSubmit={handleChangePassword} style={styles.form}>
            <label style={styles.label}>
              Current Password
              <input
                type="password"
                value={currentPw}
                onChange={(e) => setCurrentPw(e.target.value)}
                required
                style={styles.input}
              />
            </label>

            <label style={styles.label}>
              New Password
              <input
                type="password"
                value={newPw}
                onChange={(e) => setNewPw(e.target.value)}
                required
                minLength={6}
                style={styles.input}
              />
            </label>

            <label style={styles.label}>
              Confirm New Password
              <input
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                required
                style={styles.input}
              />
            </label>

            <button type="submit" disabled={savingPw} style={styles.btn}>
              {savingPw ? 'Changing…' : 'Change Password'}
            </button>
          </form>
        </section>
      </main>
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
    maxWidth: 700,
  },
  heading: {
    margin: 0,
    marginBottom: space.xl,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.size2xl,
    color: color.text,
  },
  card: {
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    padding: space.xl,
    boxShadow: color.shadow,
    marginBottom: space.lg,
  },
  sectionTitle: {
    margin: 0,
    marginBottom: space.md,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeLg,
    color: color.text,
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
  inputDisabled: {
    backgroundColor: color.bgPage,
    color: color.textMuted,
    cursor: 'not-allowed',
  },
  btn: {
    alignSelf: 'flex-start',
    marginTop: space.xs,
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
  successBanner: {
    padding: space.sm,
    marginBottom: space.md,
    borderRadius: radius.md,
    backgroundColor: '#DCFCE7',
    color: '#166534',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    textAlign: 'center',
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
};
