import { useEffect, useRef, useState } from "react";
import { Button } from "@citetrack/ui/button";
import { Skeleton } from "@citetrack/ui/skeleton";
import { ChevronsUpDown } from "lucide-react";
import { useMyWorkspaces } from "./queries";

function initial(name: string | undefined | null): string {
  if (!name) return "?";
  const trimmed = name.trim();
  return trimmed.length > 0 ? trimmed.charAt(0).toUpperCase() : "?";
}

export function WorkspaceSwitcher() {
  const workspacesQuery = useMyWorkspaces();
  const workspaces = workspacesQuery.data ?? [];
  const workspace = workspaces[0] ?? null;
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

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
    <div ref={rootRef} className="relative">
      <Button
        type="button"
        variant="ghost"
        data-testid="workspace-switcher-trigger"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        className="w-full justify-start gap-2 h-10 px-2 font-medium"
        disabled={!workspace}
        onClick={() => {
          if (workspace) {
            setIsOpen((current) => !current);
          }
        }}
      >
        <div className="size-6 rounded-md bg-foreground text-background flex items-center justify-center text-xs font-semibold">
          {initial(name)}
        </div>
        <span className="truncate">{name}</span>
        <ChevronsUpDown className="ml-auto size-4 text-muted-foreground" />
      </Button>

      {isOpen ? (
        <div
          role="menu"
          data-testid="workspace-switcher-menu"
          className="mt-2 rounded-xl border bg-background p-2 shadow-sm"
        >
          <div className="space-y-1">
            {workspaces.map((item, index) => {
              const isCurrent = index === 0;
              return (
                <button
                  key={item.id}
                  type="button"
                  role="menuitem"
                  data-testid={`workspace-switcher-item-${item.slug}`}
                  aria-current={isCurrent ? "true" : undefined}
                  className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm hover:bg-muted"
                  onClick={() => setIsOpen(false)}
                >
                  <span className="truncate">{item.name}</span>
                  <span className="text-xs text-muted-foreground">{isCurrent ? "Current" : "Preview"}</span>
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
