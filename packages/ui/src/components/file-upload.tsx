import { File as FileIcon, Upload, X } from "lucide-react";
import { type ChangeEvent, type DragEvent, useCallback, useRef, useState } from "react";
import { cn } from "./cn";

// ─── Types ────────────────────────────────────────────────────────────────────

interface FileUploadFile {
  id: string;
  file: File;
  preview?: string;
}

interface FileUploadProps {
  /** Called when file list changes */
  onFilesChange?: (files: File[]) => void;
  /** Accept string passed to the input, e.g. "image/*,.pdf" */
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
  /** Max file size in bytes. Files exceeding this are rejected. */
  maxSize?: number;
  /**
   * Where to render the file list relative to the drop zone.
   * - "bottom" (default): list appears below the drop zone
   * - "right": list appears to the right of the drop zone
   * - "left": list appears to the left of the drop zone
   */
  filesPosition?: "bottom" | "right" | "left";
  className?: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function buildEntry(file: File): FileUploadFile {
  return {
    id: `${file.name}-${file.size}-${file.lastModified}`,
    file,
    preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined,
  };
}

function buildHintText(accept: string | undefined, maxSize: number | undefined): string {
  return [
    accept && `Accepted: ${accept}`,
    maxSize && `Max ${formatBytes(maxSize)}`,
    !(accept || maxSize) && "Any file type",
  ]
    .filter(Boolean)
    .join(" · ");
}

// ─── Subcomponents ────────────────────────────────────────────────────────────

interface DropZoneProps {
  dragging: boolean;
  disabled: boolean;
  isSide: boolean;
  accept?: string;
  maxSize?: number;
  onDrop: (e: DragEvent<HTMLElement>) => void;
  onDragOver: (e: DragEvent<HTMLElement>) => void;
  onDragLeave: () => void;
  onClick: () => void;
}

function DropZone({
  dragging,
  disabled,
  isSide,
  accept,
  maxSize,
  onDrop,
  onDragOver,
  onDragLeave,
  onClick,
}: DropZoneProps) {
  return (
    <button
      type="button"
      aria-label="Upload files"
      disabled={disabled}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onClick={onClick}
      className={cn(
        "flex w-full cursor-pointer flex-col items-center justify-center gap-2 rounded-sm border-2 border-dashed px-6 py-10 text-center transition-colors",
        isSide && "flex-1 self-stretch",
        dragging
          ? "border-foreground bg-surface"
          : "border-border hover:border-foreground-muted hover:bg-surface/50",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      <Upload className="h-8 w-8 text-foreground-muted" />
      <div>
        <p className="text-sm font-medium text-foreground">
          {dragging ? "Drop files here" : "Click to upload or drag and drop"}
        </p>
        <p className="mt-1 text-xs text-foreground-muted">{buildHintText(accept, maxSize)}</p>
      </div>
    </button>
  );
}

interface FileListProps {
  entries: FileUploadFile[];
  isSide: boolean;
  onRemove: (id: string) => void;
}

function FileList({ entries, isSide, onRemove }: FileListProps) {
  return (
    <ul className={cn("space-y-2", isSide && "flex-1 min-w-0")}>
      {entries.map((entry) => (
        <li
          key={entry.id}
          className="flex items-center gap-3 rounded-sm border border-border bg-surface px-3 py-2"
        >
          {entry.preview ? (
            // biome-ignore lint/performance/noImgElement: this is a shared UI package, not a Next.js page; next/image is not available here
            <img
              src={entry.preview}
              alt={entry.file.name}
              className="h-8 w-8 rounded-sm object-cover shrink-0"
            />
          ) : (
            <FileIcon className="h-8 w-8 shrink-0 text-foreground-muted" />
          )}
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{entry.file.name}</p>
            <p className="text-xs text-foreground-muted">{formatBytes(entry.file.size)}</p>
          </div>
          <button
            type="button"
            aria-label={`Remove ${entry.file.name}`}
            onClick={() => onRemove(entry.id)}
            className="shrink-0 rounded-sm p-0.5 opacity-50 transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <X className="h-4 w-4" />
          </button>
        </li>
      ))}
    </ul>
  );
}

// ─── Component ────────────────────────────────────────────────────────────────

function FileUpload({
  onFilesChange,
  accept,
  multiple = true,
  disabled = false,
  maxSize,
  filesPosition = "bottom",
  className,
}: FileUploadProps) {
  const isSide = filesPosition === "right" || filesPosition === "left";
  const [entries, setEntries] = useState<FileUploadFile[]>([]);
  const [dragging, setDragging] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const processFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) {
        return;
      }
      const newErrors: string[] = [];
      const valid: FileUploadFile[] = [];

      for (const file of incoming) {
        if (maxSize && file.size > maxSize) {
          newErrors.push(`"${file.name}" exceeds ${formatBytes(maxSize)}`);
          continue;
        }
        valid.push(buildEntry(file));
      }

      setErrors(newErrors);
      setEntries((prev) => {
        const merged = multiple ? [...prev, ...valid] : valid;
        // deduplicate by id
        const seen = new Set<string>();
        const deduped = merged.filter((e) => {
          if (seen.has(e.id)) {
            return false;
          }
          seen.add(e.id);
          return true;
        });
        onFilesChange?.(deduped.map((e) => e.file));
        return deduped;
      });
    },
    [multiple, maxSize, onFilesChange],
  );

  const handleDrop = useCallback(
    (e: DragEvent<HTMLElement>) => {
      e.preventDefault();
      setDragging(false);
      if (!disabled) {
        processFiles(e.dataTransfer.files);
      }
    },
    [disabled, processFiles],
  );

  const handleDragOver = (e: DragEvent<HTMLElement>) => {
    e.preventDefault();
    if (!disabled) {
      setDragging(true);
    }
  };

  const handleDragLeave = () => setDragging(false);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    processFiles(e.target.files);
    // reset so same file can be re-added after removal
    e.target.value = "";
  };

  const removeEntry = (id: string) => {
    setEntries((prev) => {
      const next = prev.filter((e) => {
        if (e.id === id && e.preview) {
          URL.revokeObjectURL(e.preview);
        }
        return e.id !== id;
      });
      onFilesChange?.(next.map((e) => e.file));
      return next;
    });
  };

  const dropZone = (
    <DropZone
      dragging={dragging}
      disabled={disabled}
      isSide={isSide}
      accept={accept}
      maxSize={maxSize}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onClick={() => inputRef.current?.click()}
    />
  );

  const fileList =
    entries.length > 0 ? (
      <FileList entries={entries} isSide={isSide} onRemove={removeEntry} />
    ) : null;

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div
        className={cn(
          "flex gap-3",
          filesPosition === "bottom" && "flex-col",
          filesPosition === "right" && "flex-row items-start",
          filesPosition === "left" && "flex-row-reverse items-start",
        )}
      >
        {dropZone}
        {isSide && fileList}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple={multiple}
        disabled={disabled}
        onChange={handleChange}
        className="sr-only"
        tabIndex={-1}
      />

      {errors.length > 0 && (
        <ul className="space-y-1">
          {errors.map((err) => (
            <li key={err} className="text-xs text-error-foreground">
              {err}
            </li>
          ))}
        </ul>
      )}

      {!isSide && fileList}
    </div>
  );
}

export type { FileUploadFile, FileUploadProps };
export { FileUpload };
