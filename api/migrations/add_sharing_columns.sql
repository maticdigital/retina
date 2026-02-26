-- Migration: Add project sharing columns
-- Purpose: Enable password-protected public sharing of project reports.
--
-- share_token:         Short UUID used in the public share URL (e.g. /share/<token>).
--                      Nullable — only populated when sharing has been enabled at least once.
--                      Unique so lookups by token are fast and unambiguous.
--
-- share_password_hash: Bcrypt hash of the password required to view the shared report.
--                      Nullable — null means sharing is disabled or no password set yet.
--
-- is_shared:           Boolean flag controlling whether the project is currently publicly
--                      accessible via its share link. Defaults to false.

-- ── Add columns ─────────────────────────────────────────────────────────────

ALTER TABLE projects ADD COLUMN IF NOT EXISTS share_token TEXT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS share_password_hash TEXT;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_shared BOOLEAN NOT NULL DEFAULT false;

-- ── Unique index on share_token for fast public lookups ─────────────────────

CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_share_token
  ON projects (share_token)
  WHERE share_token IS NOT NULL;

-- ── RLS policy for anonymous/public access to shared projects ───────────────
-- Allows unauthenticated users to SELECT a project row ONLY when:
--   1. is_shared = true  (sharing is enabled)
--   2. The query filters by share_token (the token must match)
--
-- The service-role client bypasses RLS entirely, so this policy only affects
-- requests made with the anon key (i.e. the public share viewer endpoint).

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY shared_project_public_read
  ON projects
  FOR SELECT
  TO anon
  USING (
    is_shared = true
    AND share_token IS NOT NULL
  );
