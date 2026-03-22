-- Open project visibility to all authenticated users (SELECT only).
-- Write operations remain restricted to project creator + admins/owners.

-- ── projects ─────────────────────────────────────────────────────────────────
-- Drop any restrictive SELECT policy that limits by created_by
DROP POLICY IF EXISTS "Users see own projects" ON projects;
DROP POLICY IF EXISTS "users_see_own_projects" ON projects;
DROP POLICY IF EXISTS "Authenticated users can view projects" ON projects;

-- All authenticated users can view all projects
CREATE POLICY "Authenticated users can view all projects"
  ON projects FOR SELECT
  TO authenticated
  USING (true);

-- ── project_data ─────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users see own project_data" ON project_data;
DROP POLICY IF EXISTS "users_see_own_project_data" ON project_data;
DROP POLICY IF EXISTS "Authenticated users can view project_data" ON project_data;

CREATE POLICY "Authenticated users can view all project_data"
  ON project_data FOR SELECT
  TO authenticated
  USING (true);

-- ── analyst_scores ───────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users see own analyst_scores" ON analyst_scores;
DROP POLICY IF EXISTS "users_see_own_analyst_scores" ON analyst_scores;
DROP POLICY IF EXISTS "Authenticated users can view analyst_scores" ON analyst_scores;

CREATE POLICY "Authenticated users can view all analyst_scores"
  ON analyst_scores FOR SELECT
  TO authenticated
  USING (true);

-- ── reports ──────────────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users see own reports" ON reports;
DROP POLICY IF EXISTS "users_see_own_reports" ON reports;
DROP POLICY IF EXISTS "Authenticated users can view reports" ON reports;

CREATE POLICY "Authenticated users can view all reports"
  ON reports FOR SELECT
  TO authenticated
  USING (true);

-- ── recommendations ──────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "Users see own recommendations" ON recommendations;
DROP POLICY IF EXISTS "users_see_own_recommendations" ON recommendations;
DROP POLICY IF EXISTS "Authenticated users can view recommendations" ON recommendations;

CREATE POLICY "Authenticated users can view all recommendations"
  ON recommendations FOR SELECT
  TO authenticated
  USING (true);
