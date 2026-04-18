# @citetrack/ui

Shared UI primitives and utilities for Citetrack AI apps. Shadcn-style components and helper functions.

## Install

Already installed as a workspace dependency. Nothing to do.

```bash
# In consumer app's package.json (auto-linked by Bun workspaces)
"@citetrack/ui": "workspace:*"
```

## Usage

```tsx
import { cn } from "@citetrack/ui";

<button className={cn("px-4 py-2", isActive && "bg-primary")} />
```

## What's Here

| Export | Purpose |
|---|---|
| `cn(...classes)` | Merge Tailwind classes with `clsx` + `twMerge` |

## Roadmap

Shadcn primitives to add (copy from [ui.shadcn.com](https://ui.shadcn.com)):

- [ ] Button
- [ ] Input
- [ ] Dialog
- [ ] Dropdown Menu
- [ ] Toast
- [ ] Card
- [ ] Table
- [ ] Skeleton
- [ ] Select
- [ ] Tooltip

Each component lives in its own file under `src/components/` and is re-exported from `src/index.ts`.

## Adding a Component

```bash
# Copy from shadcn docs into packages/ui/src/components/
# Add export to packages/ui/src/index.ts:

export { Button } from "./components/button";
```

## Peer Dependencies

- `react` ≥ 19
- `react-dom` ≥ 19
- Tailwind CSS (configured in consumer app)

## Why Not Use Shadcn CLI?

Shadcn CLI copies components into each consumer. We prefer shared workspace package because:
1. Single source of truth across web / admin / future apps
2. Single upgrade path
3. Easier to enforce brand consistency
