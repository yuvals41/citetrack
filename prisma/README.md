# @citetrack/prisma

Citetrack-owned Prisma schema and generated clients. **Standalone** — no dependency on stanley/solaraai shared schema.

## Layout

```
prisma/
├── prisma/
│   ├── schema/          One file per model (Workspace, Brand, ...)
│   └── migrations/      Squashed init + future migrations
├── scripts/
│   ├── generatepython.sh     Generates client-python/prisma/ (the importable client)
│   ├── generatenodejs.sh     Generates client-node/
│   └── vars.sh               Shared datasource + generator config
├── client-python/       Pip-installable Python package (hatchling)
│   ├── pyproject.toml        name = "citetrack-prisma-client"
│   └── prisma/               Generated client lives here (gitignored)
│       └── __init__.py       Empty placeholder — overwritten on `prisma generate`
└── client-node/         Generated TS client (gitignored, future)
```

## Generate clients

```bash
# From repo root
bash prisma/scripts/generatepython.sh
# bash prisma/scripts/generatenodejs.sh   # if/when the web app needs it
```

## Migrations

The schema is the source of truth. To apply changes against a dev DB:

```bash
cd prisma
npx prisma migrate dev --schema=prisma/schema --name <change-name>
```

The first migration (`20260501000000_init`) was synthesized via `pg_dump` from
the existing `ai_vis_*` tables. Mark it as applied on environments that already
have the tables:

```bash
npx prisma migrate resolve --applied 20260501000000_init --schema=prisma/schema
```

## Why a local package, not a submodule?

Citetrack ships as a single repo. The Prisma client is consumed by `apps/api`
via a workspace path:

```toml
# apps/api/pyproject.toml
[tool.uv.sources]
citetrack-prisma-client = { path = "../prisma/dist/client-python", editable = true }
```

No extra `git submodule update --init` step. Runtime import stays
`from prisma import Prisma` (the generated package name).
