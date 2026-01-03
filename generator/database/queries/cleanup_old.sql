-- ============================================
-- Cleanup: Delete Data Older Than N Days
-- ============================================
-- Keeps the last N days of data, deletes everything older
-- ============================================

USE [RubyUsers];
GO

-- ============================================
-- CONFIGURATION: Change this value
-- ============================================
DECLARE @DaysToKeep INT = 30; -- Keep last 30 days, change as needed
-- ============================================

DECLARE @CutoffDate DATETIME2 = DATEADD(DAY, -@DaysToKeep, GETDATE());
DECLARE @DeletedRuns INT;
DECLARE @DeletedExpectations INT;
DECLARE @DeletedRules INT;

PRINT '============================================';
PRINT 'CLEANUP: Keep Last ' + CAST(@DaysToKeep AS VARCHAR(10)) + ' Days';
PRINT 'Deleting data older than: ' + CAST(@CutoffDate AS VARCHAR(50));
PRINT '============================================';

-- Show what will be deleted
SELECT 
    COUNT(*) AS RecordsToDelete,
    MIN([RunTimestamp]) AS OldestRecord,
    MAX([RunTimestamp]) AS NewestRecord
FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] < @CutoffDate;
GO

-- Get RunIds to delete
DECLARE @RunIdsToDelete TABLE (RunId INT);
INSERT INTO @RunIdsToDelete
SELECT [RunId] FROM [dbo].[GeValidationRuns]
WHERE [RunTimestamp] < @CutoffDate;

-- Delete related records first
DELETE er FROM [dbo].[GeExpectationResults] er
INNER JOIN @RunIdsToDelete r ON er.[RunId] = r.RunId;
SET @DeletedExpectations = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedExpectations AS VARCHAR(10)) + ' expectation results';

DELETE ra FROM [dbo].[GeValidationRulesApplied] ra
INNER JOIN @RunIdsToDelete r ON ra.[RunId] = r.RunId;
SET @DeletedRules = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRules AS VARCHAR(10)) + ' rules applied';

-- Delete main records
DELETE vr FROM [dbo].[GeValidationRuns] vr
INNER JOIN @RunIdsToDelete r ON vr.[RunId] = r.RunId;
SET @DeletedRuns = @@ROWCOUNT;
PRINT 'Deleted ' + CAST(@DeletedRuns AS VARCHAR(10)) + ' validation runs';

PRINT '============================================';
PRINT 'Cleanup Complete';
PRINT '============================================';

-- Show remaining counts
SELECT 'GeValidationRuns' AS TableName, COUNT(*) AS RecordCount FROM [dbo].[GeValidationRuns]
UNION ALL
SELECT 'GeExpectationResults', COUNT(*) FROM [dbo].[GeExpectationResults]
UNION ALL
SELECT 'GeValidationRulesApplied', COUNT(*) FROM [dbo].[GeValidationRulesApplied];
GO



