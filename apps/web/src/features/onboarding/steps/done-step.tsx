import { Button } from "@citetrack/ui/button";
import { Check, Loader2 } from "lucide-react";

interface DoneStepProps {
  submitting: boolean;
  error: string | null;
  onRetry: () => void;
}

export function DoneStep({ submitting, error, onRetry }: DoneStepProps) {
  if (submitting) {
    return (
      <div className="flex flex-col items-center gap-4 py-10">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          Setting up your workspace…
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4 py-4">
        <div className="rounded-lg bg-destructive/5 p-4 ring-1 ring-destructive/30">
          <p className="text-sm font-medium text-destructive">Setup failed</p>
          <p className="mt-1 text-xs text-muted-foreground">{error}</p>
        </div>
        <div className="flex justify-center">
          <Button variant="outline" onClick={onRetry}>
            Try again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 py-10">
      <div className="flex size-12 items-center justify-center rounded-full bg-muted ring-1 ring-foreground/10">
        <Check className="size-6" />
      </div>
      <div className="space-y-1 text-center">
        <p className="font-medium">All set!</p>
        <p className="text-sm text-muted-foreground">
          Redirecting you to your dashboard…
        </p>
      </div>
    </div>
  );
}
