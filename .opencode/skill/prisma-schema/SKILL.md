---
name: prisma-schema
description: |
  Guide for managing Prisma database schema in Citetrack. Covers documenting schema changes,
  proposing new fields/relations/indexes, and understanding the migration workflow.
  Trigger phrases: "database schema", "Prisma model", "add column", "add field", "migration",
  "database change", "schema update", "new table", "add relation", "add index", "prisma schema"
license: MIT
metadata:
  author: solara-ai
  version: "1.0"
---

# Prisma Schema Management Skill

This skill helps developers understand and document Prisma schema changes for the Citetrack project.

## When to Use This Skill

- Adding new fields to existing models
- Creating new database models/tables
- Adding relations between models
- Creating indexes for query optimization
- Documenting schema changes for the user to migrate
- Understanding the shared schema architecture (TypeScript + Python)

## CRITICAL: What You Can and Cannot Do

### CAN Do

- **Document proposed changes** with clear TODO comments in code
- **Update application code** to use new/existing fields
- **Generate Prisma client** after schema changes: `npx prisma generate`
- **View current schema** and understand the data model
- **Propose indexes** based on query patterns
- **Add documentation comments** (`///`) to schema files

### CANNOT Do

- **Create migrations** - User handles this via `python create_migration.py`
- **Run `prisma migrate`** commands - Requires production sync first
- **Modify schema.prisma directly** without user approval for migrations
- **Run `prisma db push`** - Only for prototyping, never in shared environments

## Schema Location and Commands

### Directory Structure

```
prisma/
├── prisma/
│   └── schema/           # Schema files live here
│       ├── schema.prisma # Main schema file
│       └── *.prisma      # Additional schema files
├── create_migration.py   # Python CLI for migrations
└── package.json
```

### CRITICAL: Command Execution Location

**ALL Prisma commands MUST run from `prisma/` root directory!**

```bash
# CORRECT - Run from prisma/
cd prisma && npx prisma generate
cd prisma && npx prisma db pull
cd prisma && npx prisma studio

# WRONG - Will fail!
cd prisma/prisma && npx prisma generate        # NO!
cd prisma/prisma/schema && npx prisma db pull  # NO!
```

## How to Propose Schema Changes

When schema changes are needed, follow this documentation format:

### 1. Notify the User

```markdown
**Schema changes needed for this feature:**

| Table | Change | Field/Index | Type | Notes |
|-------|--------|-------------|------|-------|
| User | Add column | subscriptionTier | String? | Nullable, stores tier name |
| User | Add column | subscriptionExpiresAt | DateTime? | Nullable |
| User | Add index | @@index([subscriptionTier]) | - | Query optimization |

I will implement the code changes. You will need to create the migration.
```

### 2. Document in Code with TODO Comments

```typescript
// TODO: Migration needed - Add to User model:
// - subscriptionTier: String?
// - subscriptionExpiresAt: DateTime?
// - @@index([subscriptionTier])
//
// After migration, remove this TODO and update the following code:

interface UserWithSubscription {
  // These fields require migration
  subscriptionTier?: string;
  subscriptionExpiresAt?: Date;
}
```

## Examples

### Adding a New Field

**Proposed schema change:**
```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String?
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  
  /// User's subscription tier (free, pro, enterprise)
  subscriptionTier String? @map("subscription_tier")
  
  /// When the subscription expires
  subscriptionExpiresAt DateTime? @map("subscription_expires_at")
}
```

**Code documentation:**
```typescript
// TODO: Migration required
// Model: User
// Add: subscriptionTier String? @map("subscription_tier")
// Add: subscriptionExpiresAt DateTime? @map("subscription_expires_at")
```

### Adding a Relation

**Proposed schema change:**
```prisma
model Post {
  id        String   @id @default(cuid())
  title     String
  authorId  String   @map("author_id")
  
  /// The user who created this post
  author    User     @relation(fields: [authorId], references: [id], onDelete: Cascade)
  
  @@index([authorId])
}

model User {
  id    String @id @default(cuid())
  posts Post[]
}
```

**Code documentation:**
```typescript
// TODO: Migration required
// Model: Post
// Add: authorId String @map("author_id")
// Add: author User @relation(fields: [authorId], references: [id], onDelete: Cascade)
// Add: @@index([authorId])
//
// Model: User
// Add: posts Post[]
```

### Adding an Index

**Proposed schema change:**
```prisma
model ContentItem {
  id        String   @id @default(cuid())
  status    String
  createdAt DateTime @default(now())
  userId    String   @map("user_id")
  
  /// Composite index for filtering user content by status
  @@index([userId, status])
  
  /// Index for date-based queries
  @@index([createdAt])
}
```

## Guidelines

### Always

- Use `@map()` for snake_case database column names
- Use `@@map()` for snake_case table names
- Include `createdAt` and `updatedAt` on all models
- Use `@default(cuid())` or `@default(uuid())` for IDs
- Add `///` documentation comments for non-obvious fields
- Consider `onDelete` behavior for relations (Cascade, SetNull, Restrict)

### Ask First

- Adding nullable vs required fields (impacts existing data)
- Cascade delete behavior (can cause data loss)
- Removing fields (data migration may be needed)
- Changing field types (requires data transformation)

### Never

- Create migrations without user approval
- Run `prisma migrate` commands directly
- Use `prisma db push` in shared environments
- Remove fields without explicit permission
- Change primary key strategies on existing tables

## Useful Commands

```bash
# Generate Prisma client after schema changes
cd prisma && npx prisma generate

# View schema in browser UI
cd prisma && npx prisma studio

# Pull current database schema (sync local with DB)
cd prisma && npx prisma db pull

# Check migration status
cd prisma && npx prisma migrate status

# Format schema file
cd prisma && npx prisma format
```

## User Migration Process (Reference Only)

The user handles migrations with this workflow:

```bash
# 1. Sync with production database
scripts/database/sync-database-universal.sh

# 2. Create migration via Python CLI
cd prisma
python create_migration.py --name add_subscription_fields

# 3. Test on staging branch
git checkout staging
git push
# Verify migrations pass in QA environment

# 4. Merge to master
git checkout master
git merge staging
git push
```

## Reference Files

- **Main Schema**: `prisma/prisma/schema/schema.prisma`
- **Migration CLI**: `prisma/create_migration.py`
- **Migration History**: `prisma/migrations/`
- **Database Sync Script**: `scripts/database/sync-database-universal.sh`
- **Prisma Client (TS)**: `@solaraai/prisma-client` (AWS CodeArtifact)

## Related Documentation

- `docs/40_Decisions/` - ADRs for schema design decisions
- `docs/50_Standards/` - Database naming conventions
- `AGENTS.md` Section 7 - Database Operations & Prisma Migrations
