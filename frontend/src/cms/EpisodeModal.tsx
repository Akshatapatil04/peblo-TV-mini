import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, Loader2, Info } from 'lucide-react';
import { Episode, Show } from '../types';
import { ArtworkUploadSlot } from './ArtworkUploadSlot';
import { api, ApiError } from '../api/client';

interface EpisodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  shows: Show[];
  initialShowId?: string;
  episode?: Episode | null;
}

export const EpisodeModal: React.FC<EpisodeModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  shows,
  initialShowId,
  episode
}) => {
  const [showId, setShowId] = useState(initialShowId || '');
  const [seasonNumber, setSeasonNumber] = useState<number>(1);
  const [episodeNumber, setEpisodeNumber] = useState<number>(1);
  const [episodeTitle, setEpisodeTitle] = useState('');
  const [durationSeconds, setDurationSeconds] = useState<number>(300);
  const [language, setLanguage] = useState<string>('en');
  const [contentGroup, setContentGroup] = useState<string>('');
  const [status, setStatus] = useState<'draft' | 'published'>('published');
  const [synopsis, setSynopsis] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (episode) {
      setShowId(episode.show_id || initialShowId || '');
      setSeasonNumber(episode.season_number);
      setEpisodeNumber(episode.episode_number);
      setEpisodeTitle(episode.episode_title || '');
      setDurationSeconds(episode.duration_seconds || 300);
      setLanguage(episode.language || 'en');
      setContentGroup(episode.content_group || '');
      setStatus(episode.status || 'draft');
      setSynopsis(episode.synopsis || '');
    } else {
      setShowId(initialShowId || (shows[0]?.id || ''));
      setSeasonNumber(1);
      setEpisodeNumber(1);
      setEpisodeTitle('');
      setDurationSeconds(300);
      setLanguage('en');
      setContentGroup('');
      setStatus('published');
      setSynopsis('');
    }
    setErrorMessage(null);
  }, [episode, initialShowId, shows, isOpen]);

  if (!isOpen) return null;

  // Auto-generate content_group suggestion
  const handleGenerateContentGroup = () => {
    const selectedShow = shows.find((s) => s.id === showId);
    const slug = selectedShow?.slug || 'show';
    const sStr = seasonNumber.toString().padStart(2, '0');
    const eStr = episodeNumber.toString().padStart(2, '0');
    setContentGroup(`${slug}-s${sStr}e${eStr}`);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!showId) {
      setErrorMessage('Please select a parent show.');
      return;
    }
    if (!episodeTitle.trim()) {
      setErrorMessage('Episode title is required.');
      return;
    }
    if (!contentGroup.trim()) {
      setErrorMessage('Content group key is required.');
      return;
    }
    if (status === 'published' && durationSeconds <= 0) {
      setErrorMessage('A published episode must have a duration greater than 0 seconds.');
      return;
    }

    try {
      setIsSaving(true);
      const payload: Partial<Episode> = {
        show_id: showId,
        season_number: seasonNumber,
        episode_number: episodeNumber,
        episode_title: episodeTitle.trim(),
        duration_seconds: durationSeconds,
        language: language.trim(),
        content_group: contentGroup.trim(),
        status,
        synopsis: synopsis.trim()
      };

      if (episode) {
        await api.updateEpisode(episode.id, payload);
      } else {
        await api.createEpisode(payload);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err.message || 'Failed to save episode.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const thumbArt = episode?.artworks?.find((a) => a.slot_type === 'thumbnail');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div>
            <h3 className="text-lg font-bold text-white">
              {episode ? `Edit Episode — ${episode.episode_title}` : 'Create New Episode'}
            </h3>
            <p className="text-xs text-slate-400">Manage audio languages, duration, and thumbnail artwork.</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="mx-6 mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-2.5 text-xs text-red-300">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="flex-1 font-medium">{errorMessage}</div>
          </div>
        )}

        <form onSubmit={handleSave} className="p-6 space-y-4">
          {/* Show Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Parent Show <span className="text-red-400">*</span>
            </label>
            <select
              value={showId}
              onChange={(e) => setShowId(e.target.value)}
              className="input-field"
              required
            >
              <option value="">-- Select Show --</option>
              {shows.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title} ({s.section || 'No section'})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Season Number */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Season Number
              </label>
              <input
                type="number"
                min={0}
                max={99}
                value={seasonNumber}
                onChange={(e) => setSeasonNumber(parseInt(e.target.value) || 0)}
                className="input-field"
                required
              />
              <span className="text-[10px] text-slate-500 mt-0.5 block">Season 0 = Trailers</span>
            </div>

            {/* Episode Number */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Episode Number
              </label>
              <input
                type="number"
                min={1}
                max={999}
                value={episodeNumber}
                onChange={(e) => setEpisodeNumber(parseInt(e.target.value) || 1)}
                className="input-field"
                required
              />
            </div>

            {/* Language */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Audio Language <span className="text-red-400">*</span>
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="input-field font-mono"
              >
                <option value="en">English (en)</option>
                <option value="hi">Hindi (hi)</option>
              </select>
            </div>
          </div>

          {/* Episode Title */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Episode Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={episodeTitle}
              onChange={(e) => setEpisodeTitle(e.target.value)}
              placeholder="e.g. The Lost Kite"
              className="input-field"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Duration */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Duration (Seconds) <span className="text-red-400">*</span>
              </label>
              <input
                type="number"
                min={0}
                value={durationSeconds}
                onChange={(e) => setDurationSeconds(parseInt(e.target.value) || 0)}
                placeholder="e.g. 480"
                className="input-field"
                required
              />
              <span className="text-[10px] text-slate-400 mt-0.5 block">
                ≈ {Math.floor(durationSeconds / 60)}m {durationSeconds % 60}s
              </span>
            </div>

            {/* Status */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as 'draft' | 'published')}
                className="input-field"
              >
                <option value="draft">Draft</option>
                <option value="published">Published</option>
              </select>
            </div>
          </div>

          {/* Content Group with Helper */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                Content Group Key <span className="text-red-400">*</span>
              </label>
              <button
                type="button"
                onClick={handleGenerateContentGroup}
                className="text-[11px] text-blue-400 hover:text-blue-300 underline"
              >
                Auto-generate
              </button>
            </div>
            <input
              type="text"
              value={contentGroup}
              onChange={(e) => setContentGroup(e.target.value)}
              placeholder="e.g. motis-many-lives-s01e01"
              className="input-field font-mono text-xs"
              required
            />
            <div className="mt-1.5 flex items-start gap-1.5 text-[11px] text-slate-400 bg-slate-950/60 p-2 rounded-lg border border-slate-800">
              <Info className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
              <span>
                <strong>Language Collapsing:</strong> Episodes with the same content_group collapse into a single viewer entry with multiple audio tracks (e.g. English/Hindi).
              </span>
            </div>
          </div>

          {/* Episode Thumbnail Artwork */}
          <div className="border-t border-slate-800 pt-4">
            <ArtworkUploadSlot
              slotType="thumbnail"
              episodeId={episode?.id}
              existingArtwork={thumbArt}
              onArtworkChange={() => {}}
            />
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="btn btn-primary"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Episode
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
