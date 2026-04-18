import { AnimatePresence, motion, type Transition } from "motion/react";
import { type ReactNode, useEffect, useRef, useState } from "react";
import { cn } from "./cn";

export type CardStackItem = {
  /** Stable identifier — used as React key. */
  id: string | number;
  /**
   * Card body. Accepts any `ReactNode` — plain text, JSX, an entire custom
   * component, whatever you want to render. The card container fills its
   * slot via `absolute inset-0`, so pass a root element that fills `h-full
   * w-full` if you want edge-to-edge content.
   */
  content: ReactNode;
};

export type CardStackExitVariant =
  | "flick"
  | "alternating-flick"
  | "push-back"
  | "fade"
  | "blur-fade"
  | "dissolve"
  | "whisper";

export interface CardStackProps {
  /** The cards to cycle through. Two or more recommended. */
  items: CardStackItem[];
  /** Auto-advance interval in ms. @default 5000 */
  interval?: number;
  /** Number of cards visible at once (front + peeking cards behind). @default 3 */
  visibleCount?: number;
  /** Pixel offset between stacked cards (cards behind sit lower). @default 18 */
  offset?: number;
  /** Scale step applied to each card further back in the stack. @default 0.05 */
  scaleStep?: number;
  /** Opacity falloff per position behind the front card. @default 0.08 */
  opacityStep?: number;
  /** Pause the auto-rotation externally. */
  paused?: boolean;
  /** Pause the auto-rotation while the cursor is over the stack. @default true */
  pauseOnHover?: boolean;
  /** Extra className on the stack container — use this to size the stack. */
  className?: string;
  /**
   * Exit animation style.
   *
   * - `"flick"` — lift + diagonal tilt, like a thumb flick.
   * - `"alternating-flick"` — flick direction alternates left/right each cycle.
   * - `"push-back"` — card shrinks into the deck then fades.
   * - `"fade"` — pure opacity fade, no movement at all.
   * - `"dissolve"` — tiny scale-down + fade. Barely there.
   * - `"blur-fade"` — fade + gaussian blur. Premium camera-defocus feel.
   * - `"whisper"` — minuscule lift + scale + fade. Nearly imperceptible.
   *
   * @default "flick"
   */
  exitVariant?: CardStackExitVariant;
  /**
   * Resting tilt (in degrees) applied to cards behind the front, alternating
   * ±. The front card is always flat. Set to `0` to disable. @default 2
   */
  restTilt?: number;
  /**
   * Returning card enters at a slight counter-tilt (opposite sign of the
   * most recent exit rotation), then settles to its resting rotation.
   * @default false
   */
  entryCounterTilt?: boolean;
  /** Exit rotation magnitude in degrees (used by rotating variants). @default 8 */
  exitRotate?: number;
  /** Exit x-drift magnitude in pixels (used by drifting variants). @default 40 */
  exitX?: number;
}

type ExitCustom = {
  x: number;
  y: number;
  rotate: number;
  scale: number;
  filter: string;
  transition: Transition;
};

const DEFAULT_EASE: [number, number, number, number] = [0.32, 0, 0.2, 1];
const DEFAULT_DURATION = 0.6;

function baseExit(): ExitCustom {
  return {
    x: 0,
    y: 0,
    rotate: 0,
    scale: 1,
    filter: "blur(0px)",
    transition: { duration: DEFAULT_DURATION, ease: DEFAULT_EASE },
  };
}

function computeExitCustom(
  variant: CardStackExitVariant,
  cycle: number,
  exitRotate: number,
  exitX: number,
): ExitCustom {
  const altSign = cycle % 2 === 0 ? -1 : 1;
  const base = baseExit();

  switch (variant) {
    case "flick":
      return { ...base, y: -260, x: -exitX, rotate: -exitRotate };
    case "alternating-flick":
      return { ...base, y: -260, x: altSign * exitX, rotate: altSign * exitRotate };
    case "push-back":
      return {
        ...base,
        y: 24,
        scale: 0.7,
        transition: { duration: 0.55, ease: [0.4, 0, 0.2, 1] },
      };
    case "fade":
      return {
        ...base,
        transition: { duration: 0.55, ease: [0.4, 0, 0.2, 1] },
      };
    case "blur-fade":
      return {
        ...base,
        scale: 0.98,
        filter: "blur(12px)",
        transition: { duration: 0.6, ease: [0.4, 0, 0.2, 1] },
      };
    case "dissolve":
      return {
        ...base,
        scale: 0.94,
        transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] },
      };
    case "whisper":
      return {
        ...base,
        y: -18,
        scale: 0.97,
        transition: { duration: 0.7, ease: [0.4, 0, 0.2, 1] },
      };
  }
}

/**
 * Auto-rotating stack of cards. On each interval the front card animates
 * away (per `exitVariant`) and silently reappears at the back of the deck
 * while the cards behind promote forward one slot.
 *
 * Pauses automatically while the cursor is over the stack (disable via
 * `pauseOnHover={false}`). Size the stack via `className` on the outer
 * container; each card fills it with `absolute inset-0`.
 */
export function CardStack({
  items,
  interval = 5000,
  visibleCount = 3,
  offset = 18,
  scaleStep = 0.05,
  opacityStep = 0.08,
  paused = false,
  pauseOnHover = true,
  className,
  exitVariant = "flick",
  restTilt = 2,
  entryCounterTilt = false,
  exitRotate = 8,
  exitX = 40,
}: CardStackProps) {
  const [deck, setDeck] = useState<CardStackItem[]>(items);
  const [exitCustom, setExitCustom] = useState<ExitCustom>(() =>
    computeExitCustom(exitVariant, 0, exitRotate, exitX),
  );
  const [hovered, setHovered] = useState(false);
  const deckRef = useRef(deck);
  deckRef.current = deck;
  const rotatingRef = useRef(false);
  const cycleRef = useRef(0);

  // Re-sync if `items` identity changes.
  useEffect(() => {
    setDeck(items);
  }, [items]);

  const effectivelyPaused = paused || (pauseOnHover && hovered);

  useEffect(() => {
    if (effectivelyPaused || items.length < 2) return;

    const tick = () => {
      if (rotatingRef.current) return;
      const current = deckRef.current;
      const front = current[0];
      if (!front) return;
      rotatingRef.current = true;

      cycleRef.current += 1;
      const nextExit = computeExitCustom(exitVariant, cycleRef.current, exitRotate, exitX);
      setExitCustom(nextExit);

      // Phase 1: unmount the front card — AnimatePresence plays its exit,
      // and the cards behind tween forward to their new slots.
      setDeck(current.slice(1));

      // Phase 2: before the exit fully completes, remount the card at the
      // back. It enters at the back slot and fades in, seamlessly.
      window.setTimeout(() => {
        setDeck((prev) => [...prev, front]);
        rotatingRef.current = false;
      }, 400);
    };

    const id = window.setInterval(tick, interval);
    return () => window.clearInterval(id);
  }, [interval, effectivelyPaused, items.length, exitVariant, exitRotate, exitX]);

  const backY = (visibleCount - 1) * offset;
  const backScale = Math.max(0, 1 - scaleStep * (visibleCount - 1));

  const restRotation = (position: number): number => {
    if (!restTilt || position === 0) return 0;
    return position % 2 === 1 ? -restTilt : restTilt;
  };

  // Entry rotation for cards remounting at the back of the deck.
  const backRest = restRotation(Math.max(0, visibleCount - 1));
  const entrySign = exitCustom.rotate === 0 ? 1 : -Math.sign(exitCustom.rotate);
  const entryRotation = entryCounterTilt ? entrySign * exitRotate * 0.4 : backRest;

  return (
    // biome-ignore lint/a11y/noStaticElementInteractions: mouse enter/leave are used purely to pause the auto-rotation; there is no interactive affordance that requires keyboard parity
    <div
      className={cn("relative", className)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <AnimatePresence initial={false} custom={exitCustom}>
        {deck.map((item, position) => {
          const isVisible = position < visibleCount;
          return (
            <motion.div
              key={item.id}
              custom={exitCustom}
              initial={{
                y: backY,
                x: 0,
                rotate: entryRotation,
                scale: backScale,
                opacity: 0,
                filter: "blur(0px)",
              }}
              animate={{
                y: position * offset,
                x: 0,
                rotate: restRotation(position),
                scale: Math.max(0, 1 - position * scaleStep),
                opacity: isVisible ? Math.max(0, 1 - position * opacityStep) : 0,
                filter: "blur(0px)",
                zIndex: deck.length - position,
              }}
              variants={{
                exit: (c: ExitCustom) => ({
                  x: c.x,
                  y: c.y,
                  rotate: c.rotate,
                  scale: c.scale,
                  filter: c.filter,
                  opacity: 0,
                  transition: c.transition,
                }),
              }}
              exit="exit"
              transition={{ duration: 0.55, ease: [0.4, 0, 0.2, 1] }}
              className="absolute inset-0"
              style={{
                transformOrigin: "center center",
                willChange: "transform, opacity",
              }}
            >
              {item.content}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
