---
name: playwright-e2e
description: "E2E test automation with Playwright for end-to-end browser testing. Covers desktop-frontend and applicationserver testing patterns."
license: MIT
metadata:
  author: solara-ai
  version: "1.0"
---

# Playwright E2E Testing Skill

Guide for writing end-to-end tests using Playwright for desktop-frontend and applicationserver.

## When to Use

- Testing critical user journeys (auth, payments, content generation)
- Validating UI interactions with real backend responses
- API integration testing with JWT authentication
- Cross-browser compatibility testing
- Verifying WebSocket real-time updates

## Quick Start

```bash
cd repos/e2eautomation

# Install Playwright and browsers
npx playwright install --with-deps

# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/auth/signin.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Debug mode with inspector
npx playwright test --debug
```

## Test Structure

```
repos/e2eautomation/
├── tests/
│   ├── core/                    # Shared infrastructure
│   │   ├── fixtures/            # Test fixtures
│   │   ├── factories/           # Test data factories
│   │   ├── page-objects/        # Page Object Models
│   │   └── services/            # API service wrappers
│   ├── e2e/                     # E2E test specs
│   │   ├── admin/               # Admin panel tests
│   │   ├── api/                 # API integration tests
│   │   ├── auth/                # Authentication tests
│   │   └── journeys/            # User journey tests
│   ├── helpers/                 # Utility helpers
│   ├── utils/                   # Auth, DB utilities
│   └── fixtures.ts              # Global fixtures
├── playwright.config.ts         # Main configuration
└── .auth/                       # Stored auth state
```

## Examples

### Basic Page Test

```typescript
import { test, expect } from '../../core/fixtures';

test.describe('Login Page', () => {
  test.use({ storageState: undefined }); // Fresh session

  test('displays login form elements', async ({ appLoginPage }) => {
    await appLoginPage.goto();
    await expect(appLoginPage.emailInput).toBeVisible();
    await expect(appLoginPage.loginButton).toBeVisible();
  });
});
```

### API Test with Authentication

```typescript
import { test as base, expect, APIRequestContext, request } from '@playwright/test';

const test = base.extend<{ apiRequest: APIRequestContext }>({
  apiRequest: async ({}, use) => {
    const ctx = await request.newContext({
      baseURL: process.env.API_BASE_URL || 'http://localhost:38888',
      extraHTTPHeaders: { 'Content-Type': 'application/json' },
    });
    await use(ctx);
    await ctx.dispose();
  },
});

test('protected endpoint requires valid JWT', async ({ apiRequest }) => {
  const loginRes = await apiRequest.post('/api/auth/login', {
    data: { username: TEST_EMAIL, password: TEST_PASSWORD },
  });
  const { data } = await loginRes.json();

  const userRes = await apiRequest.get('/api/auth/user', {
    headers: { Authorization: `Bearer ${data.token}` },
  });
  expect(userRes.ok()).toBeTruthy();
});
```

### Waiting for API Response (No Sleep!)

```typescript
test('waits for async operation', async ({ page }) => {
  await page.goto('/processing');
  
  // GOOD: Poll until condition is met
  await expect(async () => {
    const status = await page.locator('[data-testid="status"]').textContent();
    expect(status).toBe('Complete');
  }).toPass({ timeout: 30000 });

  // GOOD: Wait for specific network response
  const responsePromise = page.waitForResponse(
    resp => resp.url().includes('/api/status') && resp.status() === 200
  );
  await page.click('[data-testid="refresh"]');
  await responsePromise;

  // BAD: Never use arbitrary sleeps!
  // await page.waitForTimeout(5000); // DON'T DO THIS
});
```

### Using Fixtures

```typescript
export const test = baseTest.extend<{ config: TestConfig; createUser: TestUser }>({
  config: async ({}, use) => {
    await use({
      userEmail: process.env.USER_EMAIL,
      baseURL: process.env.BASE_URL || 'http://localhost:4200',
    });
  },
  createUser: async ({ page }, use) => {
    const user = await createTestUser();
    await use(user);
    await deleteTestUser(user.id); // Cleanup
  },
});
```

## Best Practices

### Deterministic Waits (No Sleeps)

```typescript
// Poll API/DB for state changes
await expect(async () => {
  const dbResult = await queryDatabase('SELECT status FROM jobs WHERE id = $1', [jobId]);
  expect(dbResult.status).toBe('completed');
}).toPass({ timeout: 60000, intervals: [1000, 2000, 5000] });

// Wait for specific element state
await expect(page.locator('[data-testid="result"]')).toBeVisible();
```

### Correlation ID Tracing

```typescript
test('traces request through system', async ({ apiRequest }) => {
  const correlationId = `e2e-${Date.now()}`;
  const response = await apiRequest.post('/api/content/generate', {
    headers: { 'X-Correlation-ID': correlationId },
    data: { prompt: 'Test content' },
  });
  expect(response.headers()['x-correlation-id']).toBe(correlationId);
});
```

### Real Authentication (No Bypass)

```typescript
async function getAuthToken(apiRequest: APIRequestContext): Promise<string> {
  const response = await apiRequest.post('/api/auth/login', {
    data: { username: TEST_EMAIL, password: TEST_PASSWORD },
  });
  const { data } = await response.json();
  if (data.type === 'otp') test.skip(true, 'OTP required - use demo account');
  return data.token;
}

// Reuse auth state across tests
test.use({ storageState: '.auth/user.json' });
```

## Guidelines

1. **One behavior per test** - Keep tests focused and atomic
2. **Use Page Objects** - Extend `BasePage` for all page interactions
3. **Prefer data-testid** - Use `[data-testid="..."]` selectors
4. **Setup via API, test via UI** - Fast setup, meaningful validation
5. **Clean up test data** - Use fixtures with teardown
6. **No hardcoded waits** - Use Playwright's auto-waiting or explicit polls
7. **Capture artifacts** - Screenshots and traces on failure

## Commands

```bash
npx playwright test                                    # Run all tests
npx playwright test --project=api                      # Run specific project
npx playwright test --ui                               # UI mode
npx playwright test --headed                           # Visible browser
npx playwright test path/to/test.spec.ts --debug       # Debug single test
npx playwright codegen http://localhost:4200           # Generate test code
npx playwright show-report                             # View HTML report
```

## Reference Files

- **Main Config**: `repos/e2eautomation/playwright.config.ts`
- **Fixtures**: `repos/e2eautomation/tests/fixtures.ts`
- **Base Page**: `repos/e2eautomation/tests/core/page-objects/base.page.ts`
- **Best Practices**: `repos/e2eautomation/tests/e2e/examples/best-practices.spec.ts`
- **API Tests**: `repos/e2eautomation/tests/e2e/api/api-auth-integration.spec.ts`
- **Auth Setup**: `repos/e2eautomation/tests/auth.setup.ts`
- **User Factory**: `repos/e2eautomation/tests/core/factories/user.factory.ts`
