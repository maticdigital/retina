import { useState, useRef, useEffect } from 'react';
import { color, font, space, radius } from '../tokens';
import type { Project } from '../types';

interface ProjectCardProps {
  project: Project;
  onOpen?: (projectId: string) => void;
  onArchive?: (projectId: string) => void;
  onUnarchive?: (projectId: string) => void;
  onDelete?: (projectId: string) => void;
}

export function ProjectCard({ project, onOpen, onArchive, onUnarchive, onDelete }: ProjectCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on outside click
  useEffect(() => {
    if (!menuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
        setConfirmDelete(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [menuOpen]);

  return (
    <div style={styles.card}>
      {/* Thumbnail */}
      <div style={styles.thumbnail}>
        {project.thumbnailUrl ? (
          <img
            src={project.thumbnailUrl}
            alt={project.title}
            style={styles.thumbnailImg}
          />
        ) : (
          <div style={styles.thumbnailPlaceholder}>
            <ImagePlaceholderIcon />
          </div>
        )}

        {/* Archived badge */}
        {project.archived && (
          <div style={styles.archivedBadge}>Archived</div>
        )}
      </div>

      {/* Content */}
      <div style={styles.content}>
        <div style={styles.titleRow}>
          <h3 style={styles.title}>{project.title}</h3>
          {/* "..." menu button */}
          <div ref={menuRef} style={styles.menuContainer}>
            <button
              style={styles.menuBtn}
              onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen); setConfirmDelete(false); }}
              aria-label="Project actions"
            >
              <MoreIcon />
            </button>
            {menuOpen && (
              <div style={styles.menuDropdown}>
                {!project.archived ? (
                  <button
                    style={styles.menuItem}
                    onClick={() => { setMenuOpen(false); onArchive?.(project.id); }}
                  >
                    <ArchiveIcon /> Archive Project
                  </button>
                ) : (
                  <>
                    <button
                      style={styles.menuItem}
                      onClick={() => { setMenuOpen(false); onUnarchive?.(project.id); }}
                    >
                      <UnarchiveIcon /> Unarchive
                    </button>
                    {!confirmDelete ? (
                      <button
                        style={{ ...styles.menuItem, color: color.error }}
                        onClick={() => setConfirmDelete(true)}
                      >
                        <DeleteIcon /> Delete
                      </button>
                    ) : (
                      <button
                        style={styles.menuItemDanger}
                        onClick={() => { setMenuOpen(false); setConfirmDelete(false); onDelete?.(project.id); }}
                      >
                        Confirm Delete
                      </button>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        </div>
        <p style={styles.url}>{project.url}</p>
        <button
          style={styles.openButton}
          onClick={() => onOpen?.(project.id)}
        >
          Open
          <ArrowIcon />
        </button>
      </div>
    </div>
  );
}

/* ── Icons ────────────────────────────────────────── */

function ImagePlaceholderIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="1.5">
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <path d="M3 16l5-5 4 4 4-4 5 5" />
      <circle cx="8.5" cy="8.5" r="1.5" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ marginLeft: 4 }}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8l4 4-4 4M8 12h8" />
    </svg>
  );
}

function MoreIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="5" r="2" />
      <circle cx="12" cy="12" r="2" />
      <circle cx="12" cy="19" r="2" />
    </svg>
  );
}

function ArchiveIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 6, flexShrink: 0 }}>
      <rect x="2" y="3" width="20" height="5" rx="1" />
      <path d="M4 8v11a2 2 0 002 2h12a2 2 0 002-2V8" />
      <path d="M10 12h4" />
    </svg>
  );
}

function UnarchiveIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 6, flexShrink: 0 }}>
      <rect x="2" y="3" width="20" height="5" rx="1" />
      <path d="M4 8v11a2 2 0 002 2h12a2 2 0 002-2V8" />
      <path d="M12 11v5M9 14l3-3 3 3" />
    </svg>
  );
}

function DeleteIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: 6, flexShrink: 0 }}>
      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" />
      <path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
    </svg>
  );
}

/* ── Styles ────────────────────────────────────────── */

const styles: Record<string, React.CSSProperties> = {
  card: {
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    overflow: 'hidden',
    boxShadow: color.shadow,
    transition: 'box-shadow 0.2s ease, transform 0.2s ease',
    cursor: 'default',
    position: 'relative',
  },
  thumbnail: {
    width: '100%',
    aspectRatio: '16 / 10',
    backgroundColor: '#E0E0E0',
    position: 'relative',
    overflow: 'hidden',
  },
  thumbnailImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover' as const,
  },
  thumbnailPlaceholder: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'flex-end',
    padding: space.sm,
  },
  archivedBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    padding: '2px 8px',
    borderRadius: radius.sm,
    backgroundColor: 'rgba(0,0,0,0.6)',
    color: '#fff',
    fontFamily: font.family,
    fontSize: font.sizeXs,
    fontWeight: font.weightMedium,
  },
  content: {
    padding: space.md,
  },
  titleRow: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: space.xs,
  },
  title: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeMd,
    color: color.text,
    lineHeight: 1.3,
    flex: 1,
  },
  url: {
    margin: `${space.xxs} 0 ${space.sm}`,
    fontFamily: font.family,
    fontSize: font.sizeXs,
    color: color.textDim,
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  openButton: {
    display: 'inline-flex',
    alignItems: 'center',
    padding: `${space.xs} ${space.md}`,
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightMedium,
    cursor: 'pointer',
    transition: 'background-color 0.15s ease',
  },

  /* Menu */
  menuContainer: {
    position: 'relative',
  },
  menuBtn: {
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: '4px',
    borderRadius: radius.sm,
    color: color.textMuted,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 0.15s',
  },
  menuDropdown: {
    position: 'absolute',
    top: '100%',
    right: 0,
    marginTop: 4,
    minWidth: 160,
    backgroundColor: color.bgCard,
    borderRadius: radius.md,
    boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
    border: `1px solid ${color.border}`,
    zIndex: 50,
    overflow: 'hidden',
  },
  menuItem: {
    display: 'flex',
    alignItems: 'center',
    width: '100%',
    padding: '8px 12px',
    border: 'none',
    background: 'none',
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.text,
    cursor: 'pointer',
    textAlign: 'left',
    transition: 'background-color 0.1s',
  },
  menuItemDanger: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '100%',
    padding: '8px 12px',
    border: 'none',
    backgroundColor: color.error,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    color: '#fff',
    cursor: 'pointer',
    textAlign: 'center',
  },
};
