import { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { color, font, space, radius, sidebar as sidebarToken } from '../tokens';
import type { User } from '../types';

interface NavItem {
  label: string;
  icon: React.ReactNode;
  path: string;
}

interface SidebarProps {
  navItems: NavItem[];
  user: User;
}

export function Sidebar({ navItems, user }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  /* Close menu when clicking outside */
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  const handleSignOut = async () => {
    setMenuOpen(false);
    await logout();
    navigate('/login');
  };

  return (
    <aside style={styles.root}>
      {/* Logo */}
      <div style={styles.logoWrap} onClick={() => navigate('/')} role="button">
        <LogoMark />
        <div style={styles.logoText}>
          <span style={styles.logoCompany}>Matic</span>
          <span style={styles.logoProduct}>Retina</span>
        </div>
      </div>

      {/* Navigation — all items are purple pills */}
      <nav style={styles.nav}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path
            || (item.path === '/' && location.pathname.startsWith('/report'));
          return (
            <button
              key={item.label}
              onClick={() => navigate(item.path)}
              style={{
                ...styles.navButton,
                ...(isActive ? styles.navButtonActive : {}),
              }}
            >
              <span style={styles.navIcon}>{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* User Profile with dropdown */}
      <div style={styles.userWrapper} ref={menuRef}>
        {menuOpen && (
          <div style={styles.menu}>
            <button
              style={styles.menuItem}
              onClick={() => { setMenuOpen(false); navigate('/profile'); }}
            >
              <ProfileIcon /> My Profile
            </button>
            <button
              style={styles.menuItem}
              onClick={() => { setMenuOpen(false); navigate('/profile'); }}
            >
              <LockIcon /> Change Password
            </button>
            <div style={styles.menuDivider} />
            <button style={{ ...styles.menuItem, color: color.error }} onClick={handleSignOut}>
              <LogoutIcon /> Sign Out
            </button>
          </div>
        )}

        <div
          style={styles.userSection}
          onClick={() => setMenuOpen((v) => !v)}
          role="button"
        >
          <div style={styles.avatar}>
            {user.avatarUrl ? (
              <img src={user.avatarUrl} alt={user.name} style={styles.avatarImg} />
            ) : (
              <span style={styles.avatarFallback}>
                {user.name.charAt(0).toUpperCase()}
              </span>
            )}
          </div>
          <div style={styles.userInfo}>
            <span style={styles.userName}>{user.name}</span>
            <span style={styles.userRole}>{user.role}</span>
          </div>
          <ChevronIcon />
        </div>
      </div>
    </aside>
  );
}

/* ── Mini icons ──────────────────────────────────── */

function LogoMark() {
  return (
    <svg width="36" height="36" viewBox="0 0 664 664" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M332 20C149 20 0 169 0 352h87c0-135 110-245 245-245s245 110 245 245h87C664 169 515 20 332 20Zm101 332c0-56-45-101-101-101s-101 45-101 101 45 101 101 101 101-45 101-101Zm87 0c0 104-85 188-188 188S144 456 144 352s85-188 188-188 188 85 188 188Zm-130 0c0 32-26 58-58 58s-58-26-58-58 26-58 58-58 58 26 58 58Z"
        fill={color.text}
      />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="2" style={{ marginLeft: 'auto', flexShrink: 0 }}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

function ProfileIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0110 0v4" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

/* ── Styles ───────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  root: {
    width: sidebarToken.width,
    minHeight: '100vh',
    backgroundColor: sidebarToken.bgColor,
    display: 'flex',
    flexDirection: 'column',
    padding: `${space.lg} ${space.md}`,
    boxSizing: 'border-box',
    borderRight: `1px solid ${color.border}`,
    position: 'fixed',
    left: 0,
    top: 0,
    bottom: 0,
    zIndex: 10,
  },
  logoWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: space.xs,
    marginBottom: space.xl,
    cursor: 'pointer',
  },
  logoText: {
    display: 'flex',
    flexDirection: 'column',
    lineHeight: 1.15,
  },
  logoCompany: {
    fontFamily: font.family,
    fontWeight: font.weightBold,
    fontSize: font.sizeMd,
    color: color.text,
  },
  logoProduct: {
    fontFamily: font.family,
    fontWeight: font.weightBold,
    fontSize: font.sizeMd,
    color: color.text,
  },
  nav: {
    display: 'flex',
    flexDirection: 'column',
    gap: space.xs,
    flex: 1,
  },
  navButton: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: space.xs,
    padding: `6px ${space.sm}`,
    border: 'none',
    borderRadius: radius.pill,
    background: color.accent,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
    textAlign: 'left' as const,
    width: 'fit-content',
  },
  navButtonActive: {
    boxShadow: `0 0 0 2px ${color.accentHover}`,
  },
  navIcon: {
    display: 'flex',
    alignItems: 'center',
    fontSize: font.sizeBase,
  },

  /* User section */
  userWrapper: {
    position: 'relative',
    marginTop: 'auto',
    paddingTop: space.lg,
  },
  userSection: {
    display: 'flex',
    alignItems: 'center',
    gap: space.sm,
    cursor: 'pointer',
    padding: space.xs,
    borderRadius: radius.md,
    transition: 'background-color 0.15s',
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: '50%',
    overflow: 'hidden',
    backgroundColor: color.bgHover,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  avatarImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const,
  },
  avatarFallback: {
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },
  userInfo: {
    display: 'flex',
    flexDirection: 'column',
    minWidth: 0,
    flex: 1,
  },
  userName: {
    fontFamily: font.family,
    fontWeight: font.weightMedium,
    fontSize: font.sizeSm,
    color: color.text,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  userRole: {
    fontFamily: font.family,
    fontWeight: font.weightRegular,
    fontSize: font.sizeXs,
    color: color.textDim,
  },

  /* Dropdown menu */
  menu: {
    position: 'absolute',
    bottom: '100%',
    left: 0,
    right: 0,
    marginBottom: space.xs,
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
    border: `1px solid ${color.border}`,
    padding: space.xs,
    zIndex: 20,
  },
  menuItem: {
    display: 'flex',
    alignItems: 'center',
    gap: space.xs,
    width: '100%',
    padding: `${space.sm} ${space.sm}`,
    border: 'none',
    borderRadius: radius.md,
    background: 'none',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    color: color.text,
    cursor: 'pointer',
    textAlign: 'left' as const,
    transition: 'background-color 0.1s',
  },
  menuDivider: {
    height: 1,
    backgroundColor: color.border,
    margin: `${space.xxs} 0`,
  },
};
