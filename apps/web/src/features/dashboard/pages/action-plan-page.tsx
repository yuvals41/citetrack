import { isDegraded } from "@citetrack/api-client";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { Skeleton } from "@citetrack/ui/skeleton";
import { Lightbulb, RefreshCw } from "lucide-react";
import { ActionCard } from "../components/action-card";
import { PageHeader } from "../components/page-header";
import { useSnapshotActions } from "../lib/api-hooks";
import { useMyWorkspaces } from "../lib/workspaces-hooks";

export function ActionPlanPage() {
  const workspacesQuery = useMyWorkspaces();
  const workspaceSlug = workspacesQuery.data?.[0]?.slug ?? null;
  const actions = useSnapshotActions(workspaceSlug);

  const actionsData = actions.data && !isDegraded(actions.data) ? actions.data : null;
  const actionsDegraded =
    actions.data && isDegraded(actions.data) ? actions.data.degraded : null;

  return (
    <>
      <PageHeader
        title="Action Plan"
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => { void actions.refetch(); }}
            disabled={actions.isFetching}
          >
            <RefreshCw />
            Refresh
          </Button>
        }
      />
      <main className="flex-1 overflow-auto p-6">
        <div className="max-w-4xl mx-auto">
          {actions.isPending ? (
            <div data-testid="loading-skeletons" className="space-y-3">
              <Skeleton className="h-24 w-full rounded-xl" />
              <Skeleton className="h-24 w-full rounded-xl" />
              <Skeleton className="h-24 w-full rounded-xl" />
            </div>
          ) : actions.error ? (
            <Alert variant="error">
              Failed to load action plan: {actions.error.message}
            </Alert>
          ) : actionsDegraded ? (
            <Alert variant="warning">
              {actionsDegraded.message || actionsDegraded.reason}
            </Alert>
          ) : actionsData && actionsData.items.length === 0 ? (
            <Card className="p-10 flex flex-col items-center gap-6 text-center">
              <Lightbulb className="size-12 text-muted-foreground" />
              <div className="space-y-2">
                <h2 className="text-base font-medium">No recommendations yet</h2>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  Run a scan to get personalized action items based on your visibility data.
                </p>
              </div>
              <Button disabled title="Coming soon">
                Run scan
              </Button>
            </Card>
          ) : actionsData ? (
            <div className="space-y-3">
              {actionsData.items.map((item) => (
                <ActionCard
                  key={item.action_id}
                  ruleCode={item.recommendation_code}
                  title={item.title}
                  reason={item.description}
                  priority={item.priority}
                />
              ))}
            </div>
          ) : null}
        </div>
      </main>
    </>
  );
}
