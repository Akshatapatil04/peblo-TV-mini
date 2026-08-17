import React, { useState, useEffect } from 'react';
import { X, Play, Pause, Volume2, VolumeX, Globe } from 'lucide-react';
import { CollapsedEpisode } from '../types';

interface TrailerPlayerModalProps {
  episode: CollapsedEpisode | null;
  initialLanguage?: string;
  isOpen: boolean;
  onClose: () => void;
}

export const TrailerPlayerModal: React.FC<TrailerPlayerModalProps> = ({
  episode,
  initialLanguage = 'en',
  isOpen,
  onClose
}) => {
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [progress, setProgress] = useState(15);
  const [selectedLanguage, setSelectedLanguage] = useState(initialLanguage);

  useEffect(() => {
    setSelectedLanguage(initialLanguage);
    setProgress(15);
    setIsPlaying(true);
  }, [episode, initialLanguage]);

  if (!isOpen || !episode) return null;

  const currentVariant = episode.audio_variants?.find((v) => v.language === selectedLanguage) || episode.audio_variants?.[0];
  const activeTitle = currentVariant?.title || episode.title;
  const duration = currentVariant?.duration_seconds || episode.duration_seconds || 60;
  const currentTime = Math.floor((duration * progress) / 100);

  const thumb = episode.artwork?.banner || episode.artwork?.thumbnail || episode.artwork?.poster;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/90 backdrop-blur-lg overflow-y-auto">
      <div className="relative w-full max-w-4xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden animate-fade-in text-white">
        {/* Player Screen */}
        <div className="relative aspect-video w-full bg-black flex items-center justify-center overflow-hidden group">
          {thumb && (
            <img
              src={thumb}
              alt={activeTitle}
              className={`w-full h-full object-cover opacity-80 transition-all ${isPlaying ? 'scale-100' : 'scale-95 blur-sm'}`}
            />
          )}

          {/* Close Button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-20 w-10 h-10 rounded-full bg-black/70 hover:bg-black text-white flex items-center justify-center border border-white/20 transition-all hover:scale-105"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Playing Simulation Animation Overlay */}
          {isPlaying && (
            <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-red-600/90 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse shadow-lg">
              <span className="w-2 h-2 rounded-full bg-white animate-ping" />
              PLAYING • {selectedLanguage.toUpperCase()} AUDIO
            </div>
          )}

          {/* Center Play/Pause Indicator */}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`w-16 h-16 rounded-full bg-red-600/90 text-white flex items-center justify-center shadow-2xl transition-all hover:scale-110 ${
              isPlaying ? 'opacity-0 group-hover:opacity-100' : 'opacity-100'
            }`}
          >
            {isPlaying ? <Pause className="w-8 h-8 fill-current" /> : <Play className="w-8 h-8 fill-current ml-1" />}
          </button>

          {/* Player Bottom Controls Bar */}
          <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black via-black/80 to-transparent p-4 space-y-2">
            {/* Scrubber Progress Bar */}
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden cursor-pointer"
              onClick={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const clickX = e.clientX - rect.left;
                setProgress((clickX / rect.width) * 100);
              }}
            >
              <div
                className="bg-red-600 h-full transition-all duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>

            {/* Controls row */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-4">
                <button onClick={() => setIsPlaying(!isPlaying)} className="hover:text-red-400 transition-colors">
                  {isPlaying ? <Pause className="w-5 h-5 fill-current" /> : <Play className="w-5 h-5 fill-current" />}
                </button>
                <button onClick={() => setIsMuted(!isMuted)} className="hover:text-slate-300 transition-colors">
                  {isMuted ? <VolumeX className="w-5 h-5 text-red-400" /> : <Volume2 className="w-5 h-5" />}
                </button>
                <span className="text-slate-400 font-mono">
                  {Math.floor(currentTime / 60)}:{(currentTime % 60).toString().padStart(2, '0')} / {Math.floor(duration / 60)}:{(duration % 60).toString().padStart(2, '0')}
                </span>
              </div>

              {/* Multi-language audio switcher */}
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800">
                  <Globe className="w-3.5 h-3.5 text-blue-400" />
                  <span className="text-[11px] text-slate-400">Audio:</span>
                  {episode.languages?.map((lang) => (
                    <button
                      key={lang}
                      onClick={() => setSelectedLanguage(lang)}
                      className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase transition-all ${
                        selectedLanguage === lang
                          ? 'bg-blue-600 text-white'
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {lang}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Player Metadata Footer */}
        <div className="p-4 bg-slate-900 flex items-center justify-between border-t border-slate-800 text-xs">
          <div>
            <h3 className="font-bold text-white text-sm">{activeTitle}</h3>
            <p className="text-slate-400 text-xs mt-0.5 line-clamp-1">{episode.synopsis}</p>
          </div>
          <span className="badge bg-slate-800 text-slate-300 font-mono">
            {episode.content_group}
          </span>
        </div>
      </div>
    </div>
  );
};
