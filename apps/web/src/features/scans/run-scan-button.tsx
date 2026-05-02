import { Button } from "@citetrack/ui/button";
import { Loader2, Play } from "lucide-react";
import { useCurrentWorkspace } from "#/features/workspaces/queries";
import { useRunScan } from "./mutations";

export function RunScanButton() {
  const { workspace } = useCurrentWorkspace();
  const workspaceSlug = workspace?.slug ?? null;
  const runScan = useRunScan();

  const disabled = !workspaceSlug || runScan.isPending;

  const handleClick = () => {
    if (!workspaceSlug) return;
    runScan.mutate({ workspaceSlug });
  };

  return (
    <Button type="button" size="sm" onClick={handleClick} disabled={disabled}>
      {runScan.isPending ? <Loader2 className="animate-spin" /> : <Play />}
      {runScan.isPending ? "Scanning…" : "Run scan"}
    </Button>
  );
}
