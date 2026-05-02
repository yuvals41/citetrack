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
import { useForm } from "react-hook-form";
import * as z from "zod";
import { onboardingSchema } from "../lib/schema";

const brandStepSchema = onboardingSchema.shape.brand;
type BrandStepValues = z.infer<typeof brandStepSchema>;

interface BrandStepProps {
  onNext: (brand: BrandStepValues) => void;
  initial?: BrandStepValues;
}

export function BrandStep({ onNext, initial }: BrandStepProps) {
  const form = useForm<BrandStepValues>({
    resolver: zodResolver(brandStepSchema),
    defaultValues: initial ?? { name: "", domain: "" },
  });

  return (
    <div data-testid="onboarding-step-1" className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-base font-medium">Your brand</h2>
        <p className="text-sm text-muted-foreground">
          Tell us about the brand you want to track across AI.
        </p>
      </div>
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onNext)}
          className="space-y-4"
          noValidate
        >
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Brand name</FormLabel>
                <FormControl>
                  <Input data-testid="onboarding-step-1-brand-input" placeholder="Acme Inc." {...field} />
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
                <FormLabel>Website</FormLabel>
                <FormControl>
                  <Input data-testid="onboarding-step-1-domain-input" type="text" placeholder="example.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <div className="flex justify-end pt-2">
            <Button data-testid="onboarding-step-1-continue" type="submit">Continue</Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
