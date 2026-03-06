import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { color, font, space, radius } from '../tokens';
import type { User } from '../types';

interface NavItem {
  label: string;
  icon: React.ReactNode;
  path: string;
}

interface MobileDrawerProps {
  navItems: NavItem[];
  user: User;
}

export function MobileDrawer({ navItems, user }: MobileDrawerProps) {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const go = (path: string) => {
    setOpen(false);
    navigate(path);
  };

  const handleSignOut = async () => {
    setOpen(false);
    await logout();
    navigate('/login');
  };

  return (
    <>
      {/* ── Top bar ──────────────────────────────── */}
      <header style={styles.topBar}>
        <div style={styles.logoWrap} onClick={() => go('/')} role="button">
          <LogoMark />
          <div style={styles.logoText}>
            <span style={styles.logoLine}>Matic</span>
            <span style={styles.logoLine}>Retina</span>
          </div>
        </div>
        <button style={styles.hamburger} onClick={() => setOpen(true)} aria-label="Open menu">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color.text} strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
      </header>

      {/* ── Backdrop + Drawer ────────────────────── */}
      {open && (
        <>
          <div style={styles.backdrop} onClick={() => setOpen(false)} />
          <aside style={styles.drawer}>
            {/* Close button */}
            <div style={styles.drawerHeader}>
              <button style={styles.closeBtn} onClick={() => setOpen(false)} aria-label="Close menu">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke={color.text} strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {/* Navigation */}
            <nav style={styles.nav}>
              {navItems.map((item) => {
                const isActive = location.pathname === item.path
                  || (item.path === '/' && location.pathname.startsWith('/report'));
                return (
                  <button
                    key={item.label}
                    onClick={() => go(item.path)}
                    style={{
                      ...styles.navItem,
                      ...(isActive ? styles.navItemActive : {}),
                    }}
                  >
                    <span style={styles.navIcon}>{item.icon}</span>
                    {item.label}
                  </button>
                );
              })}
            </nav>

            {/* User section */}
            <div style={styles.userSection}>
              <div style={styles.divider} />
              <div style={styles.userInfo}>
                <div style={styles.avatar}>
                  <span style={styles.avatarFallback}>
                    {user.name.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <div style={styles.userName}>{user.name}</div>
                  <div style={styles.userRole}>{user.role}</div>
                </div>
              </div>
              <button style={styles.menuItem} onClick={() => go('/profile')}>
                My Profile
              </button>
              <button style={styles.menuItem} onClick={() => go('/profile')}>
                Change Password
              </button>
              <button style={{ ...styles.menuItem, color: color.error }} onClick={handleSignOut}>
                Sign Out
              </button>
            </div>
          </aside>
        </>
      )}
    </>
  );
}

/* ── Icons ───────────────────────────────────────── */

function LogoMark() {
  return (
    <svg width="28" height="28" viewBox="0 0 664 664" fill="none">
      <path
        d="M332 20C149 20 0 169 0 352h87c0-135 110-245 245-245s245 110 245 245h87C664 169 515 20 332 20Zm101 332c0-56-45-101-101-101s-101 45-101 101 45 101 101 101 101-45 101-101Zm87 0c0 104-85 188-188 188S144 456 144 352s85-188 188-188 188 85 188 188Zm-130 0c0 32-26 58-58 58s-58-26-58-58 26-58 58-58 58 26 58 58Z"
        fill={color.text}
      />
    </svg>
  );
}

/* ── Styles ───────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  /* Top bar — fixed at top */
  topBar: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    height: 56,
    backgroundColor: color.bgCard,
    borderBottom: `1px solid ${color.border}`,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: `0 ${space.md}`,
    zIndex: 100,
  },
  logoWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: space.xs,
    cursor: 'pointer',
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
    lineHeight: 1.1,
  },
  logoLine: {
    fontFamily: font.family,
    fontWeight: font.weightBold,
    fontSize: '0.875rem',
    color: color.text,
  },
  hamburger: {
    background: 'none',
    border: 'none',
    padding: space.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  /* Backdrop */
  backdrop: {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(0,0,0,0.4)',
    zIndex: 200,
  },

  /* Drawer */
  drawer: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    width: 280,
    maxWidth: '80vw',
    backgroundColor: color.bgCard,
    boxShadow: '-4px 0 16px rgba(0,0,0,0.12)',
    zIndex: 201,
    display: 'flex',
    flexDirection: 'column',
    padding: space.lg,
    overflowY: 'auto',
  },
  drawerHeader: {
    display: 'flex',
    justifyContent: 'flex-end',
    marginBottom: space.lg,
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    padding: space.xs,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },

  /* Nav items */
  nav: {
    display: 'flex',
    flexDirection: 'column',
    gap: space.xs,
    flex: 1,
  },
  navItem: {
    display: 'flex',
    alignItems: 'center',
    gap: space.sm,
    padding: `${space.sm} ${space.md}`,
    border: 'none',
    borderRadius: radius.lg,
    background: 'none',
    fontFamily: font.family,
    fontSize: font.sizeBase,
    fontWeight: font.weightMedium,
    color: color.text,
    cursor: 'pointer',
    textAlign: 'left' as const,
    width: '100%',
  },
  navItemActive: {
    backgroundColor: color.accentLight,
    color: color.accent,
    fontWeight: font.weightSemibold,
  },
  navIcon: {
    display: 'flex',
    alignItems: 'center',
    fontSize: font.sizeMd,
  },

  /* User section */
  userSection: {
    marginTop: 'auto',
  },
  divider: {
    height: 1,
    backgroundColor: color.border,
    margin: `${space.md} 0`,
  },
  userInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: space.sm,
    marginBottom: space.md,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: '50%',
    backgroundColor: color.bgHover,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  avatarFallback: {
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },
  userName: {
    fontFamily: font.family,
    fontWeight: font.weightMedium,
    fontSize: font.sizeSm,
    color: color.text,
  },
  userRole: {
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textDim,
  },
  menuItem: {
    display: 'flex',
    alignItems: 'center',
    gap: space.xs,
    width: '100%',
    padding: `${space.sm} ${space.md}`,
    border: 'none',
    borderRadius: radius.md,
    background: 'none',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    color: color.text,
    cursor: 'pointer',
    textAlign: 'left' as const,
  },
};
