import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Search, Filter, Film, Tv, Edit3, Trash2, CheckCircle2,
  AlertCircle, Layers, RefreshCw, FolderOpen
} from 'lucide-react';
import { api } from '../api/client';
import { Show, Episode } from '../types';
import { ShowModal } from './ShowModal';
import { EpisodeModal } from './EpisodeModal';

export const ShowsPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Active view: 'shows' or 'episodes'
  const [activeTab, setActiveTab] = useState<'shows' | 'episodes'>('shows');

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSection, setSelectedSection] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [page, setPage] = useState(1);
  const pageSize = 25;

  // Modals state
  const [isShowModalOpen, setIsShowModalOpen] = useState(false);
  const [isEpisodeModalOpen, setIsEpisodeModalOpen] = useState(false);
  const [editingShow, setEditingShow] = useState<Show | null>(null);
  const [editingEpisode, setEditingEpisode] = useState<Episode | null>(null);
  const [targetShowIdForEpisode, setTargetShowIdForEpisode] = useState<string | undefined>();

  // Fetch Shows
  const {
    data: showsData,
    isLoading: isLoadingShows,
    isError: isShowsError,
    refetch: refetchShows
  } = useQuery({
    queryKey: ['shows', selectedSection, selectedStatus, selectedCategory, searchQuery, page],
    queryFn: () =>
      api.getShows({
        section: selectedSection === 'all' ? undefined : selectedSection,
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        q: searchQuery || undefined,
        page,
        page_size: pageSize
      })
  });

  // Fetch Episodes
  const {
    data: episodesData,
    isLoading: isLoadingEpisodes,
    isError: isEpisodesError,
    refetch: refetchEpisodes
  } = useQuery({
    queryKey: ['episodes', selectedSection, selectedStatus, selectedLanguage, searchQuery, page],
    queryFn: () =>
      api.getEpisodes({
        section: selectedSection === 'all' ? undefined : selectedSection,
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        language: selectedLanguage === 'all' ? undefined : selectedLanguage,
        q: searchQuery || undefined,
        page,
        page_size: pageSize
      })
  });

  // Delete Mutations
  const deleteShowMutation = useMutation({
    mutationFn: (id: string) => api.deleteShow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shows'] });
      queryClient.invalidateQueries({ queryKey: ['validation-report'] });
    }
  });

  const deleteEpisodeMutation = useMutation({
    mutationFn: (id: string) => api.deleteEpisode(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['episodes'] });
      queryClient.invalidateQueries({ queryKey: ['shows'] });
      queryClient.invalidateQueries({ queryKey: ['validation-report'] });
    }
  });

  const allShows = showsData?.items || [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 lg:p-10">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <h1 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <Film className="w-7 h-7 text-blue-500" />
              Content Management System
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Manage video titles, language variants, artwork assets, and publishing metadata.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setEditingShow(null);
                setIsShowModalOpen(true);
              }}
              className="btn btn-primary bg-blue-600 hover:bg-blue-500 shadow-blue-600/30"
            >
              <Plus className="w-4 h-4" />
              New Show
            </button>
            <button
              onClick={() => {
                setEditingEpisode(null);
                setTargetShowIdForEpisode(undefined);
                setIsEpisodeModalOpen(true);
              }}
              className="btn btn-secondary border-slate-700 hover:border-slate-600"
            >
              <Plus className="w-4 h-4" />
              New Episode
            </button>
          </div>
        </div>

        {/* Tab & Filter Bar */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 space-y-4 shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* View Selector */}
            <div className="flex items-center gap-1 p-1 bg-slate-950 rounded-xl border border-slate-800 w-fit">
              <button
                onClick={() => { setActiveTab('shows'); setPage(1); }}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === 'shows'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Tv className="w-4 h-4" />
                Shows ({showsData?.total || 0})
              </button>
              <button
                onClick={() => { setActiveTab('episodes'); setPage(1); }}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2 ${
                  activeTab === 'episodes'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Layers className="w-4 h-4" />
                Episodes ({episodesData?.total || 0})
              </button>
            </div>

            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
                placeholder={activeTab === 'shows' ? 'Search show title, slug, synopsis...' : 'Search episode title, content group, code...'}
                className="input-field pl-10 text-xs"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-slate-200"
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-800/60 text-xs">
            <div className="flex items-center gap-1.5 text-slate-400 font-semibold">
              <Filter className="w-3.5 h-3.5 text-blue-400" />
              Filters:
            </div>

            {/* Section Filter */}
            <select
              value={selectedSection}
              onChange={(e) => { setSelectedSection(e.target.value); setPage(1); }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 outline-none text-xs"
            >
              <option value="all">All Sections</option>
              <option value="featured">Featured</option>
              <option value="series">Series</option>
              <option value="minisodes">Minisodes</option>
              <option value="songs">Songs</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 outline-none text-xs"
            >
              <option value="all">All Statuses</option>
              <option value="published">Published</option>
              <option value="draft">Draft</option>
            </select>

            {/* Language Filter (for Episodes) */}
            {activeTab === 'episodes' && (
              <select
                value={selectedLanguage}
                onChange={(e) => { setSelectedLanguage(e.target.value); setPage(1); }}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 outline-none text-xs"
              >
                <option value="all">All Languages</option>
                <option value="en">English (en)</option>
                <option value="hi">Hindi (hi)</option>
              </select>
            )}

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => { setSelectedCategory(e.target.value); setPage(1); }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-slate-200 outline-none text-xs"
            >
              <option value="all">All Categories</option>
              <option value="adventure">Adventure</option>
              <option value="india">India</option>
              <option value="friendship">Friendship</option>
              <option value="folk">Folk</option>
              <option value="learning">Learning</option>
              <option value="maths">Maths</option>
              <option value="music">Music</option>
              <option value="nature">Nature</option>
              <option value="science">Science</option>
              <option value="singalong">Singalong</option>
              <option value="stories">Stories</option>
              <option value="travel">Travel</option>
              <option value="values">Values</option>
            </select>

            {(selectedSection !== 'all' || selectedStatus !== 'all' || selectedLanguage !== 'all' || selectedCategory !== 'all' || searchQuery) && (
              <button
                onClick={() => {
                  setSelectedSection('all');
                  setSelectedStatus('all');
                  setSelectedLanguage('all');
                  setSelectedCategory('all');
                  setSearchQuery('');
                  setPage(1);
                }}
                className="text-[11px] text-blue-400 hover:text-blue-300 font-semibold px-2 py-1"
              >
                Reset Filters
              </button>
            )}
          </div>
        </div>

        {/* Content Area */}
        {activeTab === 'shows' ? (
          /* SHOWS LIST */
          isLoadingShows ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-64 rounded-2xl bg-slate-900 border border-slate-800 animate-pulse p-4" />
              ))}
            </div>
          ) : isShowsError ? (
            <div className="p-8 text-center bg-red-500/10 border border-red-500/30 rounded-2xl">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-red-200 font-semibold">Failed to load shows from API.</p>
              <button onClick={() => refetchShows()} className="btn btn-secondary mt-3">
                <RefreshCw className="w-4 h-4" /> Retry
              </button>
            </div>
          ) : allShows.length === 0 ? (
            <div className="p-12 text-center bg-slate-900/60 border border-slate-800 rounded-2xl space-y-3">
              <FolderOpen className="w-10 h-10 text-slate-500 mx-auto" />
              <h3 className="text-lg font-bold text-slate-200">No shows found</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto">
                No shows match your current search or filter criteria. Try adjusting filters or create a new show.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {allShows.map((show) => {
                const poster = show.artworks?.find((a) => a.slot_type === 'poster')?.url;
                const banner = show.artworks?.find((a) => a.slot_type === 'banner')?.url;

                return (
                  <div
                    key={show.id}
                    className="bg-slate-900 border border-slate-800 hover:border-slate-700 rounded-2xl overflow-hidden shadow-lg transition-all flex flex-col group"
                  >
                    {/* Card Banner Preview */}
                    <div className="relative h-36 bg-slate-950 overflow-hidden">
                      {banner || poster ? (
                        <img
                          src={banner || poster}
                          alt={show.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-slate-950 text-slate-600">
                          <Film className="w-8 h-8 opacity-40" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-black/40" />

                      {/* Status Badges */}
                      <div className="absolute top-3 left-3 flex items-center gap-2">
                        <span
                          className={`badge ${
                            show.status === 'published' ? 'badge-published' : 'badge-draft'
                          }`}
                        >
                          {show.status}
                        </span>
                        {show.section && (
                          <span className="badge bg-blue-500/20 text-blue-400 border border-blue-500/30">
                            {show.section}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Content Details */}
                    <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                      <div>
                        <h3 className="text-base font-bold text-white group-hover:text-blue-400 transition-colors">
                          {show.title}
                        </h3>
                        <p className="text-xs text-slate-400 line-clamp-2 mt-1">
                          {show.synopsis || 'No synopsis provided.'}
                        </p>

                        {/* Categories */}
                        {show.categories && show.categories.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-3">
                            {show.categories.slice(0, 3).map((cat) => (
                              <span key={cat} className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded capitalize">
                                {cat}
                              </span>
                            ))}
                            {show.categories.length > 3 && (
                              <span className="text-[10px] text-slate-500 self-center">
                                +{show.categories.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Stats & Actions */}
                      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                        <div className="text-xs text-slate-400 flex items-center gap-3">
                          <span>
                            <strong>{show.episodes_count || 0}</strong> eps
                          </span>
                          <span>
                            <strong>{show.seasons_count || 0}</strong> seasons
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => {
                              setTargetShowIdForEpisode(show.id);
                              setEditingEpisode(null);
                              setIsEpisodeModalOpen(true);
                            }}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                            title="Add Episode"
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              setEditingShow(show);
                              setIsShowModalOpen(true);
                            }}
                            className="p-1.5 rounded-lg text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 transition-colors"
                            title="Edit Show"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              if (confirm(`Are you sure you want to delete show '${show.title}'?`)) {
                                deleteShowMutation.mutate(show.id);
                              }
                            }}
                            className="p-1.5 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                            title="Delete Show"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )
        ) : (
          /* EPISODES TABLE */
          isLoadingEpisodes ? (
            <div className="h-64 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse" />
          ) : isEpisodesError ? (
            <div className="p-8 text-center bg-red-500/10 border border-red-500/30 rounded-2xl">
              <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
              <p className="text-red-200 font-semibold">Failed to load episodes.</p>
              <button onClick={() => refetchEpisodes()} className="btn btn-secondary mt-3">
                <RefreshCw className="w-4 h-4" /> Retry
              </button>
            </div>
          ) : (episodesData?.items || []).length === 0 ? (
            <div className="p-12 text-center bg-slate-900/60 border border-slate-800 rounded-2xl">
              <FolderOpen className="w-10 h-10 text-slate-500 mx-auto mb-2" />
              <h3 className="text-lg font-bold text-slate-200">No episodes found</h3>
              <p className="text-xs text-slate-400">Try adjusting your filters or add a new episode.</p>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                    <tr>
                      <th className="py-3.5 px-4">Show & Code</th>
                      <th className="py-3.5 px-4">Episode Title</th>
                      <th className="py-3.5 px-4">Content Group</th>
                      <th className="py-3.5 px-4">Lang</th>
                      <th className="py-3.5 px-4">Duration</th>
                      <th className="py-3.5 px-4">Artwork</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {episodesData?.items.map((ep) => {
                      const hasThumb = ep.artworks && ep.artworks.length > 0;
                      return (
                        <tr key={ep.id} className="hover:bg-slate-800/40 transition-colors">
                          <td className="py-3 px-4">
                            <span className="font-bold text-white block">{ep.show_title || 'Unknown Show'}</span>
                            <span className="text-[11px] text-slate-400 font-mono">
                              S{ep.season_number.toString().padStart(2, '0')}E{ep.episode_number.toString().padStart(2, '0')} {ep.episode_id && `(${ep.episode_id})`}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-medium text-slate-200">{ep.episode_title}</span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="font-mono text-[11px] text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                              {ep.content_group}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className="badge badge-lang uppercase">{ep.language}</span>
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {Math.floor(ep.duration_seconds / 60)}m {ep.duration_seconds % 60}s
                          </td>
                          <td className="py-3 px-4">
                            {hasThumb ? (
                              <span className="inline-flex items-center gap-1 text-emerald-400 text-[11px]">
                                <CheckCircle2 className="w-3.5 h-3.5" /> 16:9
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-red-400 text-[11px]">
                                <AlertCircle className="w-3.5 h-3.5" /> Missing
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`badge ${ep.status === 'published' ? 'badge-published' : 'badge-draft'}`}>
                              {ep.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <button
                                onClick={() => {
                                  setEditingEpisode(ep);
                                  setIsEpisodeModalOpen(true);
                                }}
                                className="p-1 rounded text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 transition-colors"
                                title="Edit Episode"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => {
                                  if (confirm(`Delete episode '${ep.episode_title}'?`)) {
                                    deleteEpisodeMutation.mutate(ep.id);
                                  }
                                }}
                                className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                                title="Delete Episode"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )
        )}
      </div>

      {/* Show Modal */}
      <ShowModal
        isOpen={isShowModalOpen}
        onClose={() => setIsShowModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['shows'] });
          queryClient.invalidateQueries({ queryKey: ['validation-report'] });
        }}
        show={editingShow}
      />

      {/* Episode Modal */}
      <EpisodeModal
        isOpen={isEpisodeModalOpen}
        onClose={() => setIsEpisodeModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['episodes'] });
          queryClient.invalidateQueries({ queryKey: ['shows'] });
          queryClient.invalidateQueries({ queryKey: ['validation-report'] });
        }}
        shows={allShows}
        initialShowId={targetShowIdForEpisode}
        episode={editingEpisode}
      />
    </div>
  );
};
