import type { Finding } from "@citetrack/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@citetrack/ui/card";

const SEVERITY_CLASSES: Record<string, string> = {
  high: "bg-foreground/10 text-foreground",
  medium: "bg-foreground/5 text-foreground/80",
  low: "bg-muted text-muted-foreground",
};

interface FindingsListProps {
  findings: Finding[];
}

export function FindingsList({ findings }: FindingsListProps) {
  return (
    <Card data-testid="findings-list-card">
      <CardHeader>
        <CardTitle>Findings</CardTitle>
      </CardHeader>
      <CardContent>
        {findings.length === 0 ? (
          <p className="text-sm text-muted-foreground py-2">No findings yet.</p>
        ) : (
          <ul>
            {findings.map((finding, i) => (
              <li
                key={`${finding.reason_code}-${i}`}
                className="flex items-center justify-between py-2 border-b last:border-b-0"
              >
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="text-sm font-medium truncate">{finding.reason_code}</span>
                  {typeof finding.message === "string" && finding.message && (
                    <span className="text-xs text-muted-foreground truncate">
                      {finding.message}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <span className="text-sm tabular-nums text-muted-foreground">
                    {finding.count}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-medium ${
                      SEVERITY_CLASSES[finding.severity] ?? SEVERITY_CLASSES.low
                    }`}
                  >
                    {finding.severity}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
