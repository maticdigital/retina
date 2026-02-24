import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchUsers, inviteUser, updateUser } from '../api';
import type { AdminUser, InviteUserBody } from '../api';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import { Sidebar } from '../components/Sidebar';
import { NAV_ITEMS } from './Dashboard';

/* ── Invite Modal ─────────────────────────────────── */

function InviteModal({
  open,
  onClose,
  onSubmit,
}: {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: InviteUserBody) => Promise<void>;
}) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [role, setRole] = useState('analyst');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => { setEmail(''); setName(''); setRole('analyst'); setPassword(''); setError(null); };
  const handleClose = () => { reset(); onClose(); };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim() || !name.trim() || !password.trim()) {
      setError('All fields are required.');
      return;
    }
    setSubmitting(true);
    try {
      await onSubmit({ email: email.trim(), name: name.trim(), role, password });
      reset();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to invite user');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={modalStyles.overlay} onClick={handleClose}>
      <div style={modalStyles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={modalStyles.header}>
          <h2 style={modalStyles.title}>Invite User</h2>
          <button style={modalStyles.closeBtn} onClick={handleClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && <div style={modalStyles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={modalStyles.form}>
          <label style={modalStyles.label}>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="user@company.com" required style={modalStyles.input} autoFocus />
          </label>
          <label style={modalStyles.label}>
            Full Name
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" required style={modalStyles.input} />
          </label>
          <label style={modalStyles.label}>
            Role
            <select value={role} onChange={(e) => setRole(e.target.value)} style={modalStyles.input}>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
              <option value="owner">Owner</option>
            </select>
          </label>
          <label style={modalStyles.label}>
            Temporary Password
            <input type="text" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Minimum 6 characters" required minLength={6} style={modalStyles.input} />
          </label>

          <div style={modalStyles.actions}>
            <button type="button" onClick={handleClose} style={modalStyles.cancelBtn}>Cancel</button>
            <button type="submit" disabled={submitting} style={modalStyles.submitBtn}>
              {submitting ? 'Inviting…' : 'Invite User'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Edit Modal ───────────────────────────────────── */

function EditModal({
  open,
  user: editUser,
  onClose,
  onSubmit,
}: {
  open: boolean;
  user: AdminUser | null;
  onClose: () => void;
  onSubmit: (userId: string, data: { name?: string; role?: string; is_active?: boolean }) => Promise<void>;
}) {
  const [name, setName] = useState('');
  const [role, setRole] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (editUser) {
      setName(editUser.name);
      setRole(editUser.role);
      setIsActive(editUser.is_active);
      setError(null);
    }
  }, [editUser]);

  if (!open || !editUser) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await onSubmit(editUser.id, { name: name.trim(), role, is_active: isActive });
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update user');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={modalStyles.overlay} onClick={onClose}>
      <div style={modalStyles.modal} onClick={(e) => e.stopPropagation()}>
        <div style={modalStyles.header}>
          <h2 style={modalStyles.title}>Edit User</h2>
          <button style={modalStyles.closeBtn} onClick={onClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && <div style={modalStyles.error}>{error}</div>}

        <form onSubmit={handleSubmit} style={modalStyles.form}>
          <label style={modalStyles.label}>
            Email
            <input type="email" value={editUser.email} disabled style={{ ...modalStyles.input, backgroundColor: color.bgPage, color: color.textMuted }} />
          </label>
          <label style={modalStyles.label}>
            Name
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} style={modalStyles.input} />
          </label>
          <label style={modalStyles.label}>
            Role
            <select value={role} onChange={(e) => setRole(e.target.value)} style={modalStyles.input}>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
              <option value="owner">Owner</option>
            </select>
          </label>
          <label style={{ ...modalStyles.label, flexDirection: 'row', alignItems: 'center', gap: space.sm }}>
            <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            Active
          </label>

          <div style={modalStyles.actions}>
            <button type="button" onClick={onClose} style={modalStyles.cancelBtn}>Cancel</button>
            <button type="submit" disabled={submitting} style={modalStyles.submitBtn}>
              {submitting ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/* ── Admin Page ───────────────────────────────────── */

export function Admin() {
  const { user } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInvite, setShowInvite] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);

  useEffect(() => {
    fetchUsers()
      .then(setUsers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const sidebarUser = {
    id: user?.id ?? '',
    name: user?.name ?? 'User',
    role: user?.role ?? '',
  };

  const handleInvite = async (data: InviteUserBody) => {
    const created = await inviteUser(data);
    setUsers((prev) => [created, ...prev]);
    setShowInvite(false);
  };

  const handleUpdate = async (userId: string, data: { name?: string; role?: string; is_active?: boolean }) => {
    const updated = await updateUser(userId, data);
    setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
  };

  const isAdmin = user?.role === 'owner' || user?.role === 'admin';

  if (!isAdmin) {
    return (
      <div style={styles.layout}>
        <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
        <main style={styles.main}>
          <h1 style={styles.heading}>Admin</h1>
          <p style={styles.accessDenied}>You do not have permission to access this page.</p>
        </main>
      </div>
    );
  }

  return (
    <div style={styles.layout}>
      <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />

      <main style={styles.main}>
        <div style={styles.headerRow}>
          <h1 style={styles.heading}>User Management</h1>
          <button style={styles.inviteBtn} onClick={() => setShowInvite(true)}>
            + Invite User
          </button>
        </div>

        {error && <div style={styles.errorBanner}>{error}</div>}

        {loading ? (
          <p style={styles.loadingText}>Loading users…</p>
        ) : (
          <div style={styles.tableWrap}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Name</th>
                  <th style={styles.th}>Email</th>
                  <th style={styles.th}>Role</th>
                  <th style={styles.th}>Status</th>
                  <th style={styles.th}>Joined</th>
                  <th style={{ ...styles.th, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} style={styles.tr}>
                    <td style={styles.td}>
                      <span style={styles.userName}>{u.name}</span>
                    </td>
                    <td style={styles.td}>{u.email}</td>
                    <td style={styles.td}>
                      <span style={{
                        ...styles.badge,
                        backgroundColor: u.role === 'owner' ? color.accentLight : u.role === 'admin' ? '#FEF3C7' : color.bgPage,
                        color: u.role === 'owner' ? color.accent : u.role === 'admin' ? '#92400E' : color.textMuted,
                      }}>
                        {u.role}
                      </span>
                    </td>
                    <td style={styles.td}>
                      <span style={{
                        ...styles.badge,
                        backgroundColor: u.is_active ? '#DCFCE7' : '#FEE2E2',
                        color: u.is_active ? '#166534' : color.error,
                      }}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td style={styles.td}>
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td style={{ ...styles.td, textAlign: 'right' }}>
                      <button style={styles.editBtn} onClick={() => setEditingUser(u)}>
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      <InviteModal open={showInvite} onClose={() => setShowInvite(false)} onSubmit={handleInvite} />
      <EditModal open={!!editingUser} user={editingUser} onClose={() => setEditingUser(null)} onSubmit={handleUpdate} />
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
    marginBottom: space.xl,
  },
  heading: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.size2xl,
    color: color.text,
  },
  inviteBtn: {
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
  tableWrap: {
    backgroundColor: color.bgCard,
    borderRadius: radius.xl,
    boxShadow: color.shadow,
    overflow: 'hidden',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontFamily: font.family,
    fontSize: font.sizeSm,
  },
  th: {
    padding: `${space.sm} ${space.md}`,
    borderBottom: `1px solid ${color.border}`,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeXs,
    color: color.textMuted,
    textAlign: 'left',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.05em',
  },
  tr: {
    transition: 'background-color 0.1s',
  },
  td: {
    padding: `${space.sm} ${space.md}`,
    borderBottom: `1px solid ${color.border}`,
    color: color.text,
    verticalAlign: 'middle',
  },
  userName: {
    fontWeight: font.weightMedium,
  },
  badge: {
    display: 'inline-block',
    padding: `2px ${space.xs}`,
    borderRadius: radius.pill,
    fontSize: font.sizeXs,
    fontWeight: font.weightMedium,
    textTransform: 'capitalize' as const,
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
