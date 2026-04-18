import { ImagePlus, Upload, X } from "lucide-react";
import { type ChangeEvent, type DragEvent, useCallback, useEffect, useRef, useState } from "react";
import { cn } from "./cn";

interface ImageUploadProps {
  /** Emits the selected image file, or null when cleared */
  onChange?: (file: File | null) => void;
  /** Optional prefilled preview URL */
  value?: string;
  /** Accepted file types. Defaults to common image formats. */
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

function ImageUpload({
  onChange,
  value,
  accept = "image/png,image/jpeg,image/webp,image/gif,image/svg+xml",
  maxSize,
  disabled = false,
  className,
  hint,
  label = "Upload image",
  aspectRatio = "square",
}: ImageUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const ownedUrls = useRef(new Set<string>());
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(value ?? null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    setPreviewUrl(value ?? null);
    setImageLoaded(false);
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

      if (!file.type.startsWith("image/")) {
        setError("Please upload an image file.");
        return;
      }

      if (maxSize && file.size > maxSize) {
        setError(`Image exceeds ${formatBytes(maxSize)}.`);
        return;
      }

      setError(null);
      setFileName(file.name);
      setImageLoaded(false);
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

  const clearImage = () => {
    setError(null);
    setFileName(null);
    setImageLoaded(false);
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
        <div className={cn("relative w-full", aspectRatioClasses[aspectRatio])}>
          {previewUrl ? (
            <>
              {/* Placeholder shown while image loads */}
              <div
                className={cn(
                  "absolute inset-0 bg-neutral-400 transition-opacity duration-500",
                  imageLoaded ? "opacity-0" : "animate-pulse opacity-100",
                )}
              />
              {/* biome-ignore lint/performance/noImgElement: shared UI package cannot depend on next/image */}
              <img
                src={previewUrl}
                alt={fileName ?? "Uploaded preview"}
                onLoad={() => setImageLoaded(true)}
                className={cn(
                  "h-full w-full object-cover transition-all duration-500",
                  imageLoaded ? "scale-100 blur-0 opacity-100" : "scale-[1.02] blur-sm opacity-0",
                )}
              />
              <div className="absolute inset-x-0 bottom-0 flex items-center justify-between gap-3 bg-black/65 px-3 py-2 text-left text-white">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{fileName ?? "Uploaded image"}</p>
                  <p className="text-xs text-white/75">Click to replace</p>
                </div>
                <button
                  type="button"
                  aria-label="Remove image"
                  onClick={(event) => {
                    event.stopPropagation();
                    clearImage();
                  }}
                  className="shrink-0 rounded-sm bg-white/15 p-1.5 transition-colors hover:bg-white/25"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </>
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-6 py-8 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface text-foreground-muted">
                <ImagePlus className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  {dragging ? "Drop image here" : label}
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
                ["PNG, JPG, WEBP, GIF, SVG", maxSize ? `Max ${formatBytes(maxSize)}` : null]
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

export type { ImageUploadProps };
export { ImageUpload };
