function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required for Clerk E2E.`);
  }
  return value;
}

export function hasClerkTestingEnv(): boolean {
  return Boolean(
    process.env.VITE_CLERK_PUBLISHABLE_KEY?.startsWith("pk_test_") &&
      process.env.CLERK_SECRET_KEY?.startsWith("sk_test_") &&
      process.env.E2E_CLERK_USER_EMAIL &&
      process.env.E2E_CLERK_USER_PASSWORD,
  );
}

export function getClerkTestingEnv() {
  return {
    publishableKey: requireEnv("VITE_CLERK_PUBLISHABLE_KEY"),
    secretKey: requireEnv("CLERK_SECRET_KEY"),
    email: requireEnv("E2E_CLERK_USER_EMAIL"),
    password: requireEnv("E2E_CLERK_USER_PASSWORD"),
  };
}
