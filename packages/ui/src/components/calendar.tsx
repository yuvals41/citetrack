import { ChevronLeft, ChevronRight } from "lucide-react";
import { DayPicker } from "react-day-picker";
import { cn } from "./cn";

type CalendarProps = React.ComponentProps<typeof DayPicker>;

// Extracted to avoid nested component definition
function CalendarChevron({ orientation }: { orientation?: string }) {
  return orientation === "left" ? (
    <ChevronLeft className="h-4 w-4" />
  ) : (
    <ChevronRight className="h-4 w-4" />
  );
}

/**
 * In react-day-picker v9 the DOM structure is:
 *
 *   .rdp-root
 *     [months]          ← flex row (one entry per month)
 *       <nav>           ← contains both prev + next buttons; sibling to <month>
 *       <div.month>
 *         <div.month_caption>
 *         <table>
 *
 * The nav is NOT inside month_caption, so we make the [months] wrapper
 * `relative` and let nav overlay it absolutely at the top of the first month.
 * Each button is then pinned left/right within that relative container.
 */
function Calendar({ className, classNames, showOutsideDays = true, ...props }: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn("p-3", className)}
      classNames={{
        // months row — relative so nav can be absolutely positioned over it
        months: "relative flex flex-col sm:flex-row gap-4",
        month: "flex flex-col gap-4",
        // caption: just the centred label; buttons come from nav overlay
        month_caption: "flex justify-center items-center h-8",
        caption_label: "text-sm font-medium",
        // nav sits absolutely over the months container, flush with caption height
        nav: "absolute inset-x-0 top-0 flex items-center justify-between pointer-events-none h-8",
        button_previous: cn(
          "pointer-events-auto h-7 w-7 inline-flex items-center justify-center",
          "rounded-sm border border-border bg-background opacity-70 hover:opacity-100",
          "transition-opacity focus:outline-none focus:ring-2 focus:ring-ring",
        ),
        button_next: cn(
          "pointer-events-auto h-7 w-7 inline-flex items-center justify-center",
          "rounded-sm border border-border bg-background opacity-70 hover:opacity-100",
          "transition-opacity focus:outline-none focus:ring-2 focus:ring-ring",
        ),
        month_grid: "w-full border-collapse",
        weekdays: "flex",
        weekday: "text-foreground-muted rounded-sm w-9 font-normal text-[0.8rem] text-center",
        week: "flex w-full mt-2",
        day: [
          "relative p-0 text-center text-sm focus-within:relative focus-within:z-20",
          "[&:has([aria-selected])]:bg-surface",
          "[&:has([aria-selected].day-range-end)]:rounded-r-sm",
          "[&:has([aria-selected].day-outside)]:bg-surface/50",
          "first:[&:has([aria-selected])]:rounded-l-sm",
          "last:[&:has([aria-selected])]:rounded-r-sm",
        ].join(" "),
        day_button: cn(
          "h-9 w-9 rounded-sm p-0 font-normal transition-colors",
          "hover:bg-surface aria-selected:opacity-100",
          "inline-flex items-center justify-center",
        ),
        range_start: "day-range-start",
        range_end: "day-range-end",
        selected:
          "[&>button]:bg-primary [&>button]:text-primary-foreground [&>button]:hover:bg-primary-hover [&>button]:hover:text-primary-foreground [&>button]:focus:bg-primary [&>button]:focus:text-primary-foreground",
        today: "[&>button]:font-semibold [&>button]:underline",
        outside:
          "day-outside text-foreground-placeholder opacity-50 aria-selected:bg-surface/50 aria-selected:text-foreground-placeholder aria-selected:opacity-30",
        disabled:
          "[&>button]:text-foreground-placeholder [&>button]:opacity-50 [&>button]:pointer-events-none",
        range_middle: "aria-selected:bg-surface aria-selected:text-foreground",
        hidden: "invisible",
        ...classNames,
      }}
      components={{ Chevron: CalendarChevron }}
      {...props}
    />
  );
}

export type { CalendarProps };
export { Calendar };
