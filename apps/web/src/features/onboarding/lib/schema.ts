import * as z from "zod";

export const onboardingSchema = z.object({
  brand: z.object({
    name: z.string().min(1, "Required").max(255),
    domain: z
      .string()
      .min(3, "Required")
      .max(255)
      .regex(
        /^(?:https?:\/\/)?(?:[\w-]+\.)+[a-z]{2,}(?:\/.*)?$/i,
        "Enter a valid domain (e.g. example.com)",
      ),
  }),
  competitors: z
    .array(
      z.object({
        name: z.string().min(1),
        domain: z.string().min(3),
      }),
    )
    .max(5, "Up to 5 competitors"),
  engines: z
    .array(z.enum(["openai", "anthropic", "perplexity", "google", "xai"]))
    .min(1, "Pick at least one"),
});

export type OnboardingData = z.infer<typeof onboardingSchema>;
