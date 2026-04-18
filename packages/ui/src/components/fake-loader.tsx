import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "./cn";

interface FakeLoaderStep {
  /** Message displayed during this step */
  text: string;
  /**
   * Duration in milliseconds before advancing to the next step.
   * The last step ignores this — it waits for `isComplete`.
   */
  duration?: number;
}

interface FakeLoaderProps {
  /** Ordered list of loading steps. The last step waits indefinitely for `isComplete`. */
  steps: FakeLoaderStep[];
  /**
   * Signal that the real operation is done. Once `true`:
   * - If remaining steps exist, their durations are overridden to `fastForwardDuration`.
   * - If already on the last step, fires `onComplete` immediately.
   */
  isComplete?: boolean;
  /**
   * Duration (ms) for each remaining step when fast-forwarding after `isComplete`.
   * @default 1500
   */
  fastForwardDuration?: number;
  /** Called after every step has completed and the done state is shown. */
  onComplete?: () => void;
  /**
   * Text shown in the completed state. Set to `null` to skip the completed state entirely
   * (will call `onComplete` immediately).
   * @default "Done"
   */
  completedText?: string | null;
  className?: string;
}

/** Spinning indicator for the active step */
function StepSpinner() {
  return (
    <span
      aria-hidden="true"
      className="inline-block h-4 w-4 shrink-0 animate-spin rounded-full border-2 border-foreground border-t-transparent"
    />
  );
}

/** Animated check icon — draws the stroke on mount */
function StepCheck() {
  return (
    <svg
      className="h-4 w-4 shrink-0 text-foreground"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path
        d="M3.5 8.5 6.5 11.5 12.5 5"
        style={{
          strokeDasharray: 16,
          strokeDashoffset: 0,
          animation: "fake-loader-check-draw 350ms ease-out forwards",
        }}
      />
    </svg>
  );
}

/** Empty circle placeholder for pending steps */
function StepPending() {
  return (
    <span
      aria-hidden="true"
      className="inline-block h-4 w-4 shrink-0 rounded-full border-2 border-foreground/20"
    />
  );
}

type StepState = "done" | "active" | "pending";

function FakeLoader({
  steps,
  isComplete = false,
  fastForwardDuration = 1500,
  onComplete,
  completedText = "Done",
  className,
}: FakeLoaderProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [allDone, setAllDone] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isCompleteRef = useRef(isComplete);
  const hasCalledComplete = useRef(false);

  // Keep ref in sync so timer callbacks see the latest value
  useEffect(() => {
    isCompleteRef.current = isComplete;
  }, [isComplete]);

  const isLastStep = currentIndex >= steps.length - 1;

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  // Fire onComplete exactly once
  const fireComplete = useCallback(() => {
    if (!hasCalledComplete.current) {
      hasCalledComplete.current = true;
      onComplete?.();
    }
  }, [onComplete]);

  // Mark everything done — show the final check, then fire onComplete
  const finalize = useCallback(() => {
    setAllDone(true);
    if (completedText === null) {
      fireComplete();
    } else {
      // Give the last checkmark animation time to play, then fire
      setTimeout(() => {
        fireComplete();
      }, 600);
    }
  }, [completedText, fireComplete]);

  // Schedule the advance from step at `index`
  const scheduleAdvance = useCallback(
    (index: number) => {
      clearTimer();
      const step = steps[index];
      if (!step) {
        return;
      }
      const isLast = index >= steps.length - 1;

      // Last step: only advance to "done" if already complete
      if (isLast) {
        if (isCompleteRef.current) {
          timerRef.current = setTimeout(() => {
            finalize();
          }, 400);
        }
        return;
      }

      // Determine duration: fast-forward if isComplete, otherwise step's own duration
      const duration = isCompleteRef.current ? fastForwardDuration : (step.duration ?? 2000);

      timerRef.current = setTimeout(() => {
        setCurrentIndex(index + 1);
      }, duration);
    },
    [steps, fastForwardDuration, clearTimer, finalize],
  );

  // When index changes, schedule the next advance
  useEffect(() => {
    scheduleAdvance(currentIndex);
  }, [currentIndex, scheduleAdvance]);

  // React to isComplete changing to true
  useEffect(() => {
    if (!isComplete) {
      return;
    }

    if (allDone) {
      return;
    }

    // If already on last step, finalize
    if (isLastStep) {
      clearTimer();
      timerRef.current = setTimeout(() => {
        finalize();
      }, 400);
      return;
    }

    // Otherwise, re-schedule with fast-forward duration
    clearTimer();
    scheduleAdvance(currentIndex);
  }, [isComplete, isLastStep, allDone, currentIndex, clearTimer, scheduleAdvance, finalize]);

  // Cleanup on unmount
  useEffect(() => {
    return () => clearTimer();
  }, [clearTimer]);

  function getStepState(index: number): StepState {
    if (allDone) {
      return "done";
    }
    if (index < currentIndex) {
      return "done";
    }
    if (index === currentIndex) {
      return "active";
    }
    return "pending";
  }

  return (
    <div className={cn("flex flex-col gap-4 text-sm", className)} role="status" aria-live="polite">
      {steps.map((step, index) => {
        const state = getStepState(index);
        return (
          <div
            // biome-ignore lint/suspicious/noArrayIndexKey: key includes state to remount on transitions and replay CSS animation
            key={`${index}-${state}`}
            className={cn("flex items-center gap-3", state === "pending" && "opacity-40")}
          >
            {state === "done" && <StepCheck />}
            {state === "active" && <StepSpinner />}
            {state === "pending" && <StepPending />}
            <span
              className={cn(
                "font-medium",
                state === "active" ? "animate-fake-loader-shimmer" : "text-foreground",
              )}
            >
              {step.text}
            </span>
          </div>
        );
      })}

      {allDone && completedText !== null && (
        <div className="flex items-center gap-3 animate-fake-loader-in pt-1">
          <StepCheck />
          <span className="font-semibold text-foreground">{completedText}</span>
        </div>
      )}
    </div>
  );
}

export type { FakeLoaderProps, FakeLoaderStep };
export { FakeLoader };
