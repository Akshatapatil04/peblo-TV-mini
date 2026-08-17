import { Role, Show, Episode, Artwork, ValidationReport, PublishRun, PublishedCatalog, SearchResponse } from '../types';

const API_BASE = '/api/v1';

// Active role management (persisted in localStorage)
export function getActiveRole(): Role {
  const saved = localStorage.getItem('peblo_user_role');
  if (saved === 'admin' || saved === 'editor') {
    return saved;
  }
  return 'admin'; // default to admin for ease of testing
}

export function setActiveRole(role: Role) {
  localStorage.setItem('peblo_user_role', role);
  window.dispatchEvent(new CustomEvent('peblo-role-change', { detail: role }));
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const role = getActiveRole();
  const headers = new Headers(options.headers || {});

  headers.set('X-User-Role', role);

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    let errorData: any = {};
    try {
      errorData = await response.json();
    } catch {
      errorData = { message: await response.text() };
    }

    const message =
      errorData.detail?.message ||
      errorData.message ||
      (typeof errorData.detail === 'string' ? errorData.detail : 'Request failed');

    throw new ApiError(message, response.status, errorData);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  // Shows
  getShows: (params?: { section?: string; status?: string; category?: string; q?: string; page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.section) query.set('section', params.section);
    if (params?.status) query.set('status', params.status);
    if (params?.category) query.set('category', params.category);
    if (params?.q) query.set('q', params.q);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.page_size) query.set('page_size', params.page_size.toString());
    return request<{ total: number; items: Show[] }>(`/shows?${query.toString()}`);
  },

  getShow: (idOrSlug: string) => request<Show>(`/shows/${idOrSlug}`),
  createShow: (data: Partial<Show>) => request<Show>('/shows', { method: 'POST', body: JSON.stringify(data) }),
  updateShow: (id: string, data: Partial<Show>) => request<Show>(`/shows/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteShow: (id: string) => request<void>(`/shows/${id}`, { method: 'DELETE' }),

  // Episodes
  getEpisodes: (params?: { show_id?: string; season_number?: number; status?: string; language?: string; content_group?: string; section?: string; q?: string; page?: number; page_size?: number }) => {
    const query = new URLSearchParams();
    if (params?.show_id) query.set('show_id', params.show_id);
    if (params?.season_number !== undefined) query.set('season_number', params.season_number.toString());
    if (params?.status) query.set('status', params.status);
    if (params?.language) query.set('language', params.language);
    if (params?.content_group) query.set('content_group', params.content_group);
    if (params?.section) query.set('section', params.section);
    if (params?.q) query.set('q', params.q);
    if (params?.page) query.set('page', params.page.toString());
    if (params?.page_size) query.set('page_size', params.page_size.toString());
    return request<{ total: number; items: Episode[] }>(`/episodes?${query.toString()}`);
  },

  getEpisode: (id: string) => request<Episode>(`/episodes/${id}`),
  createEpisode: (data: Partial<Episode>) => request<Episode>('/episodes', { method: 'POST', body: JSON.stringify(data) }),
  updateEpisode: (id: string, data: Partial<Episode>) => request<Episode>(`/episodes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteEpisode: (id: string) => request<void>(`/episodes/${id}`, { method: 'DELETE' }),

  // Artwork
  uploadArtwork: async (file: File, slotType: 'poster' | 'banner' | 'thumbnail', showId?: string, episodeId?: string): Promise<Artwork> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('slot_type', slotType);
    if (showId) formData.append('show_id', showId);
    if (episodeId) formData.append('episode_id', episodeId);

    return request<Artwork>('/artwork/upload', {
      method: 'POST',
      body: formData
    });
  },
  deleteArtwork: (id: string) => request<void>(`/artwork/${id}`, { method: 'DELETE' }),

  // Validation & Publishing
  getValidationReport: () => request<ValidationReport>('/admin/validation-report'),
  publishCatalog: (force: boolean = false) => request<{ run_id: string; version: string; status: string; shows_count: number; episodes_count: number; sections_count: number; catalogue_url: string; published_at: string }>('/admin/catalog/publish', {
    method: 'POST',
    body: JSON.stringify({ force })
  }),
  getPublishRuns: (page: number = 1, pageSize: number = 20) => request<{ total: number; items: PublishRun[] }>(`/admin/publish-runs?page=${page}&page_size=${pageSize}`),
  getPublishRun: (id: string) => request<any>(`/admin/publish-runs/${id}`),
  rollbackPublish: (runId: string) => request<any>(`/admin/publish-runs/${runId}/rollback`, { method: 'POST' }),

  // Viewer Catalog & Search
  getCatalog: () => request<PublishedCatalog>('/catalog'),
  searchCatalog: (params: { q?: string; category?: string; language?: string; section?: string }) => {
    const query = new URLSearchParams();
    if (params.q) query.set('q', params.q);
    if (params.category) query.set('category', params.category);
    if (params.language) query.set('language', params.language);
    if (params.section) query.set('section', params.section);
    return request<SearchResponse>(`/catalog/search?${query.toString()}`);
  }
};
