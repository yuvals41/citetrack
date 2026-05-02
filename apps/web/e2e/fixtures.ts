import { expect, test as base } from "@playwright/test";

type ErrorFixtures = {
  consoleErrors: string[];
};

export const test = base.extend<ErrorFixtures>({
  consoleErrors: async ({ page }, use) => {
    const errors: string[] = [];

    const handleConsole = (message: { type(): string; text(): string }) => {
      if (message.type() === "error") {
        errors.push(message.text());
      }
    };

    const handlePageError = (error: Error) => {
      errors.push(`pageerror: ${error.message}`);
    };

    page.on("console", handleConsole);
    page.on("pageerror", handlePageError);

    await use(errors);

    page.off("console", handleConsole);
    page.off("pageerror", handlePageError);
  },
});

export function expectNoConsoleErrors(consoleErrors: string[]) {
  expect(consoleErrors, consoleErrors.join("\n") || "No console errors captured").toEqual([]);
}

export { expect };
