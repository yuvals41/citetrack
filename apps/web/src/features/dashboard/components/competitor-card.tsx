import { Button } from "@citetrack/ui/button";
import { Trash2 } from "lucide-react";
import type { CompetitorRecord } from "@citetrack/api-client";

interface CompetitorCardProps {
  competitor: CompetitorRecord;
  isLast: boolean;
  onRemove: (competitor: CompetitorRecord) => void;
  isRemoving?: boolean;
}

export function CompetitorCard({
  competitor,
  isLast,
  onRemove,
  isRemoving = false,
}: CompetitorCardProps) {
  return (
    <div
      className={[
        "flex min-h-14 items-center justify-between px-4 py-3 transition-colors hover:bg-muted/30",
        isLast ? "" : "border-b",
      ].join(" ")}
    >
      <div className="min-w-0">
        <p className="font-medium">{competitor.name}</p>
        <p className="text-sm text-muted-foreground">{competitor.domain}</p>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label={`Remove ${competitor.name}`}
        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
        isLoading={isRemoving}
        loadingText=""
        onClick={() => onRemove(competitor)}
      >
        {!isRemoving ? <Trash2 className="size-4" /> : null}
      </Button>
    </div>
  );
}
