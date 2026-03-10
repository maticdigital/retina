export interface Project {
  id: string;
  title: string;
  url: string;
  thumbnailUrl?: string;
  status: 'draft' | 'in_progress' | 'complete';
  createdAt: string;
  overallScore?: number;
  archived?: boolean;
}

export interface User {
  id: string;
  name: string;
  role: string;
  avatarUrl?: string;
}

export type SortOption = 'newest' | 'oldest' | 'name' | 'score';
export type FilterOption = 'all' | 'draft' | 'in_progress' | 'complete' | 'archived';

/** Map an API ProjectOut into the frontend Project shape. */
export function toProject(p: {
  id: string;
  name: string;
  primary_url: string;
  status: string;
  created_at: string;
  archived?: boolean;
  screenshot_url?: string | null;
  retina_score?: number | null;
}): Project {
  return {
    id: p.id,
    title: p.name,
    url: p.primary_url,
    thumbnailUrl: p.screenshot_url ?? undefined,
    status: p.status as Project['status'],
    createdAt: p.created_at,
    archived: p.archived ?? false,
    overallScore: p.retina_score ?? undefined,
  };
}
