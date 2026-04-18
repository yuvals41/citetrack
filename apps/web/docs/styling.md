# Styling

Tailwind CSS v4 with Citetrack brand tokens. Monochrome (black/white) aesthetic matching the logo.

---

## Tailwind v4 Setup

Uses the Vite plugin (no config file needed):

```ts
// vite.config.ts
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tailwindcss()],
});
```

Classes are auto-scanned from all `.ts`, `.tsx`, `.css` files.

---

## Brand Tokens

Defined in `src/styles.css`:

```css
@import "tailwindcss";

@theme {
  /* Brand colors — monochrome */
  --color-background: #ffffff;
  --color-foreground: #0a0a0a;
  --color-primary: #0a0a0a;
  --color-primary-foreground: #fafafa;
  --color-muted: #f4f4f5;
  --color-muted-foreground: #71717a;
  --color-border: #e4e4e7;
  --color-ring: #0a0a0a;

  /* Typography */
  --font-sans: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", monospace;

  /* Spacing (extends default) */
  --spacing-18: 4.5rem;
  --spacing-128: 32rem;
}

/* Dark mode (inverted for the "cite" side — black background, white text) */
@media (prefers-color-scheme: dark) {
  @theme {
    --color-background: #0a0a0a;
    --color-foreground: #fafafa;
    --color-primary: #fafafa;
    --color-primary-foreground: #0a0a0a;
    --color-muted: #1a1a1a;
    --color-muted-foreground: #a1a1aa;
    --color-border: #27272a;
  }
}
```

Usage:

```tsx
<div className="bg-background text-foreground border border-border">
  <h1 className="text-primary">Citetrack AI</h1>
  <p className="text-muted-foreground">Track how AI cites your brand.</p>
</div>
```

---

## Class Composition

Use `cn()` from `@citetrack/ui` for conditional classes:

```tsx
import { cn } from "@citetrack/ui";

<button
  className={cn(
    "inline-flex items-center rounded-md px-4 py-2 font-medium",
    variant === "primary" && "bg-primary text-primary-foreground",
    variant === "ghost" && "bg-transparent text-foreground hover:bg-muted",
    disabled && "opacity-50 cursor-not-allowed",
    className,  // caller overrides last
  )}
>
  {children}
</button>
```

`cn()` = `clsx()` + `twMerge()` — handles conditionals and resolves conflicting Tailwind classes (e.g. `p-4 p-2` → `p-2`).

---

## Components

### Variants with `class-variance-authority`

```tsx
// src/components/Button.tsx
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@citetrack/ui";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-medium transition-colors",
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-foreground hover:opacity-90",
        ghost: "bg-transparent text-foreground hover:bg-muted",
        outline: "border border-border bg-background hover:bg-muted",
      },
      size: {
        sm: "h-8 px-3 text-sm",
        md: "h-10 px-4",
        lg: "h-12 px-6 text-lg",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({ variant, size, className, ...props }: Props) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}
```

---

## Typography

| Element | Class | Use for |
|---|---|---|
| `h1` | `text-4xl font-bold tracking-tight` | Page titles |
| `h2` | `text-2xl font-semibold` | Section headers |
| `h3` | `text-xl font-semibold` | Subsections |
| `p` | `text-base` | Body text |
| `small` | `text-sm text-muted-foreground` | Captions, meta |
| `code` | `font-mono text-sm rounded bg-muted px-1.5 py-0.5` | Inline code |

---

## Spacing Scale

Stick to Tailwind defaults (`p-1`, `p-2`, `p-4`, `p-6`, `p-8`, `p-12`). Avoid arbitrary values (`p-[17px]`) unless there's a design reason.

**Vertical rhythm** — use `space-y-*` for stacks:

```tsx
<div className="space-y-4">
  <MetricCard />
  <Chart />
  <Table />
</div>
```

---

## Responsive Design

Mobile-first. Breakpoints:

| Prefix | Min width | Typical device |
|---|---|---|
| `(default)` | 0 | Mobile |
| `sm:` | 640px | Large mobile |
| `md:` | 768px | Tablet |
| `lg:` | 1024px | Laptop |
| `xl:` | 1280px | Desktop |
| `2xl:` | 1536px | Large desktop |

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
  {/* Responsive grid */}
</div>
```

---

## Icons

Use [Lucide React](https://lucide.dev):

```tsx
import { Activity, ArrowRight, ChevronDown } from "lucide-react";

<Button>
  View dashboard <ArrowRight className="ml-2 h-4 w-4" />
</Button>
```

Size convention:
- Inline with text: `h-4 w-4` (16px)
- Buttons: `h-4 w-4` or `h-5 w-5` (16-20px)
- Section icons: `h-6 w-6` (24px)
- Hero icons: `h-12 w-12` (48px)

---

## Animations

Use `tailwindcss-animate` for keyframe utilities:

```tsx
<div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
  {/* Fades and slides in on mount */}
</div>
```

Transitions — prefer `transition-colors`, `transition-opacity`, `transition-transform` over `transition-all`.

---

## Accessibility

- **Focus states** — every interactive element has a visible focus ring (`focus:ring-2 focus:ring-ring`)
- **Color contrast** — WCAG AA minimum (Tailwind neutral palette passes)
- **Semantic HTML** — `<button>` not `<div onClick>`, `<nav>`, `<main>`, `<article>`
- **Alt text** — every `<img>` has `alt=""` (decorative) or descriptive text
- **Keyboard nav** — every clickable element works with Enter/Space

---

## Brand Logo

Stored in `public/`:

```
  public/
  ├── logo-dark.svg       # White on black (for dark bg)
  ├── logo-light.svg      # Black on white (for light bg)
  ├── favicon.ico         # 16/32/48 multi-size
  ├── apple-touch-icon.png # 180x180
  └── og-image.png        # 1200x630 social preview
```

Usage:

```tsx
<img src="/logo-dark.svg" alt="Citetrack AI" className="h-8 w-8" />
```
