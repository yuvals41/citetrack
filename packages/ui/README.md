# @citetrack/ui

Shared UI primitives for Citetrack AI. 48 Shadcn-based components ported from `@solaraai/ui`, rebranded with Citetrack monochrome tokens.

## Install

Workspace-linked. Already installed in `apps/web`.

## Usage

```tsx
import { Button } from "@citetrack/ui/button";
import { Input } from "@citetrack/ui/input";
import { Dialog } from "@citetrack/ui/dialog";
import { cn } from "@citetrack/ui";

<Button variant="default">Click me</Button>
<Input placeholder="Search..." />
```

## Components (48)

**Forms & Inputs**

| Export | From |
|---|---|
| `Button` | `@citetrack/ui/button` |
| `Input` | `@citetrack/ui/input` |
| `Textarea` | `@citetrack/ui/textarea` |
| `Checkbox` | `@citetrack/ui/checkbox` |
| `RadioGroup` | `@citetrack/ui/radio-group` |
| `Switch` | `@citetrack/ui/switch` |
| `Label` | `@citetrack/ui/label` |
| `Select` | `@citetrack/ui/select` |
| `FloatingInput` | `@citetrack/ui/floating-input` |
| `InputOTP` | `@citetrack/ui/input-otp` |
| `PhoneInput` | `@citetrack/ui/phone-input` |
| `ColorPicker` | `@citetrack/ui/color-picker` |
| `Slider` | `@citetrack/ui/slider` |
| `DatePicker` | `@citetrack/ui/date-picker` |
| `DateTimePicker` | `@citetrack/ui/date-time-picker` |
| `TimePicker` | `@citetrack/ui/time-picker` |
| `Calendar` | `@citetrack/ui/calendar` |
| `FileUpload` | `@citetrack/ui/file-upload` |
| `ImageUpload` | `@citetrack/ui/image-upload` |
| `VideoUpload` | `@citetrack/ui/video-upload` |

**Feedback & Status**

| Export | From |
|---|---|
| `Alert` | `@citetrack/ui/alert` |
| `Badge` | `@citetrack/ui/badge` |
| `Tag` | `@citetrack/ui/tag` |
| `Progress` | `@citetrack/ui/progress` |
| `Skeleton` | `@citetrack/ui/skeleton` |
| `Loader` | `@citetrack/ui/loader` |
| `FakeLoader` | `@citetrack/ui/fake-loader` |
| `Toaster` (sonner) | `@citetrack/ui/toast` |

**Overlays**

| Export | From |
|---|---|
| `Dialog` | `@citetrack/ui/dialog` |
| `Drawer` | `@citetrack/ui/drawer` |
| `Modal` | `@citetrack/ui/modal` |
| `Overlay` | `@citetrack/ui/overlay` |
| `Menu` | `@citetrack/ui/menu` |
| `Tooltip` | `@citetrack/ui/tooltip` |
| `InfoTooltip` | `@citetrack/ui/info-tooltip` |
| `Collapsible` | `@citetrack/ui/collapsible` |

**Layout & Navigation**

| Export | From |
|---|---|
| `Tabs` | `@citetrack/ui/tabs` |
| `Divider` | `@citetrack/ui/divider` |
| `BackButton` | `@citetrack/ui/back-button` |
| `CardStack` | `@citetrack/ui/card-stack` |
| `Carousel` | `@citetrack/ui/carousel` |
| `Avatar` | `@citetrack/ui/avatar` |
| `MediaRenderer` | `@citetrack/ui/media-renderer` |
| `ShineBorder` | `@citetrack/ui/shine-border` |

**Utility**

| Export | From |
|---|---|
| `cn()` | `@citetrack/ui` or `@citetrack/ui/cn` |
| `COUNTRIES, resolveCountry` | `@citetrack/ui/countries` |

**Styles (import in app CSS entry):**

```css
@import "@citetrack/ui/tokens.css";
@import "@citetrack/ui/animations.css";
```

## Components NOT Included

Solara-specific components from `@solaraai/ui` that we intentionally did NOT port:

- `credits-bar` — Solara's credit system
- `notifications` panel — Solara-specific
- `pricing-card`, `pricing-table` — Solara pricing
- `integration-card` — Solara integrations
- `sidebar` — Solara nav (rebuild for Citetrack)
- `solara-logo` — their logo (we have our own)
- `chat/` — Solara chat with assistant-ui
- `content-calendar/` — Solara content calendar
- `instagram-preview/`, `facebook-preview/`, `linkedin-preview/`, `tiktok-preview/` — social post mockups
- `mobile/` — Solara mobile-specific flow

## Brand Tokens

See `src/components/tokens.css`. Citetrack is **monochrome black/white** — no purple/gradients/Solara colors. Always use semantic tokens (`bg-background`, `text-foreground`), never hardcoded Tailwind grays.

## Peer Dependencies

- `react` ≥ 19
- `react-dom` ≥ 19
- Tailwind CSS (configured in consumer app)

## Source

Originally from `/home/yuval/Documents/solaraai/platform/packages/node/ui`. Ported April 2026.
