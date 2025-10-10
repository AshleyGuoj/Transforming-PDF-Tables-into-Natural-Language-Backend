-- Migration: Fix file unique constraint to allow reusing deleted file names
-- Date: 2025-10-10
-- Description: Replaces the unique constraint/index with a partial unique index
--              that only applies to non-deleted files (deleted_at IS NULL)

-- Drop the old unique constraint (which also drops its backing index)
ALTER TABLE file DROP CONSTRAINT IF EXISTS uq_project_file_name;

-- Create a partial unique index that only applies to active (non-deleted) files
CREATE UNIQUE INDEX IF NOT EXISTS uq_project_file_name_active
ON file (project_id, name)
WHERE deleted_at IS NULL;

-- This allows the same filename to be reused after a file is deleted
-- within the same project, since soft-deleted files won't conflict
