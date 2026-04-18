import * as TabsPrimitive from "@radix-ui/react-tabs";
import {
  type ComponentPropsWithoutRef,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { cn } from "./cn";

// ─── Visited-tabs context ─────────────────────────────────────────────────────
// Tracks which tab values have ever been the active tab. `TabsContent` with
// `keepMounted` reads this to decide whether to force-mount its subtree so
// React state, form values, and in-flight fetches survive tab switches.

const VisitedTabsContext = createContext<Set<string> | null>(null);

// ─── Tabs root ────────────────────────────────────────────────────────────────

type TabsProps = ComponentPropsWithoutRef<typeof TabsPrimitive.Root>;

function Tabs({ value, defaultValue, onValueChange, children, ...props }: TabsProps) {
  // Seed the visited set with whichever value is active at first render so
  // the initially-selected tab is treated as "visited" from frame 0 and its
  // content never unmounts when `keepMounted` is set on it.
  const [visited, setVisited] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    const seed = value ?? defaultValue;
    if (typeof seed === "string") {
      initial.add(seed);
    }
    return initial;
  });

  const markVisited = useCallback((next: string) => {
    setVisited((prev) => {
      if (prev.has(next)) {
        return prev;
      }
      const copy = new Set(prev);
      copy.add(next);
      return copy;
    });
  }, []);

  // Controlled mode: consumer may swap `value` directly without routing
  // through `onValueChange`. Still counts as a visit.
  useEffect(() => {
    if (typeof value === "string") {
      markVisited(value);
    }
  }, [value, markVisited]);

  const handleValueChange = useCallback(
    (next: string) => {
      markVisited(next);
      onValueChange?.(next);
    },
    [markVisited, onValueChange],
  );

  return (
    <VisitedTabsContext.Provider value={visited}>
      <TabsPrimitive.Root
        value={value}
        defaultValue={defaultValue}
        onValueChange={handleValueChange}
        {...props}
      >
        {children}
      </TabsPrimitive.Root>
    </VisitedTabsContext.Provider>
  );
}

// ─── Tabs list with sliding underline indicator ───────────────────────────────

function TabsList({
  className,
  children,
  ...props
}: ComponentPropsWithoutRef<typeof TabsPrimitive.List>) {
  const listRef = useRef<HTMLDivElement>(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0, ready: false });

  const updateIndicator = useCallback(() => {
    const list = listRef.current;
    if (!list) {
      return;
    }
    const active = list.querySelector<HTMLElement>("[data-state='active']");
    if (!active) {
      return;
    }
    setIndicator({
      left: active.offsetLeft,
      width: active.offsetWidth,
      ready: true,
    });
  }, []);

  useEffect(() => {
    const list = listRef.current;
    if (!list) {
      return;
    }

    // Initial measurement
    updateIndicator();

    // Watch for data-state attribute changes on children (tab switches)
    const mo = new MutationObserver(updateIndicator);
    mo.observe(list, { attributes: true, attributeFilter: ["data-state"], subtree: true });

    // Watch for size changes (resize, font load, etc.)
    const ro = new ResizeObserver(updateIndicator);
    ro.observe(list);

    return () => {
      mo.disconnect();
      ro.disconnect();
    };
  }, [updateIndicator]);

  return (
    <TabsPrimitive.List
      ref={listRef}
      className={cn("relative inline-flex items-center gap-0", className)}
      {...props}
    >
      {children}
      {/* Sliding underline indicator */}
      <span
        className="pointer-events-none absolute bottom-0 h-0.5 bg-foreground transition-all duration-300 ease-out"
        style={{
          left: indicator.left,
          width: indicator.width,
          opacity: indicator.ready ? 1 : 0,
        }}
      />
    </TabsPrimitive.List>
  );
}

// ─── Trigger ──────────────────────────────────────────────────────────────────

function TabsTrigger({
  className,
  ...props
}: ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        "relative inline-flex items-center justify-center whitespace-nowrap px-4 pb-2.5 pt-2 text-sm font-medium transition-colors",
        "text-foreground-muted",
        "hover:text-foreground",
        "focus-visible:outline-none",
        "disabled:pointer-events-none disabled:opacity-50",
        "data-[state=active]:text-foreground",
        className,
      )}
      {...props}
    />
  );
}

// ─── Content ──────────────────────────────────────────────────────────────────

interface TabsContentProps extends ComponentPropsWithoutRef<typeof TabsPrimitive.Content> {
  /**
   * Keep this content mounted after the first time its tab becomes active.
   *
   * - Before first activation: not in the DOM (default lazy behavior).
   * - On first activation: mounts normally.
   * - On subsequent switches away: stays mounted via Radix's `forceMount`,
   *   hidden via the HTML `hidden` attribute. React state, form values, and
   *   in-flight effects survive.
   *
   * Use for tabs with expensive fetches, form state, or scroll position that
   * should persist. Skip it for cheap presentational tabs. Default: `false`.
   *
   * Note: `hidden` attribute is equivalent to `display: none`, so scroll
   * position *inside* the content is lost on hide. React state is preserved.
   */
  keepMounted?: boolean;
}

function TabsContent({ className, value, keepMounted = false, ...props }: TabsContentProps) {
  const visited = useContext(VisitedTabsContext);
  const hasBeenVisited =
    keepMounted && typeof value === "string" && visited !== null && visited.has(value);

  return (
    <TabsPrimitive.Content
      value={value}
      forceMount={hasBeenVisited ? true : undefined}
      className={cn("mt-4 focus-visible:outline-none", className)}
      {...props}
    />
  );
}

export type { TabsContentProps, TabsProps };
export { Tabs, TabsContent, TabsList, TabsTrigger };
