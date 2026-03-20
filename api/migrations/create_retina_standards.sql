-- Migration: Create retina_standards table for the research standards library
-- This table stores curated UX, brand, SEO, performance, and conversion principles
-- from authoritative sources that are injected into Claude analysis prompts.

CREATE TABLE IF NOT EXISTS retina_standards (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  lens TEXT NOT NULL CHECK (lens IN ('performance', 'seo', 'brand', 'experience', 'conversion')),
  category TEXT NOT NULL,
  principle TEXT NOT NULL,
  source TEXT NOT NULL,
  source_url TEXT,
  evaluation_criteria TEXT NOT NULL,
  scoring_guidance TEXT NOT NULL,
  applies_to_cohort BOOLEAN DEFAULT true,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index for fast lens-based queries during analysis
CREATE INDEX IF NOT EXISTS idx_retina_standards_lens
  ON retina_standards(lens) WHERE is_active = true;

-- RLS: all authenticated users can read, only admins/owners can write
ALTER TABLE retina_standards ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Authenticated users can read standards"
  ON retina_standards FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Admins can manage standards"
  ON retina_standards FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role IN ('owner', 'admin')
    )
  );

-- Trigger for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_retina_standards_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER retina_standards_updated_at
  BEFORE UPDATE ON retina_standards
  FOR EACH ROW
  EXECUTE FUNCTION update_retina_standards_updated_at();
