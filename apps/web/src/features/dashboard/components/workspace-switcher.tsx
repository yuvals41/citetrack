import { ChevronsUpDown } from "lucide-react";
import { Button } from "@citetrack/ui/button";

function getActiveWorkspaceOrFetchFromApiWhenMultiWorkspaceLaunches() {
  return { name: "Citetrack", initial: "C" };
}

export function WorkspaceSwitcher() {
  const workspace = getActiveWorkspaceOrFetchFromApiWhenMultiWorkspaceLaunches();

  return (
    <Button
      variant="ghost"
      className="w-full justify-start gap-2 h-10 px-2 font-medium"
    >
      <div className="size-6 rounded-md bg-foreground text-background flex items-center justify-center text-xs font-semibold">
        {workspace.initial}
      </div>
      <span className="truncate">{workspace.name}</span>
      <ChevronsUpDown className="ml-auto size-4 text-muted-foreground" />
    </Button>
  );
}
