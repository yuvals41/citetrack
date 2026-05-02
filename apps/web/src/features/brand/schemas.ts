import * as z from "zod";

export const brandSchema = z.object({
  name: z.string().trim().min(1, "Brand name is required").max(255),
  domain: z
    .string()
    .trim()
    .min(3, "Domain is required")
    .regex(/^(?:https?:\/\/)?(?:[\w-]+\.)+[a-z]{2,}(?:\/.*)?$/i, "Enter a valid domain"),
  aliases: z.array(z.string().trim().min(1).max(255)).max(10),
});

export type BrandFormValues = z.infer<typeof brandSchema>;
