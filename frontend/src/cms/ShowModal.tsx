import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, Loader2 } from 'lucide-react';
import { Show } from '../types';
import { ArtworkUploadSlot } from './ArtworkUploadSlot';
import { api, ApiError } from '../api/client';

interface ShowModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  show?: Show | null;
}

const ALLOWED_SECTIONS = ['featured', 'series', 'minisodes', 'songs'];
const ALLOWED_CATEGORIES = [
  'adventure', 'folk', 'friendship', 'india', 'language',
  'learning', 'maths', 'music', 'nature', 'reading',
  'science', 'singalong', 'stories', 'travel', 'values'
];

export const ShowModal: React.FC<ShowModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  show
}) => {
  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [section, setSection] = useState('');
  const [categories, setCategories] = useState<string[]>([]);
  const [status, setStatus] = useState<'draft' | 'published'>('draft');
  const [synopsis, setSynopsis] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (show) {
      setTitle(show.title || '');
      setSlug(show.slug || '');
      setSection(show.section || '');
      setCategories(show.categories || []);
      setStatus(show.status || 'draft');
      setSynopsis(show.synopsis || '');
    } else {
      setTitle('');
      setSlug('');
      setSection('featured');
      setCategories(['adventure', 'india']);
      setStatus('draft');
      setSynopsis('');
    }
    setErrorMessage(null);
  }, [show, isOpen]);

  if (!isOpen) return null;

  const handleTitleChange = (val: string) => {
    setTitle(val);
    if (!show) {
      // Auto-generate slug from title for new shows
      const generatedSlug = val.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
      setSlug(generatedSlug);
    }
  };

  const toggleCategory = (cat: string) => {
    setCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    );
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!title.trim()) {
      setErrorMessage('Show title is required.');
      return;
    }
    if (!slug.trim()) {
      setErrorMessage('Show slug is required.');
      return;
    }
    if (status === 'published' && !section) {
      setErrorMessage('A published show must have a section assigned.');
      return;
    }

    try {
      setIsSaving(true);
      const payload: Partial<Show> = {
        title: title.trim(),
        slug: slug.trim(),
        section: section || undefined,
        categories,
        status,
        synopsis: synopsis.trim()
      };

      if (show) {
        await api.updateShow(show.id, payload);
      } else {
        await api.createShow(payload);
      }
      onSuccess();
      onClose();
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err.message || 'Failed to save show.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  const posterArt = show?.artworks?.find((a) => a.slot_type === 'poster');
  const bannerArt = show?.artworks?.find((a) => a.slot_type === 'banner');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden my-8 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div>
            <h3 className="text-lg font-bold text-white">
              {show ? `Edit Show — ${show.title}` : 'Create New Show'}
            </h3>
            <p className="text-xs text-slate-400">Configure show metadata, sections, categories, and artwork.</p>
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

        {/* Form Body */}
        <form onSubmit={handleSave} className="p-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Title */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Show Title <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => handleTitleChange(e.target.value)}
                placeholder="e.g. Moti's Many Lives"
                className="input-field"
                required
              />
            </div>

            {/* Slug */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                URL Slug <span className="text-red-400">*</span>
              </label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="e.g. motis-many-lives"
                className="input-field font-mono text-xs"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Section */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Target Section {status === 'published' && <span className="text-red-400">*</span>}
              </label>
              <select
                value={section}
                onChange={(e) => setSection(e.target.value)}
                className="input-field capitalize"
              >
                <option value="">-- No Section (Draft only) --</option>
                {ALLOWED_SECTIONS.map((sec) => (
                  <option key={sec} value={sec}>
                    {sec}
                  </option>
                ))}
              </select>
            </div>

            {/* Status */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Publish Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as 'draft' | 'published')}
                className="input-field"
              >
                <option value="draft">Draft (Hidden from Catalogue)</option>
                <option value="published">Published (Ready for Viewer)</option>
              </select>
            </div>
          </div>

          {/* Synopsis */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
              Show Synopsis
            </label>
            <textarea
              rows={3}
              value={synopsis}
              onChange={(e) => setSynopsis(e.target.value)}
              placeholder="Brief summary of the show..."
              className="input-field resize-none text-xs"
            />
          </div>

          {/* Categories Pill Multi-select */}
          <div>
            <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
              Categories ({categories.length} selected)
            </label>
            <div className="flex flex-wrap gap-1.5">
              {ALLOWED_CATEGORIES.map((cat) => {
                const isSelected = categories.includes(cat);
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => toggleCategory(cat)}
                    className={`px-3 py-1 rounded-full text-xs font-semibold capitalize transition-all ${
                      isSelected
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'bg-slate-800/80 text-slate-400 hover:text-slate-200 border border-slate-700'
                    }`}
                  >
                    {cat}
                  </button>
                );
              })}
            </div>
          </div>

          {/* 3 Artwork Slots (Show Level: Poster & Banner) */}
          <div className="border-t border-slate-800 pt-5">
            <h4 className="text-sm font-bold text-white mb-3">Show Artwork Slots</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ArtworkUploadSlot
                slotType="poster"
                showId={show?.id}
                existingArtwork={posterArt}
                onArtworkChange={() => {}}
              />
              <ArtworkUploadSlot
                slotType="banner"
                showId={show?.id}
                existingArtwork={bannerArt}
                onArtworkChange={() => {}}
              />
            </div>
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
                  Save Show
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
