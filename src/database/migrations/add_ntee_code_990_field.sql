-- Migration: Add NTEE Code 990 Field to Profiles Table
-- Version: 1.2.0
-- Date: 2025-10-18
-- Description: Add ntee_code_990 column to store NTEE code from 990 filing (organization's official NTEE code)

-- Add ntee_code_990 column to profiles table
ALTER TABLE profiles ADD COLUMN ntee_code_990 TEXT;

-- Update schema version
INSERT OR REPLACE INTO schema_version (version, description) VALUES
('1.2.0', 'Added ntee_code_990 field for NTEE code from 990 filing');
