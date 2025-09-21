-- Migration: Add Enhanced Data Fields to Profiles Table
-- Version: 1.1.0
-- Date: 2025-09-21
-- Description: Add verification_data and web_enhanced_data columns for enhanced intelligence persistence

-- Add enhanced intelligence data columns to profiles table
ALTER TABLE profiles ADD COLUMN verification_data TEXT;
ALTER TABLE profiles ADD COLUMN web_enhanced_data TEXT;

-- Update schema version
INSERT OR REPLACE INTO schema_version (version, description) VALUES
('1.1.0', 'Added enhanced intelligence data fields (verification_data, web_enhanced_data)');