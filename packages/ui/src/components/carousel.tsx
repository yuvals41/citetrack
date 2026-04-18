import { ChevronLeft, ChevronRight } from "lucide-react";
import {
  createContext,
  type KeyboardEvent,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { cn } from "./cn";

// ─── Context ─────────────────────────────────────────────────────────────────

interface CarouselContextValue {
  current: number;
  count: number;
  prev: () => void;
  next: () => void;
  goTo: (index: number) => void;
  loop: boolean;
}

const CarouselContext = createContext<CarouselContextValue | null>(null);

function useCarousel(): CarouselContextValue {
  const ctx = useContext(CarouselContext);
  if (!ctx) {
    throw new Error("useCarousel must be used within <Carousel>");
  }
  return ctx;
}

// ─── Root ─────────────────────────────────────────────────────────────────────

interface CarouselProps {
  children: React.ReactNode;
  defaultIndex?: number;
  loop?: boolean;
  className?: string;
  /** Auto-advance interval in ms. Omit or 0 to disable. */
  autoPlay?: number;
  /** Pause auto-play while the user's mouse is over the carousel. */
  pauseOnHover?: boolean;
}

function Carousel({
  children,
  defaultIndex = 0,
  loop = true,
  autoPlay = 0,
  pauseOnHover = true,
  className,
}: CarouselProps) {
  const [current, setCurrent] = useState(defaultIndex);
  const [count, setCount] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const prev = useCallback(() => {
    setCurrent((c) => {
      if (c === 0) {
        return loop ? count - 1 : 0;
      }
      return c - 1;
    });
  }, [loop, count]);

  const next = useCallback(() => {
    setCurrent((c) => {
      if (c === count - 1) {
        return loop ? 0 : count - 1;
      }
      return c + 1;
    });
  }, [loop, count]);

  const goTo = useCallback((index: number) => setCurrent(index), []);

  // Auto-play
  useEffect(() => {
    if (!autoPlay || count === 0 || (pauseOnHover && isHovered)) {
      return;
    }
    timerRef.current = setInterval(next, autoPlay);
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [autoPlay, next, count, isHovered, pauseOnHover]);

  useEffect(() => {
    if (!(pauseOnHover && rootRef.current)) {
      return;
    }
    const element = rootRef.current;
    const handleEnter = () => setIsHovered(true);
    const handleLeave = () => setIsHovered(false);

    element.addEventListener("mouseenter", handleEnter);
    element.addEventListener("mouseleave", handleLeave);

    return () => {
      element.removeEventListener("mouseenter", handleEnter);
      element.removeEventListener("mouseleave", handleLeave);
    };
  }, [pauseOnHover]);

  return (
    <CarouselContext.Provider value={{ current, count, prev, next, goTo, loop }}>
      <div
        className={cn("relative", className)}
        data-count-setter="true"
        // count slides once children mount/update
        ref={(el) => {
          rootRef.current = el;
          if (el) {
            const items = el.querySelectorAll("[data-carousel-item]");
            if (items.length !== count) {
              setCount(items.length);
            }
          }
        }}
      >
        {children}
      </div>
    </CarouselContext.Provider>
  );
}

// ─── Content ──────────────────────────────────────────────────────────────────

function CarouselContent({
  className,
  children,
  height,
}: {
  className?: string;
  children: React.ReactNode;
  /** Height of the slide viewport (e.g. 320, "20rem", "50vh"). */
  height?: number | string;
}) {
  return (
    <div className={cn("overflow-hidden rounded-sm", className)} style={{ height }}>
      <div className="flex h-full">{children}</div>
    </div>
  );
}

// ─── Item ─────────────────────────────────────────────────────────────────────

function CarouselItem({
  className,
  children,
  index = 0,
}: {
  className?: string;
  children: React.ReactNode;
  index?: number;
}) {
  const { current } = useCarousel();
  return (
    <div
      data-carousel-item="true"
      aria-hidden={index !== current}
      className={cn(
        "h-full w-full shrink-0 transition-all duration-300",
        index === current ? "block" : "hidden",
        className,
      )}
    >
      <div className="h-full w-full">{children}</div>
    </div>
  );
}

// ─── Controls ─────────────────────────────────────────────────────────────────

function CarouselPrevious({ className }: { className?: string }) {
  const { prev, current, loop } = useCarousel();
  const disabled = !loop && current === 0;

  const handleKey = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      prev();
    }
  };

  return (
    <button
      type="button"
      aria-label="Previous slide"
      disabled={disabled}
      onClick={prev}
      onKeyDown={handleKey}
      className={cn(
        "inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-foreground text-background transition-opacity",
        "hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-30",
        className,
      )}
    >
      <ChevronLeft className="h-4 w-4" />
    </button>
  );
}

function CarouselNext({ className }: { className?: string }) {
  const { next, current, count, loop } = useCarousel();
  const disabled = !loop && current === count - 1;

  const handleKey = (e: KeyboardEvent<HTMLButtonElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      next();
    }
  };

  return (
    <button
      type="button"
      aria-label="Next slide"
      disabled={disabled}
      onClick={next}
      onKeyDown={handleKey}
      className={cn(
        "inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full bg-foreground text-background transition-opacity",
        "hover:opacity-80 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        "disabled:pointer-events-none disabled:opacity-30",
        className,
      )}
    >
      <ChevronRight className="h-4 w-4" />
    </button>
  );
}

// ─── Dots ─────────────────────────────────────────────────────────────────────

function CarouselDots({ className }: { className?: string }) {
  const { current, count, goTo } = useCarousel();
  return (
    <div className={cn("flex items-center justify-center gap-1.5", className)}>
      {Array.from({ length: count }, (_, i) => (
        <button
          type="button"
          // biome-ignore lint/suspicious/noArrayIndexKey: dots are derived from a fixed count, no stable id exists
          key={`dot-${i}`}
          aria-label={`Go to slide ${i + 1}`}
          aria-current={i === current}
          onClick={() => goTo(i)}
          className={cn(
            "h-1.5 rounded-full transition-all duration-200",
            i === current ? "w-4 bg-foreground" : "w-1.5 bg-border hover:bg-foreground-muted",
          )}
        />
      ))}
    </div>
  );
}

export {
  Carousel,
  CarouselContent,
  CarouselDots,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
  useCarousel,
};
