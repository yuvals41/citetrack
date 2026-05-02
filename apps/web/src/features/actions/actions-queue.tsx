import type { ActionItem } from "@citetrack/api-client";
import { Card, CardContent, CardHeader, CardTitle } from "@citetrack/ui/card";

const PRIORITY_CLASSES: Record<string, string> = {
  high: "bg-foreground/10 text-foreground",
  medium: "bg-foreground/5 text-foreground/80",
  low: "bg-muted text-muted-foreground",
};

interface ActionsQueueProps {
  actions: ActionItem[];
}

export function ActionsQueue({ actions }: ActionsQueueProps) {
  const topActions = actions.slice(0, 5);

  return (
    <Card data-testid="actions-queue-card">
      <CardHeader>
        <CardTitle>Top actions</CardTitle>
      </CardHeader>
      <CardContent>
        {topActions.length === 0 ? (
          <p className="text-sm text-muted-foreground py-2">No actions yet.</p>
        ) : (
          <ul>
            {topActions.map((action, i) => (
              <li
                key={`${action.action_id}-${i}`}
                className="flex items-center justify-between py-2 border-b last:border-b-0"
              >
                <div className="flex flex-col gap-0.5 min-w-0">
                  <span className="text-sm font-medium truncate">
                    {action.title ?? action.recommendation_code}
                  </span>
                  {typeof action.description === "string" && action.description && (
                    <span className="text-xs text-muted-foreground line-clamp-2">
                      {action.description}
                    </span>
                  )}
                </div>
                {action.priority && (
                  <span
                    className={`text-xs px-2 py-0.5 rounded font-medium shrink-0 ml-3 ${
                      PRIORITY_CLASSES[action.priority] ?? PRIORITY_CLASSES.low
                    }`}
                  >
                    {action.priority}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
