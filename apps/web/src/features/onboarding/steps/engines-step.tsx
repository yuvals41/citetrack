import { zodResolver } from "@hookform/resolvers/zod";
import { AI_PROVIDERS } from "@citetrack/config";
import { Button } from "@citetrack/ui/button";
import { cn } from "@citetrack/ui/cn";
import { ArrowLeft } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import * as z from "zod";
import { onboardingSchema } from "../lib/schema";

const enginesStepSchema = z.object({
  engines: onboardingSchema.shape.engines,
});
type EnginesStepValues = z.infer<typeof enginesStepSchema>;
type Engine = EnginesStepValues["engines"][number];

const ALL_ENGINES: Engine[] = [...AI_PROVIDERS];

const ENGINE_OPTIONS: {
  value: Engine;
  label: string;
  provider: string;
  icon: string;
  iconClassName?: string;
}[] = [
  {
    value: "chatgpt",
    label: "ChatGPT",
    provider: "OpenAI",
    icon: "/engines/openai.svg",
    iconClassName: "h-7 w-7",
  },
  {
    value: "claude",
    label: "Claude",
    provider: "Anthropic",
    icon: "/engines/anthropic.svg",
  },
  { value: "perplexity", label: "Perplexity", provider: "Perplexity AI", icon: "/engines/perplexity.svg" },
  {
    value: "gemini",
    label: "Google Gemini",
    provider: "Google",
    icon: "/engines/google.svg",
  },
  { value: "grok", label: "xAI Grok", provider: "xAI", icon: "/engines/xai.svg" },
  {
    value: "google_ai_overview",
    label: "AI Overviews",
    provider: "Google Search",
    icon: "/engines/google_ai_overview.svg",
  },
];

interface EnginesStepProps {
  onNext: (engines: Engine[]) => void;
  onBack: () => void;
  initial?: Engine[];
}

export function EnginesStep({ onNext, onBack, initial }: EnginesStepProps) {
  const form = useForm<EnginesStepValues>({
    resolver: zodResolver(enginesStepSchema),
    defaultValues: { engines: initial ?? ALL_ENGINES },
  });

  return (
    <div data-testid="onboarding-step-3" className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-base font-medium">
          Which AI engines should we track?
        </h2>
        <p className="text-sm text-muted-foreground">
          We'll run your prompts through the engines you select. You can change
          this later.
        </p>
      </div>
      <form
        onSubmit={form.handleSubmit((values) => onNext(values.engines))}
        className="space-y-6"
      >
        <Controller
          control={form.control}
          name="engines"
          render={({ field, fieldState }) => (
            <div className="space-y-2">
              <div className="grid grid-cols-2 gap-3">
                {ENGINE_OPTIONS.map((engine) => {
                  const checked = field.value.includes(engine.value);
                  return (
                      <label
                        key={engine.value}
                        data-testid={`onboarding-engine-option-${engine.value}`}
                        className={cn(
                        "flex cursor-pointer items-center gap-3 rounded-lg p-4 ring-1 ring-foreground/10 transition-colors hover:bg-muted/50",
                        "has-[:checked]:bg-muted has-[:checked]:ring-foreground/30",
                      )}
                    >
                        <input
                          data-testid={`onboarding-engine-checkbox-${engine.value}`}
                          type="checkbox"
                          className="sr-only"
                        checked={checked}
                        onChange={(e) => {
                          const next = e.target.checked
                            ? [...field.value, engine.value]
                            : field.value.filter((v) => v !== engine.value);
                          field.onChange(next);
                        }}
                      />
                      <img
                        src={engine.icon}
                        alt=""
                        aria-hidden="true"
                        className={cn(
                          "shrink-0 select-none",
                          engine.iconClassName ?? "h-6 w-6",
                        )}
                        draggable={false}
                      />
                      <div className="flex flex-col gap-0.5">
                        <span className="text-sm font-medium leading-none">
                          {engine.label}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {engine.provider}
                        </span>
                      </div>
                    </label>
                  );
                })}
              </div>
              {fieldState.error && (
                <p className="text-xs text-destructive">
                  {fieldState.error.message}
                </p>
              )}
            </div>
          )}
        />
        <div className="flex justify-between pt-2">
            <Button data-testid="onboarding-step-3-back" type="button" variant="ghost" onClick={onBack}>
              <ArrowLeft />
              Back
            </Button>
            <Button data-testid="onboarding-step-3-finish" type="submit">Finish setup</Button>
          </div>
        </form>
      </div>
  );
}
