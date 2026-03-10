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

/* ── Icons for nav items ──────────────────────────── */
const DashboardIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="7" height="7" rx="1" />
    <rect x="14" y="3" width="7" height="7" rx="1" />
    <rect x="3" y="14" width="7" height="7" rx="1" />
    <rect x="14" y="14" width="7" height="7" rx="1" />
  </svg>
);

const ProjectsIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
  </svg>
);

const AdminIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
  </svg>
);

/* ── Shared nav items ─────────────────────────────── */

export const NAV_ITEMS = [
  { label: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { label: 'Projects', icon: <ProjectsIcon />, path: '/projects' },
  { label: 'Admin', icon: <AdminIcon />, path: '/admin' },
];

const SORT_OPTIONS: { label: string; value: SortOption }[] = [
  { label: 'Newest', value: 'newest' },
  { label: 'Oldest', value: 'oldest' },
  { label: 'Name', value: 'name' },
  { label: 'Score', value: 'score' },
];

const FILTER_OPTIONS: { label: string; value: FilterOption }[] = [
  { label: 'All', value: 'all' },
  { label: 'Draft', value: 'draft' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Complete', value: 'complete' },
];

/* ── Skeleton card (loading placeholder) ──────────── */

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

function EmptyState({ onNew }: { onNew: () => void }) {
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

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isMobile = useIsMobile();
  const [search, setSearch] = useState('');

  const [sort, setSort] = useState<SortOption>('newest');
  const [filter, setFilter] = useState<FilterOption>('all');
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewProject, setShowNewProject] = useState(false);

  const loadProjects = (includeArchived = false) => {
    setLoading(true);
    fetchProjects(includeArchived)
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
  }, [filter]);

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
    additional_pages: string[];
  }) => {
    const created = await createProject({
      name: data.name,
      primary_url: data.primary_url,
      competitor_urls: data.competitor_urls,
      additional_pages: data.additional_pages.length > 0 ? data.additional_pages : undefined,
    });
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
      loadProjects(filter === 'archived');
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
      if (p.archived) return false;
      if (filter !== 'all') {
        if (p.status !== filter) return false;
      }
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
        {/* Greeting */}
        <h1 style={styles.greeting}>Welcome, {user?.name ?? 'User'}</h1>

        {/* Toolbar: search + filters + new */}
        <div style={styles.toolbar} className={isMobile ? 'mobile-stack' : ''}>
          <SearchBar value={search} onChange={setSearch} />
          <div style={styles.filters} className={isMobile ? 'mobile-stack mobile-full' : ''}>
            <Select value={sort} onChange={setSort} options={SORT_OPTIONS} />
            <Select value={filter} onChange={setFilter} options={FILTER_OPTIONS} />
            <button style={{...styles.newBtn, ...(isMobile ? { width: '100%' } : {})}} onClick={() => setShowNewProject(true)}>
              + New Analysis
            </button>
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
          <EmptyState onNew={() => setShowNewProject(true)} />
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

const shimmerKeyframes = `
@keyframes shimmer {
  0% { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
`;

// Inject shimmer animation once
if (typeof document !== 'undefined' && !document.getElementById('shimmer-style')) {
  const style = document.createElement('style');
  style.id = 'shimmer-style';
  style.textContent = shimmerKeyframes;
  document.head.appendChild(style);
}

const shimmerBg = {
  background: `linear-gradient(90deg, #E0E0E0 25%, #ECECEC 50%, #E0E0E0 75%)`,
  backgroundSize: '800px 100%',
  animation: 'shimmer 1.5s infinite linear',
};

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
  greeting: {
    margin: 0,
    marginBottom: space.lg,
    fontFamily: font.family,
    fontWeight: font.weightSemibold,
    fontSize: font.size2xl,
    color: color.text,
  },
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
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: space.lg,
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
