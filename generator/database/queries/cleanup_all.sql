-- ============================================
-- Quick Cleanup: Delete ALL Validation Data
-- ============================================
-- WARNING: This will DELETE ALL data from validation tables
-- Use with caution!
-- ============================================

USE [RubyUsers];
GO

PRINT '============================================';
PRINT 'DELETING ALL VALIDATION DATA';
PRINT '============================================';

-- Show current counts before deletion
SELECT 'GeValidationRuns' AS TableName, COUNT(*) AS RecordCount FROM [dbo].[GeValidationRuns]
UNION ALL
SELECT 'GeExpectationResults', COUNT(*) FROM [dbo].[GeExpectationResults]
UNION ALL
SELECT 'GeValidationRulesApplied', COUNT(*) FROM [dbo].[GeValidationRulesApplied];
GO

-- Delete in order to respect foreign key constraints
-- Delete child records first
DELETE FROM [dbo].[GeExpectationResults];
PRINT 'Deleted all GeExpectationResults';

DELETE FROM [dbo].[GeValidationRulesApplied];
PRINT 'Deleted all GeValidationRulesApplied';

-- Delete parent records
DELETE FROM [dbo].[GeValidationRuns];
PRINT 'Deleted all GeValidationRuns';

PRINT '============================================';
PRINT 'Cleanup Complete - All data deleted';
PRINT '============================================';

-- Verify deletion
SELECT 'GeValidationRuns' AS TableName, COUNT(*) AS RecordCount FROM [dbo].[GeValidationRuns]
UNION ALL
SELECT 'GeExpectationResults', COUNT(*) FROM [dbo].[GeExpectationResults]
UNION ALL
SELECT 'GeValidationRulesApplied', COUNT(*) FROM [dbo].[GeValidationRulesApplied];
GO



