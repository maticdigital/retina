/**
 * Thin API client that talks to the FastAPI backend at :8000.
 */

const BASE = 'http://localhost:8000';

/** Get the stored access token. */
export function getToken(): string | null {
  return localStorage.getItem('access_token');
}

/** Store (or clear) the access token. */
export function setToken(token: string | null) {
  if (token) {
    localStorage.setItem('access_token', token);
  } else {
    localStorage.removeItem('access_token');
  }
}

/** Authenticated fetch wrapper. */
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...init, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));

    // Auto-logout on expired/invalid token
    if (res.status === 401) {
      localStorage.removeItem('access_token');
    }

    throw new ApiError(res.status, body.detail ?? 'Request failed');
  }

  return res.json() as Promise<T>;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

/* ── Auth endpoints ─────────────────────────────────────────────────────── */

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: string;
}

interface LoginResponse extends AuthUser {
  access_token: string;
}

export async function login(email: string, password: string): Promise<AuthUser> {
  const data = await apiFetch<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return { id: data.id, email: data.email, name: data.name, role: data.role };
}

export async function logout(): Promise<void> {
  try {
    await apiFetch('/auth/logout', { method: 'POST' });
  } finally {
    setToken(null);
  }
}

export async function getMe(): Promise<AuthUser> {
  return apiFetch<AuthUser>('/auth/me');
}

export async function updateProfile(name: string): Promise<AuthUser> {
  return apiFetch<AuthUser>('/auth/me', {
    method: 'PUT',
    body: JSON.stringify({ name }),
  });
}

export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<void> {
  await apiFetch('/auth/change-password', {
    method: 'POST',
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

/* ── Project endpoints ─────────────────────────────────────────────────── */

export interface ProjectOut {
  id: string;
  name: string;
  primary_url: string;
  competitor_urls: string[];
  status: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  archived?: boolean;
  screenshot_url?: string | null;
}

export interface ProjectDetail extends ProjectOut {
  project_data: Record<string, unknown>[];
  reports: Record<string, unknown>[];
  analyst_scores: Record<string, unknown>[];
}

export interface CreateProjectBody {
  name: string;
  primary_url: string;
  competitor_urls?: string[];
}

export async function fetchProjects(includeArchived = false): Promise<ProjectOut[]> {
  const qs = includeArchived ? '?include_archived=true' : '';
  return apiFetch<ProjectOut[]>(`/projects${qs}`);
}

export async function archiveProject(projectId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/archive`, { method: 'PATCH' });
}

export async function unarchiveProject(projectId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/unarchive`, { method: 'PATCH' });
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}`, { method: 'DELETE' });
}

export async function createProject(body: CreateProjectBody): Promise<ProjectOut> {
  return apiFetch<ProjectOut>('/projects', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  return apiFetch<ProjectDetail>(`/projects/${projectId}`);
}

/* ── Competitor endpoints ─────────────────────────────────────────────── */

export async function addCompetitor(projectId: string, url: string): Promise<{ ok: boolean; url: string }> {
  return apiFetch(`/projects/${projectId}/competitors`, {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export async function removeCompetitor(projectId: string, compIndex: number): Promise<{ ok: boolean }> {
  return apiFetch(`/projects/${projectId}/competitors/${compIndex}`, {
    method: 'DELETE',
  });
}

/* ── Project Summary ──────────────────────────────────────────────────── */

export interface LensScore {
  lens_id: string;
  lens_name: string;
  score: number | null;
  max_score: number;
}

export interface CompetitorSummary {
  url: string;
  retina_score: number | null;
  status?: 'ready' | 'processing';
}

export interface RecommendationItem {
  title: string;
  description?: string;
  lens?: string;
}

export interface RecommendationQuadrant {
  quadrant: string;
  items: (string | RecommendationItem)[];
}

export interface TechStack {
  cms?: string[];
  framework?: string[];
  hosting?: string[];
  analytics?: string[];
  cdn?: string[];
  crm?: string[];
}

export interface ProjectSummary {
  id: string;
  name: string;
  primary_url: string;
  status: string;
  screenshot_url: string | null;
  retina_score: number | null;
  lens_scores: LensScore[];
  tech_stack?: TechStack;
  competitors: CompetitorSummary[];
  recommendations: RecommendationQuadrant[];
}

export async function getProjectSummary(projectId: string): Promise<ProjectSummary> {
  return apiFetch<ProjectSummary>(`/projects/${projectId}/summary`);
}

export async function generateRecommendations(projectId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/recommendations/generate`, { method: 'POST' });
}

export interface QuadrantData {
  no_brainers: RecommendationItem[];
  quick_wins: RecommendationItem[];
  growth_moves: RecommendationItem[];
  transformational: RecommendationItem[];
}

export async function saveRecommendations(projectId: string, data: QuadrantData): Promise<void> {
  await apiFetch(`/projects/${projectId}/recommendations`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

/* ── Lens Detail ─────────────────────────────────────────────────────── */

export interface LensDetailData {
  project_id: string;
  project_name: string;
  lens_id: string;
  lens_name: string;
  lens_color: string;
  lens_score: number | null;
  max_score: number;
  lens_scores: LensScore[];
  lighthouse_data: {
    mobile?: {
      lighthouse_scores?: Record<string, number>;
      core_web_vitals?: Record<string, number | null>;
      audits?: Array<{
        id: string;
        score: number | null;
        title: string;
        weight?: number;
        category: string;
        description?: string;
      }>;
    };
    desktop?: {
      lighthouse_scores?: Record<string, number>;
      core_web_vitals?: Record<string, number | null>;
      audits?: Array<{
        id: string;
        score: number | null;
        title: string;
        weight?: number;
        category: string;
        description?: string;
      }>;
    };
  };
  builtwith_data: {
    technologies?: Array<{
      name: string;
      tag?: string;
      categories?: string[];
      description?: string;
      link?: string;
    }>;
    meta?: Record<string, string>;
    social_profiles?: string[];
  };
  interpretations: Record<string, unknown>;
  analyst_sub_scores: Record<string, { score: number; observation: string }>;
  analyst_observations: string;
  user_observations: string | null;
  artifacts: Artifact[];
}

export interface Artifact {
  id: string;
  file_url: string;
  file_name: string;
  uploaded_by: string;
  storage_path?: string;
}

export async function getLensDetail(projectId: string, lensId: string): Promise<LensDetailData> {
  return apiFetch<LensDetailData>(`/projects/${projectId}/lens/${lensId}`);
}

export async function saveLensObservations(projectId: string, lensId: string, text: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/lens/${lensId}/observations`, {
    method: 'PATCH',
    body: JSON.stringify({ text }),
  });
}

/* ── Artifact endpoints ──────────────────────────────────────────────── */

export async function uploadArtifact(
  projectId: string,
  lensId: string,
  file: File,
): Promise<Artifact> {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE}/projects/${projectId}/lens/${lensId}/artifacts`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? 'Upload failed');
  }

  return res.json() as Promise<Artifact>;
}

export async function deleteArtifact(
  projectId: string,
  lensId: string,
  artifactId: string,
): Promise<void> {
  await apiFetch(`/projects/${projectId}/lens/${lensId}/artifacts/${artifactId}`, {
    method: 'DELETE',
  });
}

/* ── Screenshot endpoints ─────────────────────────────────────────────── */

export async function uploadScreenshot(
  projectId: string,
  file: File,
): Promise<{ screenshot_url: string }> {
  const token = getToken();
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE}/projects/${projectId}/screenshot`, {
    method: 'POST',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? 'Upload failed');
  }

  return res.json() as Promise<{ screenshot_url: string }>;
}

export async function deleteScreenshot(projectId: string): Promise<void> {
  await apiFetch(`/projects/${projectId}/screenshot`, { method: 'DELETE' });
}

/* ── Copilot endpoints ────────────────────────────────────────────────── */

export interface CopilotMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface CopilotContext {
  project_name: string;
  site_url: string;
  lens_name: string;
  lens_definition: string;
  sub_scores: Record<string, number>;
  current_observations: string;
}

export async function sendCopilotMessage(
  projectId: string,
  lensId: string,
  message: string,
  history: CopilotMessage[],
  context: CopilotContext,
): Promise<{ response: string }> {
  return apiFetch(`/projects/${projectId}/lens/${lensId}/copilot`, {
    method: 'POST',
    body: JSON.stringify({ message, history, context }),
  });
}

/* ── Sub-dimension endpoints ──────────────────────────────────────────── */

export async function updateSubDimension(
  projectId: string,
  lensId: string,
  subdimId: string,
  score: number,
  observation: string,
): Promise<void> {
  await apiFetch(`/projects/${projectId}/lens/${lensId}/subdimension/${subdimId}`, {
    method: 'PATCH',
    body: JSON.stringify({ score, observation }),
  });
}

/* ── Pipeline status endpoints ────────────────────────────────────────── */

export interface PipelineStatus {
  project_id: string;
  status: 'running' | 'complete' | 'error';
  current_step: string;
  progress: number;
  error_message: string | null;
  started_at: number | null;
  completed_at: number | null;
  step_times: Record<string, number>;
}

export async function getProjectStatus(projectId: string): Promise<PipelineStatus> {
  return apiFetch<PipelineStatus>(`/projects/${projectId}/status`);
}

export async function retryPipeline(projectId: string): Promise<PipelineStatus> {
  return apiFetch<PipelineStatus>(`/projects/${projectId}/retry`, { method: 'POST' });
}

export async function refreshProject(projectId: string): Promise<PipelineStatus> {
  return apiFetch<PipelineStatus>(`/projects/${projectId}/refresh`, { method: 'POST' });
}

/* ── PDF Export endpoints ─────────────────────────────────────────────── */

export interface ExportJobResponse {
  job_id: string;
  status: string;
}

export interface ExportStatusResponse {
  status: 'none' | 'pending' | 'generating' | 'complete' | 'error';
  download_url: string | null;
  error: string | null;
}

export async function startPdfExport(projectId: string): Promise<ExportJobResponse> {
  return apiFetch<ExportJobResponse>(`/projects/${projectId}/export/pdf`, {
    method: 'POST',
  });
}

export async function getExportStatus(projectId: string): Promise<ExportStatusResponse> {
  return apiFetch<ExportStatusResponse>(`/projects/${projectId}/export/status`);
}

/* ── Admin endpoints ──────────────────────────────────────────────────── */

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface InviteUserBody {
  email: string;
  name: string;
  role: string;
  password: string;
}

export interface UpdateUserBody {
  name?: string;
  role?: string;
  is_active?: boolean;
}

export async function fetchUsers(): Promise<AdminUser[]> {
  return apiFetch<AdminUser[]>('/admin/users');
}

export async function inviteUser(body: InviteUserBody): Promise<AdminUser> {
  return apiFetch<AdminUser>('/admin/users', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function updateUser(userId: string, body: UpdateUserBody): Promise<AdminUser> {
  return apiFetch<AdminUser>(`/admin/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}
