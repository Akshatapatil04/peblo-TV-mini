import React, { useState, useRef } from 'react';
import { Upload, X, AlertTriangle, Image as ImageIcon, Loader2 } from 'lucide-react';
import { api, ApiError } from '../api/client';
import { Artwork } from '../types';

interface ArtworkUploadSlotProps {
  slotType: 'poster' | 'banner' | 'thumbnail';
  showId?: string;
  episodeId?: string;
  existingArtwork?: Artwork;
  onArtworkChange: (artwork?: Artwork) => void;
}

const SLOT_CONFIG = {
  poster: {
    label: 'Poster Artwork',
    aspect: '2:3 Portrait',
    dimensions: '~600 × 900 px',
    maxSize: '200 KB max',
    aspectRatioCss: '2 / 3',
    containerClass: 'w-40 h-60'
  },
  banner: {
    label: 'Hero Banner',
    aspect: '16:9 Landscape',
    dimensions: '~1280 × 720 px',
    maxSize: '200 KB max',
    aspectRatioCss: '16 / 9',
    containerClass: 'w-full h-44'
  },
  thumbnail: {
    label: 'Episode Thumbnail',
    aspect: '16:9 Landscape',
    dimensions: '~640 × 360 px',
    maxSize: '200 KB max',
    aspectRatioCss: '16 / 9',
    containerClass: 'w-full h-36'
  }
};

export const ArtworkUploadSlot: React.FC<ArtworkUploadSlotProps> = ({
  slotType,
  showId,
  episodeId,
  existingArtwork,
  onArtworkChange
}) => {
  const config = SLOT_CONFIG[slotType];
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(existingArtwork?.url || null);

  const handleFile = async (file: File) => {
    setErrorMessage(null);

    // Initial pre-upload client-side quick check
    if (file.size > 200 * 1024) {
      const kb = (file.size / 1024).toFixed(1);
      setErrorMessage(`File is ${kb} KB, which exceeds the 200 KB limit. Please compress before uploading.`);
      return;
    }

    try {
      setIsUploading(true);
      const uploaded = await api.uploadArtwork(file, slotType, showId, episodeId);
      setPreviewUrl(uploaded.url);
      onArtworkChange(uploaded);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage(err.message || 'Failed to upload artwork.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleRemove = async () => {
    if (existingArtwork?.id) {
      try {
        await api.deleteArtwork(existingArtwork.id);
      } catch (e) {
        console.error('Failed to delete artwork record', e);
      }
    }
    setPreviewUrl(null);
    setErrorMessage(null);
    onArtworkChange(undefined);
  };

  return (
    <div className="flex flex-col gap-2 p-3.5 bg-slate-900/60 border border-slate-800 rounded-xl">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-sm font-bold text-slate-200">{config.label}</span>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-xs font-semibold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              {config.aspect}
            </span>
            <span className="text-xs text-slate-400 font-mono">{config.dimensions}</span>
            <span className="text-[11px] text-amber-400/80 font-medium">({config.maxSize})</span>
          </div>
        </div>

        {previewUrl && (
          <button
            type="button"
            onClick={handleRemove}
            className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 p-1 rounded hover:bg-red-500/10 transition-colors"
            title="Remove artwork"
          >
            <X className="w-3.5 h-3.5" />
            Remove
          </button>
        )}
      </div>

      {/* Upload & Preview Dropzone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative overflow-hidden cursor-pointer rounded-lg border-2 border-dashed transition-all flex flex-col items-center justify-center text-center p-4 ${
          isDragOver
            ? 'border-blue-500 bg-blue-500/10'
            : errorMessage
            ? 'border-red-500/60 bg-red-500/5'
            : previewUrl
            ? 'border-slate-700 bg-slate-950'
            : 'border-slate-800 hover:border-slate-600 bg-slate-900/40'
        }`}
        style={{ minHeight: slotType === 'poster' ? '180px' : '120px' }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        {isUploading ? (
          <div className="flex flex-col items-center gap-2 py-6">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <span className="text-xs font-semibold text-slate-300">Validating & Uploading...</span>
          </div>
        ) : previewUrl ? (
          <div className="relative w-full h-full flex items-center justify-center group">
            <img
              src={previewUrl}
              alt={config.label}
              className="max-h-48 rounded object-contain shadow-md"
            />
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1 text-white">
              <Upload className="w-5 h-5 text-blue-400" />
              <span className="text-xs font-semibold">Click or Drop to Replace</span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2 py-4 text-slate-400">
            <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
              <ImageIcon className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-medium text-slate-300">
                <span className="text-blue-400 font-semibold">Click to upload</span> or drag and drop
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">JPEG, PNG or WebP up to 200 KB</p>
            </div>
          </div>
        )}
      </div>

      {/* Friendly Error Banner */}
      {errorMessage && (
        <div className="flex items-start gap-2 p-2.5 bg-red-500/10 border border-red-500/30 rounded-lg text-xs text-red-300 animate-fade-in">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-red-200">Validation Error</p>
            <p className="mt-0.5 leading-relaxed">{errorMessage}</p>
          </div>
        </div>
      )}
    </div>
  );
};
