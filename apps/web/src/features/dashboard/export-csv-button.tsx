import { Button } from "@citetrack/ui/button";
import { useAuth } from "@clerk/react";
import { Download, Loader2 } from "lucide-react";
import { useState } from "react";
import { useCurrentWorkspace } from "#/features/workspaces/queries";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function ExportCsvButton() {
  const { getToken } = useAuth();
  const { workspace } = useCurrentWorkspace();
  const workspaceSlug = workspace?.slug ?? null;
  const [isDownloading, setIsDownloading] = useState(false);

  const disabled = !workspaceSlug || isDownloading;

  const handleClick = async () => {
    if (!workspaceSlug) return;
    setIsDownloading(true);
    try {
      const token = await getToken();
      const res = await fetch(`${BASE_URL}/api/v1/workspaces/${workspaceSlug}/export.csv`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Export failed: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `citetrack-${workspaceSlug}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <Button type="button" variant="outline" size="sm" onClick={handleClick} disabled={disabled}>
      {isDownloading ? <Loader2 className="animate-spin" /> : <Download />}
      {isDownloading ? "Exporting…" : "Export CSV"}
    </Button>
  );
}
