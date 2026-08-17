import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Play, Info, Search, Filter,
  Tv, Film, RefreshCw, AlertCircle
} from 'lucide-react';
import { api } from '../api/client';
import { PublishedCatalog, PublishedShow, CollapsedEpisode, SearchResponse } from '../types';
import { ShowDetailModal } from './ShowDetailModal';
import { TrailerPlayerModal } from './TrailerPlayerModal';

const CATEGORIES = [
  'adventure', 'folk', 'friendship', 'india', 'language',
  'learning', 'maths', 'music', 'nature', 'reading',
  'science', 'singalong', 'stories', 'travel', 'values'
];

export const ViewerHome: React.FC = () => {
  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');

  // Active Modals
  const [selectedShow, setSelectedShow] = useState<PublishedShow | null>(null);
  const [isShowDetailOpen, setIsShowDetailOpen] = useState(false);
  const [activePlayEpisode, setActivePlayEpisode] = useState<CollapsedEpisode | null>(null);
  const [activePlayLanguage, setActivePlayLanguage] = useState<string>('en');
  const [isPlayerOpen, setIsPlayerOpen] = useState(false);

  // 1. Fetch Published Catalogue (Main Feed)
  const {
    data: catalog,
    isLoading: isLoadingCatalog,
    isError: isCatalogError,
    refetch: refetchCatalog
  } = useQuery<PublishedCatalog>({
    queryKey: ['catalog'],
    queryFn: () => api.getCatalog(),
    staleTime: 60000
  });

  // 2. Fetch Search Query if active
  const isSearchActive = Boolean(searchQuery || selectedCategory !== 'all' || selectedLanguage !== 'all');

  const {
    data: searchResults,
    isLoading: isSearching
  } = useQuery<SearchResponse>({
    queryKey: ['catalog-search', searchQuery, selectedCategory, selectedLanguage],
    queryFn: () =>
      api.searchCatalog({
        q: searchQuery || undefined,
        category: selectedCategory === 'all' ? undefined : selectedCategory,
        language: selectedLanguage === 'all' ? undefined : selectedLanguage
      }),
    enabled: isSearchActive
  });

  // Pick Hero Show (from Featured section or first available show)
  const heroShow = useMemo(() => {
    if (!catalog?.sections) return null;
    const featuredSection = catalog.sections.find((s) => s.section_id === 'featured');
    if (featuredSection && featuredSection.shows.length > 0) {
      return featuredSection.shows[0];
    }
    for (const sec of catalog.sections) {
      if (sec.shows.length > 0) return sec.shows[0];
    }
    return null;
  }, [catalog]);

  const handleOpenShow = (show: PublishedShow) => {
    setSelectedShow(show);
    setIsShowDetailOpen(true);
  };

  const handlePlayEpisode = (episode: CollapsedEpisode, language: string = 'en') => {
    setActivePlayEpisode(episode);
    setActivePlayLanguage(language);
    setIsPlayerOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#0f1015] text-slate-100 pb-20">
      {/* Search & Filter Header Bar */}
      <div className="sticky top-16 z-40 w-full backdrop-blur-md bg-slate-950/80 border-b border-white/5 py-3 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search shows, episodes, songs, or topics..."
              className="w-full pl-10 pr-4 py-2 bg-slate-900/90 border border-slate-800 rounded-full text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/20 transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          {/* Composable Filters */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 sm:pb-0 text-xs">
            <div className="flex items-center gap-1 text-slate-400 font-semibold text-[11px] shrink-0">
              <Filter className="w-3.5 h-3.5 text-red-500" />
              Filter:
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 outline-none capitalize shrink-0"
            >
              <option value="all">All Categories</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>

            {/* Language Filter */}
            <select
              value={selectedLanguage}
              onChange={(e) => setSelectedLanguage(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 outline-none shrink-0"
            >
              <option value="all">All Languages</option>
              <option value="en">English Audio</option>
              <option value="hi">Hindi Audio (हिंदी)</option>
            </select>

            {isSearchActive && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('all');
                  setSelectedLanguage('all');
                }}
                className="text-[11px] text-red-400 hover:text-red-300 font-semibold px-2 py-1 shrink-0"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      {isSearchActive ? (
        /* SEARCH & FILTER RESULTS VIEW */
        <div className="max-w-7xl mx-auto px-4 sm:px-8 py-8 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Search className="w-5 h-5 text-red-500" />
              Search & Filter Results
            </h2>
            <span className="text-xs text-slate-400">
              {searchResults?.total_matches || 0} match{searchResults?.total_matches === 1 ? '' : 'es'} found
            </span>
          </div>

          {isSearching ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="aspect-[2/3] bg-slate-900 rounded-xl animate-pulse" />
              ))}
            </div>
          ) : searchResults?.results.length === 0 ? (
            /* Rich Empty State */
            <div className="text-center py-16 bg-slate-900/40 border border-slate-800/80 rounded-3xl p-8 space-y-4 max-w-lg mx-auto">
              <div className="w-14 h-14 rounded-full bg-slate-800/80 text-slate-400 flex items-center justify-center mx-auto">
                <Film className="w-7 h-7 opacity-50" />
              </div>
              <h3 className="text-lg font-bold text-white">No results found</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                We couldn't find any published shows or episodes matching your query and filter criteria.
              </p>
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategory('all');
                  setSelectedLanguage('all');
                }}
                className="btn btn-primary text-xs mx-auto"
              >
                Clear All Filters
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 sm:gap-6">
              {searchResults?.results.map((res) => {
                const poster = res.artwork?.poster || res.artwork?.banner || res.artwork?.thumbnail;
                return (
                  <div
                    key={res.id}
                    onClick={() => {
                      // Match with published catalogue show or construct
                      const foundShow = catalog?.sections
                        .flatMap((s) => s.shows)
                        .find((s) => s.id === res.id);
                      if (foundShow) {
                        handleOpenShow(foundShow);
                      }
                    }}
                    className="group cursor-pointer bg-slate-900 border border-slate-800 hover:border-red-500/60 rounded-xl overflow-hidden shadow-lg transition-all duration-300 hover:scale-[1.03] hover:shadow-red-500/10 flex flex-col"
                  >
                    <div className="relative aspect-[2/3] bg-slate-950 overflow-hidden">
                      {poster ? (
                        <img
                          src={poster}
                          alt={res.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                          loading="lazy"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-slate-900 text-slate-600">
                          <Film className="w-8 h-8 opacity-30" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-3">
                        <span className="text-xs font-bold text-white flex items-center gap-1">
                          <Play className="w-3 h-3 fill-current text-red-500" /> Watch Now
                        </span>
                      </div>
                    </div>

                    <div className="p-3 flex-1 flex flex-col justify-between">
                      <div>
                        <h4 className="text-xs sm:text-sm font-bold text-white group-hover:text-red-400 transition-colors line-clamp-1">
                          {res.title}
                        </h4>
                        <p className="text-[11px] text-slate-400 line-clamp-2 mt-0.5">
                          {res.synopsis}
                        </p>
                      </div>

                      {res.matching_episodes && res.matching_episodes.length > 0 && (
                        <span className="text-[10px] text-blue-400 mt-2 font-medium">
                          {res.matching_episodes.length} matching episode{res.matching_episodes.length === 1 ? '' : 's'}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* NETFLIX-STYLE HOMEPAGE */
        <>
          {/* FEATURED HERO BANNER */}
          {heroShow ? (
            <div className="relative w-full h-[65vh] min-h-[440px] max-h-[620px] bg-slate-950 overflow-hidden">
              {/* Backdrop Banner Image */}
              {heroShow.artwork?.banner || heroShow.artwork?.poster ? (
                <img
                  src={heroShow.artwork.banner || heroShow.artwork.poster}
                  alt={heroShow.title}
                  className="w-full h-full object-cover object-top opacity-70"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-r from-slate-950 to-slate-900" />
              )}

              {/* Cinematic Vignette Gradients */}
              <div className="absolute inset-0 bg-gradient-to-r from-[#0f1015] via-[#0f1015]/70 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-t from-[#0f1015] via-transparent to-black/30" />

              {/* Hero Content Overlay */}
              <div className="absolute inset-0 max-w-7xl mx-auto px-4 sm:px-8 flex flex-col justify-center space-y-4">
                <div className="max-w-2xl space-y-4 animate-fade-in">
                  {/* Section Badge & Category Tags */}
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="badge bg-red-600 text-white font-extrabold text-xs px-3 py-1 shadow-lg shadow-red-600/30 uppercase tracking-wider">
                      Featured • {heroShow.section}
                    </span>
                    {heroShow.categories?.slice(0, 3).map((cat) => (
                      <span
                        key={cat}
                        className="badge bg-white/10 backdrop-blur-md text-slate-200 text-xs px-2.5 py-0.5 capitalize border border-white/15"
                      >
                        {cat}
                      </span>
                    ))}
                  </div>

                  {/* Title */}
                  <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-white tracking-tight drop-shadow-lg font-display">
                    {heroShow.title}
                  </h1>

                  {/* Synopsis */}
                  <p className="text-xs sm:text-sm lg:text-base text-slate-200 line-clamp-3 leading-relaxed drop-shadow max-w-xl">
                    {heroShow.synopsis || 'An exciting adventure for little learners with songs, stories, and multilingual joy.'}
                  </p>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-3 pt-2">
                    {heroShow.trailers && heroShow.trailers.length > 0 ? (
                      <button
                        onClick={() => handlePlayEpisode(heroShow.trailers[0])}
                        className="btn btn-primary bg-white hover:bg-slate-200 text-slate-950 font-bold px-6 py-2.5 rounded-xl shadow-xl hover:scale-105 transition-all text-sm"
                      >
                        <Play className="w-4 h-4 fill-current" />
                        Watch Trailer
                      </button>
                    ) : (
                      <button
                        onClick={() => handleOpenShow(heroShow)}
                        className="btn btn-primary bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-2.5 rounded-xl shadow-xl shadow-red-600/30 hover:scale-105 transition-all text-sm"
                      >
                        <Play className="w-4 h-4 fill-current" />
                        Explore Episodes
                      </button>
                    )}

                    <button
                      onClick={() => handleOpenShow(heroShow)}
                      className="btn btn-outline border-white/30 hover:bg-white/10 text-white font-semibold px-5 py-2.5 rounded-xl text-sm"
                    >
                      <Info className="w-4 h-4" />
                      More Info
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : isLoadingCatalog ? (
            <div className="w-full h-[55vh] bg-slate-900 animate-pulse" />
          ) : null}

          {/* SECTION ROWS (Featured, Series, Minisodes, Songs) */}
          <div className="max-w-7xl mx-auto px-4 sm:px-8 -mt-8 relative z-20 space-y-10">
            {isLoadingCatalog ? (
              <div className="space-y-8">
                {[1, 2, 3].map((row) => (
                  <div key={row} className="space-y-3">
                    <div className="w-40 h-6 bg-slate-800 rounded animate-pulse" />
                    <div className="flex gap-4 overflow-hidden">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="w-48 aspect-[2/3] bg-slate-900 rounded-xl shrink-0 animate-pulse" />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : isCatalogError ? (
              <div className="p-8 text-center bg-red-500/10 border border-red-500/30 rounded-2xl">
                <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
                <p className="text-red-200 font-semibold">Failed to load published catalogue.</p>
                <button onClick={() => refetchCatalog()} className="btn btn-secondary mt-3">
                  <RefreshCw className="w-4 h-4" /> Retry
                </button>
              </div>
            ) : catalog?.sections.length === 0 ? (
              <div className="p-12 text-center bg-slate-900/60 border border-slate-800 rounded-2xl space-y-3">
                <Tv className="w-12 h-12 text-slate-500 mx-auto" />
                <h3 className="text-lg font-bold text-white">No published shows yet</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  The content catalogue has not been published yet. Head over to the CMS Console to review validation and publish the seed shows!
                </p>
                <a href="/cms/publish" className="btn btn-primary text-xs mx-auto inline-flex">
                  Go to CMS Publish Dashboard
                </a>
              </div>
            ) : (
              catalog?.sections.map((section) => {
                if (section.shows.length === 0) return null;

                return (
                  <div key={section.section_id} className="space-y-3">
                    {/* Section Header */}
                    <div className="flex items-center justify-between">
                      <h2 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
                        <span>{section.title}</span>
                        <span className="text-xs text-slate-500 font-normal">({section.shows.length})</span>
                      </h2>
                    </div>

                    {/* Horizontal Scrolling Row (Poster Artwork) */}
                    <div className="carousel-row">
                      {section.shows.map((show) => {
                        const poster = show.artwork?.poster || show.artwork?.banner || show.artwork?.thumbnail;
                        return (
                          <div
                            key={show.id}
                            onClick={() => handleOpenShow(show)}
                            className="group relative w-36 sm:w-44 md:w-48 aspect-[2/3] shrink-0 rounded-xl overflow-hidden bg-slate-900 border border-white/5 hover:border-red-500/60 shadow-lg cursor-pointer transition-all duration-300 hover:scale-105 hover:z-30 hover:shadow-2xl hover:shadow-red-500/10"
                          >
                            {poster ? (
                              <img
                                src={poster}
                                alt={show.title}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                loading="lazy"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center bg-slate-900 text-slate-600">
                                <Film className="w-8 h-8 opacity-30" />
                              </div>
                            )}

                            {/* Hover Card Details */}
                            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 p-3 flex flex-col justify-end">
                              <h4 className="text-xs sm:text-sm font-bold text-white line-clamp-1 drop-shadow">
                                {show.title}
                              </h4>
                              <div className="flex items-center gap-1.5 mt-1">
                                <span className="text-[10px] text-red-400 font-semibold flex items-center gap-0.5">
                                  <Play className="w-2.5 h-2.5 fill-current" /> Watch
                                </span>
                                {show.categories?.[0] && (
                                  <span className="text-[10px] text-slate-300 capitalize">
                                    • {show.categories[0]}
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </>
      )}

      {/* Show Detail Modal */}
      <ShowDetailModal
        show={selectedShow}
        isOpen={isShowDetailOpen}
        onClose={() => setIsShowDetailOpen(false)}
        onPlayEpisode={handlePlayEpisode}
      />

      {/* Media Player Modal */}
      <TrailerPlayerModal
        episode={activePlayEpisode}
        initialLanguage={activePlayLanguage}
        isOpen={isPlayerOpen}
        onClose={() => setIsPlayerOpen(false)}
      />
    </div>
  );
};
