import { type RefObject, useEffect, useRef, useState } from "react";
import { cn } from "./cn";

// ─── Types ────────────────────────────────────────────────────────────────────

type MediaType = "image" | "video" | "auto";

interface MediaRendererProps {
  /** URL of the media (image or video) */
  src: string;
  /** Force media type instead of auto-detecting from URL */
  mediaType?: MediaType;
  /** Alt text for images */
  alt?: string;
  /** CSS class applied to the img/video element */
  className?: string;
  /** Whether the video should be paused (only applies to video) */
  paused?: boolean;
  /** Whether video should loop (default true) */
  loop?: boolean;
  /** Whether video should be muted (default true) */
  muted?: boolean;
  /** Ref forwarded to the underlying video element */
  videoRef?: RefObject<HTMLVideoElement | null>;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const VIDEO_EXTENSIONS = new Set(["mp4", "webm", "ogg", "mov", "m4v", "avi"]);

/**
 * Registry for blob URL media type hints. Blob URLs have no file extension,
 * so callers can register the type here before passing the URL to MediaRenderer.
 * Usage: `blobMediaTypeHints.set(blobUrl, "video")`
 */
const blobMediaTypeHints = new Map<string, "image" | "video">();

function detectMediaType(url: string): "image" | "video" {
  // Check the blob hint registry first (blob URLs have no extension)
  const hint = blobMediaTypeHints.get(url);
  if (hint) return hint;

  try {
    const pathname = new URL(url, "https://placeholder.local").pathname;
    const ext = pathname.split(".").pop()?.toLowerCase() ?? "";
    return VIDEO_EXTENSIONS.has(ext) ? "video" : "image";
  } catch {
    return "image";
  }
}

/** Tracks URLs that have been fully loaded at least once — skips the blur-up animation on remount.
 * Keyed by normalized URL (no query params) so presigned URL rotation doesn't trigger replays. */
const loadedSrcs = new Set<string>();

function normalizeSrc(src: string): string {
  try {
    const u = new URL(src);
    u.search = "";
    return u.toString();
  } catch {
    return src;
  }
}

// ─── Component ────────────────────────────────────────────────────────────────

/**
 * Renders either an `<img>` or `<video>` element based on the media URL
 * extension or an explicit `mediaType` prop.
 *
 * For video: auto-plays muted by default, supports external pause control.
 */
function MediaRenderer({
  src,
  mediaType = "auto",
  alt = "Media content",
  className = "h-full w-full object-cover",
  paused,
  loop = true,
  muted = true,
  videoRef: externalRef,
}: MediaRendererProps) {
  const internalRef = useRef<HTMLVideoElement>(null);
  const videoElement = externalRef ?? internalRef;
  const resolved = mediaType === "auto" ? detectMediaType(src) : mediaType;

  const alreadySeen = loadedSrcs.has(normalizeSrc(src));
  const isCached =
    alreadySeen ||
    (resolved === "image" &&
      typeof Image !== "undefined" &&
      (() => {
        const img = new Image();
        img.src = src;
        return img.complete;
      })());

  const [loaded, setLoaded] = useState(isCached);

  useEffect(() => {
    if (loadedSrcs.has(normalizeSrc(src))) {
      setLoaded(true);
      return;
    }
    if (resolved === "image") {
      const img = new Image();
      img.src = src;
      setLoaded(img.complete);
    } else {
      setLoaded(false);
    }
  }, [src, resolved]);

  useEffect(() => {
    const el = videoElement.current;
    if (!el || resolved !== "video") {
      return;
    }
    if (paused) {
      el.pause();
    } else {
      el.play().catch(() => {
        /* autoplay may be blocked */
      });
    }
  }, [paused, resolved, videoElement]);

  const fadeClasses = cn(
    "transition-all duration-500",
    loaded ? "scale-100 blur-0 opacity-100" : "scale-[1.02] blur-sm opacity-0",
  );

  const placeholder = (
    <div
      className={cn(
        "absolute inset-0 bg-neutral-400 transition-opacity duration-500",
        loaded ? "opacity-0" : "animate-pulse opacity-100",
      )}
    />
  );

  if (resolved === "video") {
    return (
      <div className="relative h-full w-full overflow-hidden">
        {placeholder}
        <video
          ref={videoElement}
          src={src}
          className={cn(className, fadeClasses)}
          loop={loop}
          muted={muted}
          autoPlay={!paused}
          playsInline
          onLoadedData={() => {
            loadedSrcs.add(normalizeSrc(src));
            setLoaded(true);
          }}
        />
      </div>
    );
  }

  return (
    <div className="relative h-full w-full overflow-hidden">
      {placeholder}
      <img
        src={src}
        alt={alt}
        className={cn(className, fadeClasses)}
        onLoad={() => {
          loadedSrcs.add(normalizeSrc(src));
          setLoaded(true);
        }}
      />
    </div>
  );
}

export type { MediaRendererProps, MediaType };
export { blobMediaTypeHints, detectMediaType, MediaRenderer };
