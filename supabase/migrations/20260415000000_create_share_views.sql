-- Migration: Create share_views table
-- Purpose: Track successful views (password-verified) of publicly shared project reports.
--
-- A row is inserted each time a client submits the correct password to the
-- /shared/{token}/verify endpoint. Used for analytics and outbound
-- notifications (e.g. Slack pings when a share link is viewed).

CREATE TABLE IF NOT EXISTS share_views (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  share_token TEXT,
  viewed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ip_address TEXT,
  user_agent TEXT
);

-- Index for looking up views by project or token
CREATE INDEX IF NOT EXISTS idx_share_views_project_id ON share_views (project_id);
CREATE INDEX IF NOT EXISTS idx_share_views_share_token ON share_views (share_token);

-- RLS: writes happen via service-role key (bypasses RLS); no anon access.
ALTER TABLE share_views ENABLE ROW LEVEL SECURITY;
