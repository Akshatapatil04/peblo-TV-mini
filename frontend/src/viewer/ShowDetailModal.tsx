import React, { useState } from 'react';
import { X, Play, Clock, Sparkles, Film, Globe } from 'lucide-react';
import { PublishedShow, CollapsedEpisode } from '../types';

interface ShowDetailModalProps {
  show: PublishedShow | null;
  isOpen: boolean;
  onClose: () => void;
  onPlayEpisode: (episode: CollapsedEpisode, language?: string) => void;
}

export const ShowDetailModal: React.FC<ShowDetailModalProps> = ({
  show,
  isOpen,
  onClose,
  onPlayEpisode
}) => {
  const [selectedSeasonNumber, setSelectedSeasonNumber] = useState<number>(1);
  const [selectedLanguages, setSelectedLanguages] = useState<Record<string, string>>({});

  if (!isOpen || !show) return null;

  const banner = show.artwork?.banner || show.artwork?.poster;
  const seasons = show.seasons || [];
  const trailers = show.trailers || [];
  const activeSeason = seasons.find((s) => s.season_number === selectedSeasonNumber) || seasons[0];

  const handleLanguageSelect = (contentGroup: string, lang: string) => {
    setSelectedLanguages((prev) => ({ ...prev, [contentGroup]: lang }));
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 md:p-6 bg-black/85 backdrop-blur-md overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-auto animate-fade-in text-slate-100">
        {/* Hero Backdrop in Modal */}
        <div className="relative h-64 sm:h-80 md:h-96 w-full bg-slate-950 overflow-hidden">
          {banner ? (
            <img
              src={banner}
              alt={show.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-slate-900 text-slate-600">
              <Film className="w-16 h-16 opacity-30" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/60 to-black/30" />

          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-20 w-9 h-9 rounded-full bg-black/60 hover:bg-black/90 text-white flex items-center justify-center border border-white/20 transition-all hover:scale-105"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Hero Content Overlay */}
          <div className="absolute bottom-6 left-6 right-6 space-y-3 z-10">
            <div className="flex flex-wrap items-center gap-2">
              <span className="badge bg-red-600/90 text-white text-xs px-2.5 py-0.5 font-bold uppercase tracking-wider">
                {show.section || 'Peblo Original'}
              </span>
              {show.categories?.map((cat) => (
                <span key={cat} className="badge bg-slate-800/90 text-slate-200 text-xs capitalize border border-slate-700">
                  {cat}
                </span>
              ))}
            </div>

            <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight drop-shadow-md">
              {show.title}
            </h2>

            <p className="text-xs sm:text-sm text-slate-300 max-w-2xl line-clamp-2 sm:line-clamp-3 leading-relaxed drop-shadow">
              {show.synopsis || 'Explore episodes and singalongs in English and Hindi.'}
            </p>

            {/* Quick Action Buttons */}
            {trailers.length > 0 && (
              <div className="pt-2 flex items-center gap-3">
                <button
                  onClick={() => onPlayEpisode(trailers[0])}
                  className="btn btn-primary bg-white hover:bg-slate-200 text-slate-950 font-bold px-5 py-2 rounded-xl flex items-center gap-2 shadow-lg hover:scale-105 transition-all"
                >
                  <Play className="w-4 h-4 fill-current" />
                  Watch Trailer
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Modal Body: Trailers & Seasons */}
        <div className="p-6 space-y-8 max-h-[60vh] overflow-y-auto">
          {/* Season 0 Trailers (Separated from regular seasons!) */}
          {trailers.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Trailers & Teasers</h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {trailers.map((trailer) => {
                  const thumb = trailer.artwork?.thumbnail || show.artwork?.thumbnail || banner;
                  return (
                    <div
                      key={trailer.content_group}
                      onClick={() => onPlayEpisode(trailer)}
                      className="group cursor-pointer bg-slate-950/60 border border-slate-800 hover:border-slate-700 rounded-xl overflow-hidden p-3 flex gap-3 transition-all hover:bg-slate-800/40"
                    >
                      <div className="relative w-32 h-20 bg-slate-900 rounded-lg overflow-hidden shrink-0">
                        {thumb && <img src={thumb} alt={trailer.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />}
                        <div className="absolute inset-0 bg-black/40 flex items-center justify-center group-hover:bg-black/20 transition-colors">
                          <div className="w-8 h-8 rounded-full bg-red-600/90 text-white flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                            <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                          </div>
                        </div>
                      </div>
                      <div className="flex-1 flex flex-col justify-center">
                        <h4 className="text-sm font-bold text-white group-hover:text-red-400 transition-colors">
                          {trailer.title}
                        </h4>
                        <span className="text-xs text-slate-400 mt-1 flex items-center gap-1.5">
                          <Clock className="w-3 h-3 text-slate-500" />
                          {trailer.duration_seconds}s
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Regular Seasons & Episodes */}
          {seasons.length > 0 && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <h3 className="text-base font-bold text-white">Episodes</h3>

                {/* Season Switcher */}
                {seasons.length > 1 && (
                  <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
                    {seasons.map((s) => (
                      <button
                        key={s.season_number}
                        onClick={() => setSelectedSeasonNumber(s.season_number)}
                        className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                          selectedSeasonNumber === s.season_number
                            ? 'bg-red-600 text-white shadow-sm'
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Season {s.season_number}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Episodes List */}
              <div className="space-y-3">
                {activeSeason?.episodes.map((ep) => {
                  const thumb = ep.artwork?.thumbnail || show.artwork?.thumbnail || banner;
                  const currentLang = selectedLanguages[ep.content_group] || ep.languages[0] || 'en';

                  return (
                    <div
                      key={ep.content_group}
                      className="p-3.5 bg-slate-950/60 border border-slate-800 hover:border-slate-700/80 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 transition-colors group"
                    >
                      {/* Thumbnail & Info */}
                      <div className="flex items-start gap-4 flex-1">
                        <div
                          onClick={() => onPlayEpisode(ep, currentLang)}
                          className="relative w-32 sm:w-36 h-20 bg-slate-900 rounded-lg overflow-hidden shrink-0 cursor-pointer"
                        >
                          {thumb && (
                            <img
                              src={thumb}
                              alt={ep.title}
                              className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                            />
                          )}
                          <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="w-8 h-8 rounded-full bg-red-600 text-white flex items-center justify-center shadow-lg">
                              <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                            </div>
                          </div>
                          <span className="absolute bottom-1 right-1 bg-black/80 text-[10px] text-slate-300 font-mono px-1.5 py-0.5 rounded">
                            {Math.floor(ep.duration_seconds / 60)}:{(ep.duration_seconds % 60).toString().padStart(2, '0')}
                          </span>
                        </div>

                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono font-bold text-red-500">
                              {ep.episode_number}.
                            </span>
                            <h4 className="text-sm font-bold text-white group-hover:text-red-400 transition-colors">
                              {ep.title}
                            </h4>
                          </div>
                          <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                            {ep.synopsis || show.synopsis}
                          </p>
                        </div>
                      </div>

                      {/* Language Selection Pills (Collapsed content_group magic!) */}
                      <div className="flex flex-col sm:items-end gap-1.5 shrink-0">
                        <div className="flex items-center gap-1">
                          <Globe className="w-3 h-3 text-slate-400" />
                          <span className="text-[11px] font-semibold text-slate-400">Audio:</span>
                        </div>
                        <div className="flex items-center gap-1 bg-slate-900 p-1 rounded-lg border border-slate-800">
                          {ep.languages.map((lang) => {
                            const isSelected = currentLang === lang;
                            return (
                              <button
                                key={lang}
                                type="button"
                                onClick={() => handleLanguageSelect(ep.content_group, lang)}
                                className={`px-2 py-0.5 text-xs font-bold uppercase rounded transition-all ${
                                  isSelected
                                    ? 'bg-blue-600 text-white shadow-sm'
                                    : 'text-slate-400 hover:text-slate-200'
                                }`}
                                title={`Switch audio to ${lang === 'en' ? 'English' : 'Hindi'}`}
                              >
                                {lang}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
