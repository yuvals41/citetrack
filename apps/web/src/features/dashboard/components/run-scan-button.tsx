import { Button } from "@citetrack/ui/button";
import { Loader2, Play } from "lucide-react";
import { useRunScan } from "../lib/scan-hooks";
import { useMyWorkspaces } from "../lib/workspaces-hooks";

export function RunScanButton() {
  const workspacesQuery = useMyWorkspaces();
  const workspaceSlug = workspacesQuery.data?.[0]?.slug ?? null;
  const runScan = useRunScan();

  const disabled = !workspaceSlug || runScan.isPending;

  const handleClick = () => {
    if (!workspaceSlug) return;
    runScan.mutate({ workspaceSlug });
  };

  return (
    <Button
      type="button"
      size="sm"
      onClick={handleClick}
      disabled={disabled}
    >
      {runScan.isPending ? <Loader2 className="animate-spin" /> : <Play />}
      {runScan.isPending ? "Scanning…" : "Run scan"}
    </Button>
  );
}
