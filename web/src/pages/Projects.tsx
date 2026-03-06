import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  fetchProjects,
  createProject,
  archiveProject,
  unarchiveProject,
  deleteProject,
} from '../api';
import { color, font, space, sidebar as sidebarToken, radius } from '../tokens';
import { Sidebar } from '../components/Sidebar';
import { MobileDrawer } from '../components/MobileDrawer';
import { useIsMobile } from '../hooks/useIsMobile';
import { SearchBar } from '../components/SearchBar';
import { Select } from '../components/Select';
import { ProjectCard } from '../components/ProjectCard';
import { NewProjectModal } from '../components/NewProjectModal';
import type { Project, SortOption, FilterOption } from '../types';
import { toProject } from '../types';
import { NAV_ITEMS } from './Dashboard';

type Tab = 'active' | 'archived';

const SORT_OPTIONS: { label: string; value: SortOption }[] = [
  { label: 'Newest', value: 'newest' },
  { label: 'Oldest', value: 'oldest' },
  { label: 'Name', value: 'name' },
  { label: 'Score', value: 'score' },
];

const STATUS_FILTER_OPTIONS: { label: string; value: FilterOption }[] = [
  { label: 'All', value: 'all' },
  { label: 'Draft', value: 'draft' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Complete', value: 'complete' },
];

/* ── Skeleton card (loading placeholder) ──────────── */

const shimmerKeyframes = `
@keyframes shimmer-projects {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
`;

if (typeof document !== 'undefined' && !document.getElementById('shimmer-projects-style')) {
  const style = document.createElement('style');
  style.id = 'shimmer-projects-style';
  style.textContent = shimmerKeyframes;
  document.head.appendChild(style);
}

const shimmerBg = {
  background: `linear-gradient(90deg, #E0E0E0 25%, #ECECEC 50%, #E0E0E0 75%)`,
  backgroundSize: '800px 100%',
  animation: 'shimmer-projects 1.5s infinite linear',
};

function SkeletonCard() {
  return (
    <div style={styles.skeletonCard}>
      <div style={styles.skeletonThumb} />
      <div style={styles.skeletonContent}>
        <div style={{ ...styles.skeletonLine, width: '70%' }} />
        <div style={{ ...styles.skeletonLine, width: '50%', height: 10 }} />
        <div style={{ ...styles.skeletonLine, width: 80, height: 28, borderRadius: radius.pill }} />
      </div>
    </div>
  );
}

/* ── Empty state ──────────────────────────────────── */

function EmptyState({ tab, onNew }: { tab: Tab; onNew: () => void }) {
  if (tab === 'archived') {
    return (
      <div style={styles.emptyState}>
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="1.5">
          <polyline points="21 8 21 21 3 21 3 8" />
          <rect x="1" y="3" width="22" height="5" />
          <line x1="10" y1="12" x2="14" y2="12" />
        </svg>
        <h3 style={styles.emptyTitle}>No archived projects</h3>
        <p style={styles.emptyText}>Archived projects will appear here.</p>
      </div>
    );
  }
  return (
    <div style={styles.emptyState}>
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke={color.textDim} strokeWidth="1.5">
        <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
      </svg>
      <h3 style={styles.emptyTitle}>No projects yet</h3>
      <p style={styles.emptyText}>Create your first analysis to get started.</p>
      <button style={styles.emptyButton} onClick={onNew}>+ New Analysis</button>
    </div>
  );
}

/* ── Component ────────────────────────────────────── */

export function Projects() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isMobile = useIsMobile();
  const [tab, setTab] = useState<Tab>('active');
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState<SortOption>('newest');
  const [filter, setFilter] = useState<FilterOption>('all');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewProject, setShowNewProject] = useState(false);

  const loadProjects = () => {
    setLoading(true);
    fetchProjects(tab === 'archived')
      .then((data) => {
        setProjects(data.map(toProject));
        setError(null);
      })
      .catch((err) => {
        setError(err.message ?? 'Failed to load projects');
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    loadProjects();
  }, [tab]);

  // Reset status filter when switching to archived tab
  useEffect(() => {
    if (tab === 'archived') setFilter('all');
  }, [tab]);

  const sidebarUser = {
    id: user?.id ?? '',
    name: user?.name ?? 'User',
    role: user?.role ?? '',
  };

  const handleOpenProject = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  const handleCreateProject = async (data: {
    name: string;
    primary_url: string;
    competitor_urls: string[];
  }) => {
    const created = await createProject(data);
    setShowNewProject(false);
    navigate(`/projects/${created.id}/status`);
  };

  const handleArchive = async (projectId: string) => {
    try {
      await archiveProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to archive');
    }
  };

  const handleUnarchive = async (projectId: string) => {
    try {
      await unarchiveProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to unarchive');
    }
  };

  const handleDelete = async (projectId: string) => {
    try {
      await deleteProject(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  /* ── Filter & sort ──────────────────────────────── */
  const visible = projects
    .filter((p) => {
      // Tab-level filter
      if (tab === 'archived' && !p.archived) return false;
      if (tab === 'active' && p.archived) return false;

      // Status filter (only on active tab)
      if (tab === 'active' && filter !== 'all' && p.status !== filter) return false;

      // Search
      if (search) {
        const q = search.toLowerCase();
        return p.title.toLowerCase().includes(q) || p.url.toLowerCase().includes(q);
      }
      return true;
    })
    .sort((a, b) => {
      switch (sort) {
        case 'oldest':
          return a.createdAt.localeCompare(b.createdAt);
        case 'name':
          return a.title.localeCompare(b.title);
        case 'score':
          return (b.overallScore ?? 0) - (a.overallScore ?? 0);
        case 'newest':
        default:
          return b.createdAt.localeCompare(a.createdAt);
      }
    });

  return (
    <div style={styles.layout}>
      {isMobile ? (
        <MobileDrawer navItems={NAV_ITEMS} user={sidebarUser} />
      ) : (
        <Sidebar navItems={NAV_ITEMS} user={sidebarUser} />
      )}

      <main style={styles.main} className={isMobile ? 'mobile-main mobile-pad-top' : ''}>
        {/* Page heading */}
        <h1 style={styles.heading}>Projects</h1>

        {/* Tab bar */}
        <div style={styles.tabBar}>
          <button
            style={tab === 'active' ? { ...styles.tab, ...styles.tabActive } : styles.tab}
            onClick={() => setTab('active')}
          >
            Active
          </button>
          <button
            style={tab === 'archived' ? { ...styles.tab, ...styles.tabActive } : styles.tab}
            onClick={() => setTab('archived')}
          >
            Archived
          </button>
        </div>

        {/* Toolbar: search + filters + new */}
        <div style={styles.toolbar} className={isMobile ? 'mobile-stack' : ''}>
          <SearchBar value={search} onChange={setSearch} />
          <div style={styles.filters} className={isMobile ? 'mobile-stack mobile-full' : ''}>
            <Select value={sort} onChange={setSort} options={SORT_OPTIONS} />
            {tab === 'active' && (
              <Select value={filter} onChange={setFilter} options={STATUS_FILTER_OPTIONS} />
            )}
            {tab === 'active' && (
              <button style={{...styles.newBtn, ...(isMobile ? { width: '100%' } : {})}} onClick={() => setShowNewProject(true)}>
                + New Analysis
              </button>
            )}
          </div>
        </div>

        {/* Error */}
        {error && <div style={styles.errorBanner}>{error}</div>}

        {/* Project Grid */}
        {loading ? (
          <div style={styles.grid} className={isMobile ? 'mobile-grid-1' : ''}>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </div>
        ) : visible.length === 0 && !search && filter === 'all' ? (
          <EmptyState tab={tab} onNew={() => setShowNewProject(true)} />
        ) : visible.length === 0 ? (
          <p style={styles.noResults}>No projects match your search.</p>
        ) : (
          <div style={styles.grid} className={isMobile ? 'mobile-grid-1' : ''}>
            {visible.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onOpen={handleOpenProject}
                onArchive={handleArchive}
                onUnarchive={handleUnarchive}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </main>

      {/* New Project Modal */}
      <NewProjectModal
        open={showNewProject}
        onClose={() => setShowNewProject(false)}
        onSubmit={handleCreateProject}
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
    maxWidth: 1200,
  },
  heading: {
    margin: 0,
    marginBottom: space.lg,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.size2xl,
    color: color.text,
  },

  /* Tab bar */
  tabBar: {
    display: 'flex',
    gap: space.xs,
    marginBottom: space.lg,
    borderBottom: `1px solid ${color.border}`,
  },
  tab: {
    padding: `${space.sm} ${space.lg}`,
    border: 'none',
    borderBottom: '2px solid transparent',
    background: 'none',
    fontFamily: font.family,
    fontSize: font.sizeBase,
    fontWeight: font.weightMedium,
    color: color.textMuted,
    cursor: 'pointer',
    transition: 'color 0.15s, border-color 0.15s',
  },
  tabActive: {
    color: color.accent,
    borderBottomColor: color.accent,
    fontWeight: font.weightSemibold,
  },

  /* Toolbar */
  toolbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: space.md,
    marginBottom: space.xl,
  },
  filters: {
    display: 'flex',
    gap: space.sm,
    flexShrink: 0,
  },
  newBtn: {
    padding: `${space.sm} ${space.lg}`,
    border: 'none',
    borderRadius: radius.pill,
    backgroundColor: color.accent,
    color: color.textOnAccent,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    fontWeight: font.weightSemibold,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    transition: 'background-color 0.15s',
  },

  /* Grid */
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: space.lg,
  },

  /* Error */
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

  /* Skeleton card */
  skeletonCard: {
    backgroundColor: color.bgCard,
    borderRadius: radius.lg,
    overflow: 'hidden',
    boxShadow: color.shadow,
  },
  skeletonThumb: {
    width: '100%',
    aspectRatio: '16 / 10',
    ...shimmerBg,
  },
  skeletonContent: {
    padding: space.md,
    display: 'flex',
    flexDirection: 'column',
    gap: space.sm,
  },
  skeletonLine: {
    height: 14,
    borderRadius: radius.sm,
    ...shimmerBg,
  },

  /* Empty state */
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: `${space.xxl} 0`,
    gap: space.sm,
  },
  emptyTitle: {
    margin: 0,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.sizeLg,
    color: color.text,
  },
  emptyText: {
    margin: 0,
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
  },
  emptyButton: {
    marginTop: space.sm,
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

  /* No results */
  noResults: {
    fontFamily: font.family,
    fontSize: font.sizeSm,
    color: color.textMuted,
    textAlign: 'center',
    padding: space.xl,
  },
};
