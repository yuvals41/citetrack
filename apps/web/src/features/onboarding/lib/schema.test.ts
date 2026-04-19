import { describe, expect, it } from "vitest";
import { onboardingSchema } from "./schema";

const validPayload = {
  brand: {
    name: "Acme Corp",
    domain: "example.com",
  },
  competitors: [
    {
      name: "Rival",
      domain: "rival.com",
    },
  ],
  engines: ["openai", "google"] as const,
};

describe("onboardingSchema", () => {
  it("accepts a valid payload", () => {
    expect(onboardingSchema.safeParse(validPayload).success).toBe(true);
  });

  it.each([
    "not a url",
    "localhost",
    "x.y",
    "",
    "http://example..com",
  ])("rejects invalid domain %s", (domain) => {
    const result = onboardingSchema.safeParse({
      ...validPayload,
      brand: { ...validPayload.brand, domain },
    });

    expect(result.success).toBe(false);
  });

  it.each([
    "example.com",
    "app.example.co.uk",
    "https://example.com",
    "my-brand.io",
  ])("accepts valid domain %s", (domain) => {
    expect(
      onboardingSchema.safeParse({
        ...validPayload,
        brand: { ...validPayload.brand, domain },
      }).success,
    ).toBe(true);
  });

  it("rejects an empty brand name", () => {
    const result = onboardingSchema.safeParse({
      ...validPayload,
      brand: { ...validPayload.brand, name: "" },
    });

    expect(result.success).toBe(false);
  });

  it("rejects a brand name longer than 255 characters", () => {
    const result = onboardingSchema.safeParse({
      ...validPayload,
      brand: { ...validPayload.brand, name: "a".repeat(256) },
    });

    expect(result.success).toBe(false);
  });

  it("accepts a normal brand name", () => {
    expect(
      onboardingSchema.safeParse({
        ...validPayload,
        brand: { ...validPayload.brand, name: "Acme Corp" },
      }).success,
    ).toBe(true);
  });

  it("accepts up to five competitors", () => {
    const result = onboardingSchema.safeParse({
      ...validPayload,
      competitors: Array.from({ length: 5 }, (_, index) => ({
        name: `Competitor ${index + 1}`,
        domain: `competitor-${index + 1}.com`,
      })),
    });

    expect(result.success).toBe(true);
  });

  it("rejects six competitors", () => {
    const result = onboardingSchema.safeParse({
      ...validPayload,
      competitors: Array.from({ length: 6 }, (_, index) => ({
        name: `Competitor ${index + 1}`,
        domain: `competitor-${index + 1}.com`,
      })),
    });

    expect(result.success).toBe(false);
  });

  it("accepts zero competitors", () => {
    expect(
      onboardingSchema.safeParse({
        ...validPayload,
        competitors: [],
      }).success,
    ).toBe(true);
  });

  it("rejects empty engines", () => {
    const result = onboardingSchema.safeParse({
      ...validPayload,
      engines: [],
    });

    expect(result.success).toBe(false);
  });

  it("accepts a single engine", () => {
    expect(
      onboardingSchema.safeParse({
        ...validPayload,
        engines: ["openai"],
      }).success,
    ).toBe(true);
  });

  it("accepts all supported engines", () => {
    expect(
      onboardingSchema.safeParse({
        ...validPayload,
        engines: ["openai", "anthropic", "perplexity", "google", "xai", "google_ai_overview"],
      }).success,
    ).toBe(true);
  });

  it("rejects an unknown engine", () => {
    const result = onboardingSchema.safeParse({
      ...validPayload,
      engines: ["chatgpt-plus"],
    });

    expect(result.success).toBe(false);
  });
});
