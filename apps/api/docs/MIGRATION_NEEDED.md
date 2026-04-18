# Phase 3d: Schema changes needed

Phase 3d ships authenticated user/workspace endpoints using a temporary file-based stub for user↔workspace ownership at `apps/api/.cache/user_associations.json`.

This keeps the backend working end-to-end today without creating Prisma migrations in this task.

## Required schema changes (user applies)

1. Add a `users` table:
   - `clerk_user_id TEXT PRIMARY KEY`
   - `email TEXT`
   - `created_at TIMESTAMP DEFAULT NOW()`

2. Add a `user_workspaces` junction table:
   - `clerk_user_id TEXT`
   - `workspace_id TEXT`
   - `role TEXT DEFAULT 'owner'`
   - `created_at TIMESTAMP DEFAULT NOW()`
   - `PRIMARY KEY (clerk_user_id, workspace_id)`

3. Backfill:
   - None needed. This is a new feature with no existing ownership data.

## After migrations land

Replace the file-backed methods in `ai_visibility/storage/repositories/user_repo.py` with Prisma calls using the same public interface:

- `add_workspace_to_user(user_id, workspace_slug)`
- `list_workspaces_for_user(user_id)`
- `get_workspace_owner(workspace_slug)`
- `user_owns_workspace(user_id, slug)`

The onboarding metadata currently stored in-process should also move into real workspace/user-owned tables once the schema exists.
