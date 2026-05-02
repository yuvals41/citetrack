import type { PromptRecord } from "@citetrack/api-client";
import { Badge } from "@citetrack/ui/badge";
import { Card } from "@citetrack/ui/card";

const CATEGORY_LABELS: Record<string, string> = {
  buying_intent: "Buying Intent",
  comparison: "Comparison",
  recommendation: "Recommendation",
  informational: "Informational",
};

interface PromptCardProps {
  prompt: PromptRecord;
}

export function PromptCard({ prompt }: PromptCardProps) {
  const categoryLabel = CATEGORY_LABELS[prompt.category ?? ""] ?? prompt.category ?? "Other";

  return (
    <Card className="p-5 space-y-3">
      <Badge variant="outline">{categoryLabel}</Badge>
      <p className="text-sm leading-relaxed">{prompt.template}</p>
      {prompt.ai_search_volume != null && (
        <p className="text-xs text-muted-foreground">AI search volume: {prompt.ai_search_volume}</p>
      )}
    </Card>
  );
}
