import { zodResolver } from "@hookform/resolvers/zod";
import { Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Card } from "@citetrack/ui/card";
import { Input } from "@citetrack/ui/input";
import { Label } from "@citetrack/ui/label";
import { Skeleton } from "@citetrack/ui/skeleton";
import type { ScanScheduleValue } from "@citetrack/api-client";
import { PageHeader } from "#/features/dashboard/components/page-header";
import { useMyWorkspaces } from "#/features/dashboard/lib/workspaces-hooks";
import { useSettings, useUpdateSettings } from "#/features/dashboard/lib/settings-hooks";

const detailsSchema = z.object({
  name: z.string().min(1, "Workspace name is required").max(255),
});
type DetailsForm = z.infer<typeof detailsSchema>;

const SCHEDULE_OPTIONS: Array<{ value: ScanScheduleValue; label: string; description: string }> = [
  { value: "off", label: "Off", description: "No automatic scans. Run them manually." },
  { value: "daily", label: "Daily", description: "One scan every 24 hours." },
  { value: "weekly", label: "Weekly", description: "One scan every 7 days." },
];

export function SettingsPage() {
  const workspacesQuery = useMyWorkspaces();
  const workspace = workspacesQuery.data?.[0];
  const slug = workspace?.slug ?? null;

  if (workspacesQuery.isPending) {
    return (
      <>
        <PageHeader title="Settings" />
        <main className="flex-1 overflow-auto px-6 py-8">
          <div className="mx-auto max-w-3xl space-y-6">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </main>
      </>
    );
  }

  if (!slug) {
    return (
      <>
        <PageHeader title="Settings" />
        <main className="flex-1 overflow-auto px-6 py-8">
          <Card className="mx-auto max-w-2xl p-8 text-center">
            <h2 className="text-lg font-medium">No workspace yet</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Complete onboarding to configure settings for your workspace.
            </p>
            <Button asChild className="mt-4">
              <Link to="/onboarding">Complete onboarding</Link>
            </Button>
          </Card>
        </main>
      </>
    );
  }

  return <SettingsContent slug={slug} />;
}

function SettingsContent({ slug }: { slug: string }) {
  const settingsQuery = useSettings(slug);
  const update = useUpdateSettings(slug);

  if (settingsQuery.isPending) {
    return (
      <>
        <PageHeader title="Settings" />
        <main className="flex-1 overflow-auto px-6 py-8">
          <div className="mx-auto max-w-3xl space-y-6">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </main>
      </>
    );
  }

  if (settingsQuery.error) {
    return (
      <>
        <PageHeader title="Settings" />
        <main className="flex-1 overflow-auto px-6 py-8">
          <div className="mx-auto max-w-3xl">
            <Alert variant="error">
              Failed to load settings: {settingsQuery.error.message}
            </Alert>
          </div>
        </main>
      </>
    );
  }

  const settings = settingsQuery.data;
  if (!settings) return null;

  return (
    <>
      <PageHeader title="Settings" />
      <main className="flex-1 overflow-auto px-6 py-8">
        <div className="mx-auto max-w-3xl space-y-6">
          {settings.degraded ? (
            <Alert variant="warning">
              {settings.degraded.message ?? `Settings unavailable: ${settings.degraded.reason}`}
            </Alert>
          ) : null}
          <WorkspaceDetailsSection
            initialName={settings.name}
            onSave={(patch) => update.mutateAsync(patch)}
            disabled={update.isPending}
          />
          <ScanScheduleSection
            current={settings.scan_schedule}
            onSave={(schedule) => update.mutateAsync({ scan_schedule: schedule })}
            disabled={update.isPending}
          />
        </div>
      </main>
    </>
  );
}

function WorkspaceDetailsSection({
  initialName,
  onSave,
  disabled,
}: {
  initialName: string;
  onSave: (patch: { name: string }) => Promise<unknown>;
  disabled: boolean;
}) {
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<DetailsForm>({
    resolver: zodResolver(detailsSchema),
    defaultValues: { name: initialName },
  });

  useEffect(() => {
    reset({ name: initialName });
  }, [initialName, reset]);

  const handleSave = handleSubmit(async (values) => {
    await onSave({ name: values.name });
    reset({ name: values.name });
    setSavedMessage("Saved");
    window.setTimeout(() => setSavedMessage(null), 2000);
  });

  return (
    <Card className="p-6">
      <div className="space-y-1">
        <h3 className="text-base font-medium">Workspace details</h3>
        <p className="text-sm text-muted-foreground">
          The name appears throughout the app and in exported reports.
        </p>
      </div>
      <form onSubmit={handleSave} className="mt-4 space-y-4">
        <div className="space-y-2">
          <Label htmlFor="settings-workspace-name">Name</Label>
          <Input id="settings-workspace-name" {...register("name")} />
          {errors.name ? (
            <p className="text-xs text-destructive">{errors.name.message}</p>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          <Button type="submit" disabled={!isDirty || isSubmitting || disabled}>
            {isSubmitting ? "Saving…" : "Save changes"}
          </Button>
          {savedMessage ? (
            <span className="text-xs text-muted-foreground">{savedMessage}</span>
          ) : null}
        </div>
      </form>
    </Card>
  );
}

function ScanScheduleSection({
  current,
  onSave,
  disabled,
}: {
  current: ScanScheduleValue;
  onSave: (schedule: ScanScheduleValue) => Promise<unknown>;
  disabled: boolean;
}) {
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  async function handleChange(next: ScanScheduleValue) {
    if (next === current) return;
    await onSave(next);
    setSavedMessage("Saved");
    window.setTimeout(() => setSavedMessage(null), 2000);
  }

  return (
    <Card className="p-6">
      <div className="space-y-1">
        <h3 className="text-base font-medium">Scan schedule</h3>
        <p className="text-sm text-muted-foreground">
          We'll run a full scan on this schedule and notify you when new results land.
        </p>
      </div>
      <div className="mt-4 space-y-2">
        {SCHEDULE_OPTIONS.map((option) => {
          const isActive = option.value === current;
          return (
            <label
              key={option.value}
              className={`flex items-start gap-3 rounded-lg p-4 ring-1 ring-foreground/10 cursor-pointer transition-colors ${isActive ? "bg-muted" : "hover:bg-muted/40"}`}
            >
              <input
                type="radio"
                name="scan-schedule"
                value={option.value}
                checked={isActive}
                disabled={disabled}
                onChange={() => void handleChange(option.value)}
                className="mt-0.5 accent-foreground"
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{option.label}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{option.description}</p>
              </div>
            </label>
          );
        })}
        {savedMessage ? (
          <p className="text-xs text-muted-foreground pt-1">{savedMessage}</p>
        ) : null}
      </div>
    </Card>
  );
}
