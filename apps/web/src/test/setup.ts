import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

vi.stubEnv("VITE_API_BASE_URL", "http://localhost:8000");
vi.stubEnv("VITE_CLERK_PUBLISHABLE_KEY", "pk_test_citetrack");

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
