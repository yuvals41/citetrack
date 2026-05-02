import { isDegraded } from "@citetrack/api-client";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { Skeleton } from "@citetrack/ui/skeleton";
import { Lightbulb, RefreshCw } from "lucide-react";
import { PageHeader } from "#/components/dashboard-shell/page-header";
import { RunScanButton } from "#/features/scans/run-scan-button";
import { useCurrentWorkspace } from "#/features/workspaces/queries";
import { ActionCard } from "./action-card";
import { useSnapshotActions } from "./queries";

export function ActionPlanPage() {
  const { workspace } = useCurrentWorkspace();
  const workspaceSlug = workspace?.slug ?? null;
  const actions = useSnapshotActions(workspaceSlug);

  const actionsData = actions.data && !isDegraded(actions.data) ? actions.data : null;
  const actionsDegraded = actions.data && isDegraded(actions.data) ? actions.data.degraded : null;

  return (
    <>
      <PageHeader
        title="Action Plan"
        actions={
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              void actions.refetch();
            }}
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
            <Alert variant="error">Failed to load action plan: {actions.error.message}</Alert>
          ) : actionsDegraded ? (
            <Alert variant="warning">{actionsDegraded.message || actionsDegraded.reason}</Alert>
          ) : actionsData && actionsData.items.length === 0 ? (
            <Card className="p-10 flex flex-col items-center gap-6 text-center">
              <Lightbulb className="size-12 text-muted-foreground" />
              <div className="space-y-2">
                <h2 className="text-base font-medium">No recommendations yet</h2>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  Run a scan to get personalized action items based on your visibility data.
                </p>
              </div>
              <RunScanButton />
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
