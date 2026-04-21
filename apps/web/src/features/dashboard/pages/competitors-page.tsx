import { zodResolver } from "@hookform/resolvers/zod";
import { ApiClientError } from "@citetrack/api-client";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@citetrack/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@citetrack/ui/form";
import { Input } from "@citetrack/ui/input";
import { Skeleton } from "@citetrack/ui/skeleton";
import { Link } from "@tanstack/react-router";
import { Plus, Swords } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { CompetitorCard } from "../components/competitor-card";
import { PageHeader } from "../components/page-header";
import {
  useCompetitors,
  useCreateCompetitor,
  useDeleteCompetitor,
} from "../lib/competitors-hooks";
import { useMyWorkspaces } from "../lib/workspaces-hooks";

const competitorFormSchema = z.object({
  name: z.string().min(1, "Name is required"),
  domain: z
    .string()
    .min(3, "Domain is required")
    .regex(/^(?:https?:\/\/)?(?:[\w-]+\.)+[a-z]{2,}(?:\/.*)?$/i, "Enter a valid domain"),
});

type CompetitorFormValues = z.infer<typeof competitorFormSchema>;

const DEFAULT_VALUES: CompetitorFormValues = {
  name: "",
  domain: "",
};

function NoWorkspaceState() {
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <Card className="max-w-sm w-full p-8 flex flex-col items-center gap-4 text-center">
        <Swords className="size-10 text-muted-foreground" />
        <div className="space-y-1">
          <p className="font-medium">No workspace yet</p>
          <p className="text-sm text-muted-foreground">
            Complete onboarding to start tracking competitors.
          </p>
        </div>
        <Link to="/onboarding" className="text-sm underline underline-offset-4">
          Complete onboarding
        </Link>
      </Card>
    </div>
  );
}

function LoadingRows() {
  return (
    <div data-testid="competitor-loading" className="mx-auto max-w-3xl space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <Skeleton key={index} className="h-14 w-full rounded-xl" />
      ))}
    </div>
  );
}

function getCreateErrorMessage(error: unknown): string {
  if (error instanceof ApiClientError && error.status === 409) {
    return "That domain is already tracked";
  }
  if (error instanceof Error && error.message.length > 0) {
    return error.message;
  }
  return "Failed to add competitor";
}

export function CompetitorsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [pendingRemove, setPendingRemove] = useState<{ id: string; name: string } | null>(null);
  const workspacesQuery = useMyWorkspaces();
  const workspace = workspacesQuery.data?.[0] ?? null;
  const workspaceSlug = workspace?.slug ?? "";
  const competitorsQuery = useCompetitors(workspaceSlug);
  const createCompetitor = useCreateCompetitor(workspaceSlug);
  const deleteCompetitor = useDeleteCompetitor(workspaceSlug);

  const form = useForm<CompetitorFormValues>({
    resolver: zodResolver(competitorFormSchema),
    defaultValues: DEFAULT_VALUES,
  });

  const competitors = competitorsQuery.data?.items ?? [];
  const degraded = competitorsQuery.data?.degraded ?? null;

  function handleDialogChange(nextOpen: boolean) {
    setIsDialogOpen(nextOpen);
    if (!nextOpen) {
      form.reset(DEFAULT_VALUES);
      setSubmitError(null);
    }
  }

  async function handleCreate(values: CompetitorFormValues) {
    setSubmitError(null);
    try {
      await createCompetitor.mutateAsync(values);
      handleDialogChange(false);
    } catch (error) {
      setSubmitError(getCreateErrorMessage(error));
    }
  }

  function requestRemove(id: string, name: string) {
    setPendingRemove({ id, name });
  }

  async function confirmRemove() {
    if (!pendingRemove) return;
    const { id } = pendingRemove;
    setPendingRemove(null);
    await deleteCompetitor.mutateAsync(id);
  }

  return (
    <>
      <PageHeader
        title="Competitors"
        actions={
          workspaceSlug ? (
            <Button type="button" onClick={() => handleDialogChange(true)}>
              <Plus className="size-4" />
              Add competitor
            </Button>
          ) : undefined
        }
      />
      <main className="flex-1 overflow-auto p-6">
        {workspacesQuery.isPending ? (
          <LoadingRows />
        ) : workspacesQuery.error ? (
          <div className="mx-auto max-w-3xl">
            <Alert variant="error">Failed to load workspaces: {workspacesQuery.error.message}</Alert>
          </div>
        ) : !workspaceSlug ? (
          <NoWorkspaceState />
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {competitorsQuery.isPending ? <LoadingRows /> : null}

            {competitorsQuery.error ? (
              <Alert variant="error">
                Failed to load competitors: {competitorsQuery.error.message}
              </Alert>
            ) : null}

            {degraded ? <Alert variant="warning">{degraded.message}</Alert> : null}

            {!competitorsQuery.isPending && !competitorsQuery.error && competitors.length === 0 ? (
              <Card className="items-center gap-6 p-10 text-center">
                <Swords className="size-12 text-muted-foreground" />
                <div className="space-y-2">
                  <h2 className="text-base font-medium">No competitors yet</h2>
                  <p className="mx-auto max-w-md text-sm text-muted-foreground">
                    Track up to 20 competitors to compare visibility. Add them one by one or run
                    research during onboarding.
                  </p>
                </div>
                <Button type="button" onClick={() => handleDialogChange(true)}>
                  <Plus className="size-4" />
                  Add your first competitor
                </Button>
              </Card>
            ) : null}

            {!competitorsQuery.isPending && !competitorsQuery.error && competitors.length > 0 ? (
              <Card className="gap-0 py-0">
                {competitors.map((competitor, index) => (
                  <CompetitorCard
                    key={competitor.id}
                    competitor={competitor}
                    isLast={index === competitors.length - 1}
                    isRemoving={deleteCompetitor.isPending && deleteCompetitor.variables === competitor.id}
                    onRemove={(item) => {
                      requestRemove(item.id, item.name);
                    }}
                  />
                ))}
              </Card>
            ) : null}
          </div>
        )}
      </main>

      <Dialog open={isDialogOpen} onOpenChange={handleDialogChange}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add competitor</DialogTitle>
            <DialogDescription>
              Add one domain to compare your workspace visibility against it.
            </DialogDescription>
          </DialogHeader>

          <Form {...form}>
            <form className="space-y-4" onSubmit={form.handleSubmit(handleCreate)}>
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Example Inc." {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="domain"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Domain</FormLabel>
                    <FormControl>
                      <Input placeholder="example.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {submitError ? <Alert variant="error">{submitError}</Alert> : null}

              <DialogFooter>
                <Button type="button" variant="ghost" onClick={() => handleDialogChange(false)}>
                  Cancel
                </Button>
                <Button type="submit" isLoading={createCompetitor.isPending}>
                  Add competitor
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <Dialog open={pendingRemove !== null} onOpenChange={(open) => !open && setPendingRemove(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove competitor</DialogTitle>
            <DialogDescription>
              {pendingRemove
                ? `Remove ${pendingRemove.name} from tracking? This does not delete past scan data.`
                : ""}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setPendingRemove(null)}>
              Cancel
            </Button>
            <Button
              type="button"
              variant="destructive"
              onClick={() => {
                void confirmRemove();
              }}
              isLoading={deleteCompetitor.isPending}
            >
              Remove
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
