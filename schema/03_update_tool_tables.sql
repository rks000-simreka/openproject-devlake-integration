-- Update tool tables to add missing columns for the extractor

-- Add missing columns to _tool_openproject_statuses
ALTER TABLE _tool_openproject_statuses 
ADD COLUMN IF NOT EXISTS color VARCHAR(20),
ADD COLUMN IF NOT EXISTS all_fields JSON;

-- Add missing columns to _tool_openproject_types
ALTER TABLE _tool_openproject_types 
ADD COLUMN IF NOT EXISTS all_fields JSON;

-- Add missing columns to _tool_openproject_priorities
ALTER TABLE _tool_openproject_priorities 
ADD COLUMN IF NOT EXISTS color VARCHAR(20),
ADD COLUMN IF NOT EXISTS all_fields JSON;

-- Add missing columns to _tool_openproject_activities
ALTER TABLE _tool_openproject_activities 
ADD COLUMN IF NOT EXISTS all_fields JSON;

-- Add missing columns to _tool_openproject_users
ALTER TABLE _tool_openproject_users 
ADD COLUMN IF NOT EXISTS avatar VARCHAR(512),
ADD COLUMN IF NOT EXISTS identity_url VARCHAR(512),
ADD COLUMN IF NOT EXISTS all_fields JSON;

-- Add missing columns to _tool_openproject_projects
ALTER TABLE _tool_openproject_projects 
ADD COLUMN IF NOT EXISTS parent_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS all_fields JSON;

-- Add missing columns to _tool_openproject_time_entries
ALTER TABLE _tool_openproject_time_entries 
ADD COLUMN IF NOT EXISTS work_package_title VARCHAR(512),
ADD COLUMN IF NOT EXISTS project_id INT,
ADD COLUMN IF NOT EXISTS project_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS all_fields JSON;