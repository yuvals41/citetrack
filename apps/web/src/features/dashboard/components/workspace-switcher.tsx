import { ChevronsUpDown } from "lucide-react";
import { Button } from "@citetrack/ui/button";
import { Skeleton } from "@citetrack/ui/skeleton";
import { useMyWorkspaces } from "../lib/workspaces-hooks";

function initial(name: string | undefined | null): string {
  if (!name) return "?";
  const trimmed = name.trim();
  return trimmed.length > 0 ? trimmed[0]!.toUpperCase() : "?";
}

export function WorkspaceSwitcher() {
  const workspacesQuery = useMyWorkspaces();
  const workspace = workspacesQuery.data?.[0] ?? null;

  if (workspacesQuery.isPending) {
    return (
      <div className="flex items-center gap-2 h-10 px-2">
        <Skeleton className="size-6 rounded-md" />
        <Skeleton className="h-4 w-24" />
      </div>
    );
  }

  const name = workspace?.name ?? "No workspace";

  return (
    <Button
      variant="ghost"
      className="w-full justify-start gap-2 h-10 px-2 font-medium"
      disabled={!workspace}
    >
      <div className="size-6 rounded-md bg-foreground text-background flex items-center justify-center text-xs font-semibold">
        {initial(name)}
      </div>
      <span className="truncate">{name}</span>
      <ChevronsUpDown className="ml-auto size-4 text-muted-foreground" />
    </Button>
  );
}
