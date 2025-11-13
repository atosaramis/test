-- Migration: Add columns for comprehensive company research
-- Date: 2025-11-13
-- Description: Adds columns to store Grok/Claude research and competitor relationships

-- Add LinkedIn company URL (unique identifier for this tool)
ALTER TABLE linkedin_company_analysis
ADD COLUMN IF NOT EXISTS linkedin_company_url text DEFAULT NULL;

-- Add website URL (for Grok/Claude research)
ALTER TABLE linkedin_company_analysis
ADD COLUMN IF NOT EXISTS website_url text DEFAULT NULL;

-- Add grok research data (structured JSON)
ALTER TABLE linkedin_company_analysis
ADD COLUMN IF NOT EXISTS grok_research jsonb DEFAULT NULL;

-- Add claude research data (structured JSON)
ALTER TABLE linkedin_company_analysis
ADD COLUMN IF NOT EXISTS claude_research jsonb DEFAULT NULL;

-- Track if this is a competitor record
ALTER TABLE linkedin_company_analysis
ADD COLUMN IF NOT EXISTS competitor_of text DEFAULT NULL;

-- Indicate if this is primary company or competitor
ALTER TABLE linkedin_company_analysis
ADD COLUMN IF NOT EXISTS research_type text DEFAULT 'primary';

-- Add comments for documentation
COMMENT ON COLUMN linkedin_company_analysis.linkedin_company_url IS 'LinkedIn company URL - unique identifier for Company Research tool';
COMMENT ON COLUMN linkedin_company_analysis.website_url IS 'Company website URL for Grok/Claude research';
COMMENT ON COLUMN linkedin_company_analysis.grok_research IS 'Structured research data from Grok (xAI) web and X search';
COMMENT ON COLUMN linkedin_company_analysis.claude_research IS 'Structured research data from Claude web fetch and search';
COMMENT ON COLUMN linkedin_company_analysis.competitor_of IS 'If this is a competitor, reference to main company linkedin_company_url';
COMMENT ON COLUMN linkedin_company_analysis.research_type IS 'Type of record: primary or competitor';

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_linkedin_company_url ON linkedin_company_analysis(linkedin_company_url);
CREATE INDEX IF NOT EXISTS idx_competitor_of ON linkedin_company_analysis(competitor_of);
CREATE INDEX IF NOT EXISTS idx_research_type ON linkedin_company_analysis(research_type);
