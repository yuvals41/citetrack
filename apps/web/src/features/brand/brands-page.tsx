import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { Skeleton } from "@citetrack/ui/skeleton";
import { Link } from "@tanstack/react-router";
import { PageHeader } from "#/components/dashboard-shell/page-header";
import { useCurrentWorkspace } from "#/features/workspaces/queries";
import { BrandEditorCard } from "./brand-editor-card";
import { useUpsertBrand } from "./mutations";
import { BrandNotFoundError, useBrand } from "./queries";

function LoadingState() {
  return (
    <>
      <PageHeader title="Brands" />
      <main className="flex-1 overflow-auto px-6 py-8">
        <div data-testid="brand-loading" className="mx-auto max-w-3xl">
          <Card className="p-6 shadow-none">
            <Skeleton className="h-6 w-28" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-32" />
          </Card>
        </div>
      </main>
    </>
  );
}

export function BrandsPage() {
  const { workspace, isPending, error } = useCurrentWorkspace();
  const workspaceSlug = workspace?.slug ?? null;

  if (isPending) {
    return <LoadingState />;
  }

  if (error) {
    return (
      <>
        <PageHeader title="Brands" />
        <main className="flex-1 overflow-auto px-6 py-8">
          <div className="mx-auto max-w-3xl">
            <Alert variant="error">Failed to load workspaces: {error.message}</Alert>
          </div>
        </main>
      </>
    );
  }

  if (!workspaceSlug) {
    return (
      <>
        <PageHeader title="Brands" />
        <main className="flex-1 overflow-auto px-6 py-8">
          <Card className="mx-auto max-w-2xl p-8 text-center shadow-none">
            <h2 className="text-lg font-medium">No workspace yet</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Complete onboarding to set up the brand your workspace tracks.
            </p>
            <Button asChild className="mt-4">
              <Link to="/onboarding">Complete onboarding</Link>
            </Button>
          </Card>
        </main>
      </>
    );
  }

  return <BrandsContent workspaceSlug={workspaceSlug} />;
}

function BrandsContent({ workspaceSlug }: { workspaceSlug: string }) {
  const brandQuery = useBrand(workspaceSlug);
  const upsertBrand = useUpsertBrand(workspaceSlug);

  if (brandQuery.isPending) {
    return <LoadingState />;
  }

  const isNotFound = brandQuery.error instanceof BrandNotFoundError;

  if (brandQuery.error && !isNotFound) {
    return (
      <>
        <PageHeader title="Brands" />
        <main className="flex-1 overflow-auto px-6 py-8">
          <div className="mx-auto max-w-3xl">
            <Alert variant="error">Failed to load brand: {brandQuery.error.message}</Alert>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Brands" />
      <main className="flex-1 overflow-auto px-6 py-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {brandQuery.data?.degraded ? (
            <Alert variant="warning">{brandQuery.data.degraded.message}</Alert>
          ) : null}
          <BrandEditorCard
            brand={brandQuery.data ?? null}
            mode={isNotFound ? "create" : "edit"}
            isSaving={upsertBrand.isPending}
            onSave={(input) => upsertBrand.mutateAsync(input)}
          />
        </div>
      </main>
    </>
  );
}
