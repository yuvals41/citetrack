import { useState } from "react";
import type { AIResponseItem } from "@citetrack/api-client";
import { Badge } from "@citetrack/ui/badge";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";

export interface ResponseCardProps {
  item: AIResponseItem;
}

const STATUS_LABELS: Record<AIResponseItem["mention_type"], string> = {
  cited: "cited",
  mentioned: "mentioned",
  not_mentioned: "not mentioned",
};

function renderStatusBadge(item: AIResponseItem) {
  if (item.mention_type === "cited") {
    return <Badge variant="default">{STATUS_LABELS[item.mention_type]}</Badge>;
  }

  return (
    <Badge
      variant="outline"
      className={item.mention_type === "not_mentioned" ? "border-foreground/15 text-muted-foreground" : undefined}
    >
      {STATUS_LABELS[item.mention_type]}
    </Badge>
  );
}

export function ResponseCard({ item }: ResponseCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card className="rounded-xl border border-foreground/10 p-4">
      <div className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <Badge variant="outline" className="shrink-0">
              {item.provider}
            </Badge>
            <span className="truncate text-xs text-muted-foreground">· {item.model}</span>
          </div>
          {renderStatusBadge(item)}
        </div>

        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">Q: {item.prompt_text}</p>
          <p className="line-clamp-1 text-sm">{item.excerpt}</p>
        </div>

        {isExpanded ? (
          <div className="space-y-4">
            <div className="rounded-lg bg-muted/40 p-4 text-sm leading-relaxed whitespace-pre-wrap ring-1 ring-foreground/10">
              {item.response_text}
            </div>

            {item.citations.length > 0 ? (
              <div className="space-y-2 text-sm text-muted-foreground">
                <p className="font-medium text-foreground">Citations:</p>
                <ul className="space-y-1">
                  {item.citations.map((citation) => (
                    <li key={`${item.id}-${citation.url}`}>
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 hover:underline"
                      >
                        <span>{citation.domain || citation.url}</span>
                        <ExternalLink className="size-3" />
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {item.position !== null ? (
              <p className="text-sm text-muted-foreground">Position: #{item.position}</p>
            ) : null}

            {item.sentiment ? (
              <p className="text-sm text-muted-foreground">Sentiment: {item.sentiment}</p>
            ) : null}

            <div className="flex justify-end">
              <Button variant="ghost" size="sm" onClick={() => setIsExpanded(false)}>
                <ChevronUp className="size-4" />
                Hide
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex justify-end">
            <Button variant="ghost" size="sm" onClick={() => setIsExpanded(true)}>
              <ChevronDown className="size-4" />
              Show response
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
}
