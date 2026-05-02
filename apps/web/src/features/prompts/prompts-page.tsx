import { Alert } from "@citetrack/ui/alert";
import { Badge } from "@citetrack/ui/badge";
import { Button } from "@citetrack/ui/button";
import { Skeleton } from "@citetrack/ui/skeleton";
import { Plus } from "lucide-react";
import { PageHeader } from "#/components/dashboard-shell/page-header";
import { PromptCard } from "./prompt-card";
import { usePrompts } from "./queries";

const CATEGORIES = [
  { key: "buying_intent", label: "Buying Intent" },
  { key: "comparison", label: "Comparison" },
  { key: "recommendation", label: "Recommendation" },
  { key: "informational", label: "Informational" },
] as const;

const PROMPT_SKELETON_IDS = [
  "prompt-skeleton-1",
  "prompt-skeleton-2",
  "prompt-skeleton-3",
  "prompt-skeleton-4",
  "prompt-skeleton-5",
  "prompt-skeleton-6",
] as const;

function PromptCardSkeleton() {
  return (
    <output aria-label="Loading prompt" className="p-5 border rounded-xl space-y-3">
      <Skeleton className="h-5 w-28 rounded-full" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
    </output>
  );
}

export function PromptsPage() {
  const { data, isPending, error } = usePrompts();

  return (
    <div className="flex flex-col flex-1 overflow-auto">
      <PageHeader
        title="Prompts"
        actions={
          <Button variant="outline" size="sm" disabled title="Coming soon">
            <Plus className="size-4" />
            Add custom prompt
          </Button>
        }
      />

      <main className="p-6 space-y-6">
        <Alert variant="info" title="These are the questions we ask AI assistants about your brand">
          Each prompt includes your brand name and competitor names automatically. Custom workspace
          prompts appear alongside the defaults.
        </Alert>

        <div className="flex items-center flex-wrap gap-2">
          <span className="text-xs text-muted-foreground mr-2">Categories:</span>
          {CATEGORIES.map(({ key, label }) => (
            <Badge key={key} variant="outline">
              {label}
            </Badge>
          ))}
        </div>

        {isPending ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl">
            {PROMPT_SKELETON_IDS.map((id) => (
              <PromptCardSkeleton key={id} />
            ))}
          </div>
        ) : error ? (
          <Alert variant="error">Failed to load prompts: {error.message}</Alert>
        ) : data?.items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No prompts yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-5xl">
            {data?.items.map((prompt) => (
              <PromptCard key={prompt.id} prompt={prompt} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
