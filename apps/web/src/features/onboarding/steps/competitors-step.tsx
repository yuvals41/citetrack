import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@citetrack/ui/button";
import { Input } from "@citetrack/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@citetrack/ui/form";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import { useFieldArray, useForm } from "react-hook-form";
import { z } from "zod";
import { onboardingSchema } from "../lib/schema";

const competitorsStepSchema = z.object({
  competitors: onboardingSchema.shape.competitors,
});
type CompetitorsStepValues = z.infer<typeof competitorsStepSchema>;
type CompetitorItem = CompetitorsStepValues["competitors"][number];

interface CompetitorsStepProps {
  onNext: (competitors: CompetitorItem[]) => void;
  onBack: () => void;
  initial?: CompetitorItem[];
}

export function CompetitorsStep({
  onNext,
  onBack,
  initial,
}: CompetitorsStepProps) {
  const form = useForm<CompetitorsStepValues>({
    resolver: zodResolver(competitorsStepSchema),
    defaultValues: { competitors: initial ?? [] },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: "competitors",
  });

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-base font-medium">Who are your top competitors?</h2>
        <p className="text-sm text-muted-foreground">
          We'll benchmark your visibility against theirs. Add up to 5.
        </p>
      </div>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit((values) => onNext(values.competitors))}
          className="space-y-4"
        >
          <div className="space-y-3">
            {fields.map((field, index) => (
              <div key={field.id} className="flex gap-2 items-start">
                <FormField
                  control={form.control}
                  name={`competitors.${index}.name`}
                  render={({ field: f }) => (
                    <FormItem className="flex-1">
                      {index === 0 && <FormLabel>Name</FormLabel>}
                      <FormControl>
                        <Input placeholder="Competitor Inc." {...f} />
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
                      {index === 0 && <FormLabel>Domain</FormLabel>}
                      <FormControl>
                        <Input placeholder="competitor.com" {...f} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <button
                  type="button"
                  onClick={() => remove(index)}
                  aria-label="Remove competitor"
                  className={`flex h-10 w-10 shrink-0 items-center justify-center text-muted-foreground transition-colors hover:text-foreground ${index === 0 ? "mt-8" : "mt-0"}`}
                >
                  <Trash2 className="size-4" />
                </button>
              </div>
            ))}
          </div>

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
            <Button type="submit">Continue</Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
