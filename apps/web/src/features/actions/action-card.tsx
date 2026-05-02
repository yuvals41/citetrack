import { Badge } from "@citetrack/ui/badge";
import { Card } from "@citetrack/ui/card";

export interface ActionCardProps {
  ruleCode: string;
  title: string;
  reason: string;
  priority: "high" | "medium" | "low";
}

const PRIORITY_BORDER: Record<"high" | "medium" | "low", string> = {
  high: "border-foreground",
  medium: "border-foreground/50",
  low: "border-foreground/25",
};

const PRIORITY_LABEL: Record<"high" | "medium" | "low", string> = {
  high: "HIGH",
  medium: "MEDIUM",
  low: "LOW",
};

export function ActionCard({ ruleCode, title, reason, priority }: ActionCardProps) {
  return (
    <Card className={`relative p-5 border-l-[3px] ${PRIORITY_BORDER[priority]}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5 min-w-0 flex-1">
          <span className="text-xs font-mono text-muted-foreground">{ruleCode}</span>
          <p className="text-base font-medium leading-snug">{title}</p>
          <p className="text-sm text-muted-foreground">{reason}</p>
        </div>
        <Badge variant="outline" className="shrink-0 uppercase tracking-wide">
          {PRIORITY_LABEL[priority]}
        </Badge>
      </div>
    </Card>
  );
}
