import { zodResolver } from "@hookform/resolvers/zod";
import { Alert } from "@citetrack/ui/alert";
import { Button } from "@citetrack/ui/button";
import { Input } from "@citetrack/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormMessage,
} from "@citetrack/ui/form";
import { ArrowLeft, Loader2, Plus, RotateCw, Trash2 } from "lucide-react";
import { useEffect, useRef } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import * as z from "zod";
import type { OnboardingCompetitor } from "../lib/schema";
import { onboardingSchema } from "../lib/schema";

export type ResearchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; competitors: OnboardingCompetitor[] }
  | { status: "degraded"; reason: string; message?: string }
  | { status: "error"; message: string };

const competitorsStepSchema = z.object({
  competitors: onboardingSchema.shape.competitors,
});
type CompetitorsStepValues = z.infer<typeof competitorsStepSchema>;

interface CompetitorsStepProps {
  onNext: (competitors: OnboardingCompetitor[]) => void;
  onBack: () => void;
  initial?: OnboardingCompetitor[];
  researchState?: ResearchState;
  onResearchAgain?: () => void | Promise<void>;
}

export function CompetitorsStep({
  onNext,
  onBack,
  initial,
  researchState = { status: "idle" },
  onResearchAgain,
}: CompetitorsStepProps) {
  const form = useForm<CompetitorsStepValues>({
    resolver: zodResolver(competitorsStepSchema),
    defaultValues: { competitors: initial ?? [] },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "competitors",
  });

  const appliedResearchRef = useRef<ResearchState | null>(null);

  useEffect(() => {
    if (
      researchState.status === "success" &&
      researchState.competitors.length > 0 &&
      fields.length === 0 &&
      appliedResearchRef.current !== researchState
    ) {
      form.reset({ competitors: researchState.competitors });
      appliedResearchRef.current = researchState;
    }
  }, [researchState, fields.length, form]);

  const isLoading = researchState.status === "loading";

  const handleRunAgain = () => {
    if (!onResearchAgain) return;
    appliedResearchRef.current = researchState;
    form.reset({ competitors: [] });
    void onResearchAgain();
  };

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-base font-medium">Who are your top competitors?</h2>
        <p className="text-sm text-muted-foreground">
          We'll benchmark your visibility against theirs. Add up to 5.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          Finding your competitors...
        </div>
      )}

      {researchState.status === "success" && researchState.competitors.length === 0 && (
        <Alert variant="warning">
          We couldn't find competitors automatically for this domain. Add yours below.
        </Alert>
      )}

      {researchState.status === "success" && researchState.competitors.length > 0 && (
        <p className="text-sm text-muted-foreground">
          We found these — edit or add more below.
        </p>
      )}

      {researchState.status === "degraded" && (
        <Alert variant="warning">
          {researchState.message ?? `Auto-research is unavailable (${researchState.reason}). Add competitors manually below.`}
        </Alert>
      )}

      {researchState.status === "error" && (
        <Alert variant="error">
          Research failed: {researchState.message}. You can still add competitors manually.
        </Alert>
      )}

      {onResearchAgain &&
        (researchState.status === "success" || researchState.status === "error") && (
          <div className="flex">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleRunAgain}
            >
              <RotateCw />
              Run research again
            </Button>
          </div>
        )}

      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => onNext(values.competitors))}
          className="space-y-4"
        >
          {fields.length > 0 && (
            <div className="space-y-2">
              <div className="flex gap-2 items-end text-sm font-medium">
                <div className="flex-1">Name</div>
                <div className="flex-1">Domain</div>
                <div className="w-10 shrink-0" aria-hidden="true" />
              </div>
              <div className="space-y-2">
                {fields.map((field, index) => (
                  <div key={field.id} className="flex gap-2 items-start">
                    <FormField
                      control={form.control}
                      name={`competitors.${index}.name`}
                      render={({ field: f }) => (
                        <FormItem className="flex-1">
                          <FormControl>
                            <Input placeholder="Competitor Inc." aria-label="Name" {...f} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name={`competitors.${index}.domain`}
                      render={({ field: f }) => (
                        <FormItem className="flex-1">
                          <FormControl>
                            <Input placeholder="competitor.com" aria-label="Domain" {...f} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <button
                      type="button"
                      onClick={() => remove(index)}
                      aria-label="Remove competitor"
                      className="flex h-10 w-10 shrink-0 items-center justify-center text-muted-foreground transition-colors hover:text-foreground"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {fields.length < 5 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => append({ name: "", domain: "" })}
              className="w-full"
            >
              <Plus />
              Add competitor
            </Button>
          )}

          <div className="flex justify-between pt-2">
            <Button type="button" variant="ghost" onClick={onBack}>
              <ArrowLeft />
              Back
            </Button>
            <Button type="submit" disabled={isLoading}>
              Continue
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
