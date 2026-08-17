export type Role = 'admin' | 'editor';

export interface Artwork {
  id: string;
  slot_type: 'poster' | 'banner' | 'thumbnail';
  url: string;
  width: number;
  height: number;
  file_size_bytes: number;
  file_size_kb?: number;
  mime_type?: string;
  aspect_ratio?: string;
  show_id?: string;
  episode_id?: string;
}

export interface Episode {
  id: string;
  episode_id?: string;
  show_id: string;
  season_id?: string;
  season_number: number;
  episode_number: number;
  episode_title: string;
  duration_seconds: number;
  language: string;
  content_group: string;
  status: 'draft' | 'published';
  synopsis?: string;
  created_at?: string;
  updated_at?: string;
  artworks: Artwork[];
  show_title?: string;
  show_slug?: string;
}

export interface Season {
  id: string;
  show_id: string;
  season_number: number;
  title?: string;
  episodes: Episode[];
}

export interface Show {
  id: string;
  slug: string;
  title: string;
  synopsis?: string;
  section?: 'featured' | 'series' | 'minisodes' | 'songs' | string;
  categories: string[];
  status: 'draft' | 'published';
  created_at: string;
  updated_at: string;
  artworks: Artwork[];
  seasons_count?: number;
  episodes_count?: number;
  seasons?: Season[];
}

export interface ValidationErrorItem {
  entity_type: 'show' | 'episode';
  entity_id: string;
  db_id?: string;
  show_id?: string;
  show_slug?: string;
  show_title?: string;
  title: string;
  field: string;
  severity: 'blocking' | 'warning' | 'info';
  message: string;
  remediation: string;
}

export interface ShowValidationSummary {
  show_id: string;
  show_slug: string;
  show_title: string;
  status: string;
  section?: string;
  blocking_count: number;
  warning_count: number;
  errors: ValidationErrorItem[];
  warnings: ValidationErrorItem[];
}

export interface ValidationReport {
  can_publish: boolean;
  total_shows: number;
  total_blocking_errors: number;
  total_warnings: number;
  blocking_errors: ValidationErrorItem[];
  warnings: ValidationErrorItem[];
  grouped_by_show: Record<string, ShowValidationSummary>;
}

export interface PublishRun {
  id: string;
  initiated_by: string;
  started_at: string;
  completed_at?: string;
  status: 'running' | 'success' | 'failed';
  shows_count: number;
  episodes_count: number;
  sections_count: number;
  catalogue_path?: string;
  catalogue_version?: string;
  error_message?: string;
  created_at: string;
}

export interface CollapsedEpisode {
  content_group: string;
  episode_number: number;
  title: string;
  synopsis?: string;
  duration_seconds: number;
  languages: string[];
  audio_variants: Array<{
    language: string;
    episode_id: string;
    duration_seconds: number;
    title: string;
    synopsis?: string;
  }>;
  artwork: {
    poster?: string;
    banner?: string;
    thumbnail?: string;
  };
}

export interface PublishedSeason {
  season_number: number;
  title: string;
  episodes_count: number;
  episodes: CollapsedEpisode[];
}

export interface PublishedShow {
  id: string;
  slug: string;
  title: string;
  synopsis?: string;
  section: string;
  categories: string[];
  artwork: {
    poster?: string;
    banner?: string;
    thumbnail?: string;
  };
  trailers: CollapsedEpisode[];
  seasons: PublishedSeason[];
  total_seasons: number;
}

export interface PublishedSection {
  section_id: string;
  title: string;
  shows_count: number;
  shows: PublishedShow[];
}

export interface PublishedCatalog {
  schema_version: string;
  catalogue_version: string;
  generated_at?: string;
  summary: {
    total_sections: number;
    total_shows: number;
    total_episodes: number;
  };
  sections: PublishedSection[];
  message?: string;
}

export interface SearchShowResult {
  id: string;
  slug: string;
  title: string;
  synopsis?: string;
  section?: string;
  categories: string[];
  artwork: Record<string, string>;
  matching_episodes: Array<{
    id: string;
    episode_id?: string;
    season_number: number;
    episode_number: number;
    title: string;
    duration_seconds: number;
    language: string;
    content_group: string;
    synopsis?: string;
    artwork: {
      thumbnail?: string;
    };
  }>;
}

export interface SearchResponse {
  total_matches: number;
  query?: string;
  filters: {
    category?: string;
    language?: string;
    section?: string;
  };
  results: SearchShowResult[];
}
