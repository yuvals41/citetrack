import { Film, Pause, Play, Upload, Volume2, VolumeX, X } from "lucide-react";
import {
  type ChangeEvent,
  type DragEvent,
  type MouseEvent as ReactMouseEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { cn } from "./cn";
import { Slider } from "./slider";

interface VideoUploadProps {
  /** Emits the selected video file, or null when cleared */
  onChange?: (file: File | null) => void;
  /** Optional prefilled preview URL */
  value?: string;
  /** Accepted file types. Defaults to common video formats. */
  accept?: string;
  /** Max file size in bytes */
  maxSize?: number;
  disabled?: boolean;
  className?: string;
  /** Helper text shown below the upload zone */
  hint?: string;
  /** Main label shown in the empty state */
  label?: string;
  /** Aspect ratio for preview area */
  aspectRatio?: "square" | "video" | "portrait";
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const aspectRatioClasses = {
  square: "aspect-square",
  video: "aspect-video",
  portrait: "aspect-[4/5]",
} as const;

interface VideoPreviewProps {
  src: string;
  fileName: string | null;
  onRemove: () => void;
}

function VideoPreview({ src, fileName, onRemove }: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);

  // Keep audio state synced to the <video> element
  useEffect(() => {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    video.volume = volume;
    video.muted = muted || volume === 0;
  }, [volume, muted]);

  const togglePlay = (event: ReactMouseEvent) => {
    event.stopPropagation();
    const video = videoRef.current;
    if (!video) {
      return;
    }
    if (video.paused) {
      video.play().catch(() => {
        /* autoplay/permission errors are harmless here */
      });
    } else {
      video.pause();
    }
  };

  const onVolumeChange = (values: number[]) => {
    const next = values[0] ?? 0;
    setVolume(next);
    if (next > 0 && muted) {
      setMuted(false);
    }
  };

  const toggleMute = (event: ReactMouseEvent) => {
    event.stopPropagation();
    setMuted((prev) => !prev);
  };

  const isMuted = muted || volume === 0;

  return (
    <>
      <video
        ref={videoRef}
        key={src}
        src={src}
        playsInline
        preload="metadata"
        className="h-full w-full object-contain"
        onClick={togglePlay}
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
      >
        <track kind="captions" />
      </video>

      {/* Center play/pause button — horizontally + vertically centered in the preview area */}
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <button
          type="button"
          aria-label={playing ? "Pause video" : "Play video"}
          onClick={togglePlay}
          className={cn(
            "pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full bg-white text-black shadow-md transition-opacity",
            playing && "opacity-0 hover:opacity-100",
          )}
        >
          {playing ? (
            <Pause className="h-6 w-6 fill-current" />
          ) : (
            <Play className="h-6 w-6 translate-x-0.5 fill-current" />
          )}
        </button>
      </div>

      {/* Top-right volume control */}
      <div className="absolute right-2 top-2 flex items-center gap-2 rounded-full bg-white/90 px-2 py-1 text-black backdrop-blur-sm">
        <button
          type="button"
          aria-label={isMuted ? "Unmute" : "Mute"}
          onClick={toggleMute}
          className="flex h-6 w-6 items-center justify-center rounded-full hover:bg-black/10"
        >
          {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
        </button>
        <Slider
          className="w-24"
          min={0}
          max={1}
          step={0.05}
          value={[isMuted ? 0 : volume]}
          onValueChange={onVolumeChange}
          onPointerDown={(event) => event.stopPropagation()}
          onClick={(event) => event.stopPropagation()}
          aria-label="Volume"
        />
      </div>

      {/* Bottom caption bar */}
      <div className="absolute inset-x-0 bottom-0 flex items-center justify-between gap-3 bg-black/65 px-3 py-2 text-left text-white">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{fileName ?? "Uploaded video"}</p>
          <p className="text-xs text-white/75">Click border to replace</p>
        </div>
        <button
          type="button"
          aria-label="Remove video"
          onClick={(event) => {
            event.stopPropagation();
            onRemove();
          }}
          className="shrink-0 rounded-sm bg-white/15 p-1.5 transition-colors hover:bg-white/25"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </>
  );
}

function VideoUpload({
  onChange,
  value,
  accept = "video/mp4,video/webm,video/quicktime,video/ogg",
  maxSize,
  disabled = false,
  className,
  hint,
  label = "Upload video",
  aspectRatio = "video",
}: VideoUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const ownedUrls = useRef(new Set<string>());
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(value ?? null);
  const [fileName, setFileName] = useState<string | null>(null);

  useEffect(() => {
    setPreviewUrl(value ?? null);
  }, [value]);

  useEffect(() => {
    return () => {
      for (const url of ownedUrls.current) {
        URL.revokeObjectURL(url);
      }
      ownedUrls.current.clear();
    };
  }, []);

  const handleFile = useCallback(
    (file: File | null) => {
      if (!file) {
        return;
      }

      if (!file.type.startsWith("video/")) {
        setError("Please upload a video file.");
        return;
      }

      if (maxSize && file.size > maxSize) {
        setError(`Video exceeds ${formatBytes(maxSize)}.`);
        return;
      }

      setError(null);
      setFileName(file.name);
      setPreviewUrl((prev) => {
        if (prev && ownedUrls.current.has(prev)) {
          URL.revokeObjectURL(prev);
          ownedUrls.current.delete(prev);
        }
        const url = URL.createObjectURL(file);
        ownedUrls.current.add(url);
        return url;
      });
      onChange?.(file);
    },
    [maxSize, onChange],
  );

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    handleFile(file);
    event.target.value = "";
  };

  const onDrop = (event: DragEvent<HTMLButtonElement>) => {
    event.preventDefault();
    setDragging(false);
    if (disabled) {
      return;
    }
    handleFile(event.dataTransfer.files?.[0] ?? null);
  };

  const clearVideo = () => {
    setError(null);
    setFileName(null);
    setPreviewUrl((prev) => {
      if (prev && ownedUrls.current.has(prev)) {
        URL.revokeObjectURL(prev);
        ownedUrls.current.delete(prev);
      }
      return null;
    });
    onChange?.(null);
  };

  return (
    <div className={cn("flex w-full flex-col gap-3", className)}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={(event) => {
          event.preventDefault();
          if (!disabled) {
            setDragging(true);
          }
        }}
        onDragLeave={() => setDragging(false)}
        className={cn(
          "relative flex w-full cursor-pointer flex-col overflow-hidden rounded-sm border border-border bg-background transition-colors",
          dragging ? "border-foreground bg-surface" : "hover:bg-surface/40",
          disabled && "cursor-not-allowed opacity-50",
        )}
      >
        <div className={cn("relative w-full bg-black", aspectRatioClasses[aspectRatio])}>
          {previewUrl ? (
            <VideoPreview src={previewUrl} fileName={fileName} onRemove={clearVideo} />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface text-foreground-muted">
                <Film className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  {dragging ? "Drop video here" : label}
                </p>
                <p className="mt-1 text-xs text-foreground-muted">
                  Drag and drop or click to browse
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-border px-3 py-2 text-left">
          <p className="min-w-0 flex-1 text-xs text-foreground-muted">
            {error
              ? error
              : (hint ??
                ["MP4, WEBM, MOV, OGG", maxSize ? `Max ${formatBytes(maxSize)}` : null]
                  .filter(Boolean)
                  .join(" · "))}
          </p>
          <span className="inline-flex items-center gap-1 text-xs font-medium text-foreground-muted">
            <Upload className="h-3.5 w-3.5" />
            {previewUrl ? "Replace" : "Browse"}
          </span>
        </div>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        disabled={disabled}
        onChange={onInputChange}
        className="sr-only"
        tabIndex={-1}
      />
    </div>
  );
}

export type { VideoUploadProps };
export { VideoUpload };
