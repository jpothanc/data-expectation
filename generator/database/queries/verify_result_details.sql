-- ============================================
-- Verify Result Details Storage
-- ============================================
-- Check if partial_unexpected_counts is actually stored in the database
-- ============================================

USE [RubyUsers];
GO

-- ============================================
-- 1. Check if ResultDetails contains data
-- ============================================
SELECT 
    COUNT(*) AS TotalRecords,
    SUM(CASE WHEN [ResultDetails] IS NOT NULL AND [ResultDetails] != '' THEN 1 ELSE 0 END) AS HasResultDetails,
    SUM(CASE WHEN [ResultDetails] IS NULL OR [ResultDetails] = '' THEN 1 ELSE 0 END) AS MissingResultDetails
FROM [dbo].[GeExpectationResults];
GO

-- ============================================
-- 2. Check JSON validity and structure
-- ============================================
SELECT TOP 20
    er.[RunId],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success],
    er.[UnexpectedCount],
    -- Check JSON validity
    CASE 
        WHEN ISJSON(er.[ResultDetails]) = 1 THEN 'Valid JSON'
        ELSE 'Invalid JSON'
    END AS JsonStatus,
    -- Check if partial_unexpected_counts exists
    CASE 
        WHEN JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL 
        THEN 'Has partial_unexpected_counts'
        ELSE 'No partial_unexpected_counts'
    END AS HasPartialUnexpectedCounts,
    -- Show first 200 chars of ResultDetails
    LEFT(er.[ResultDetails], 200) AS ResultDetailsPreview
FROM [dbo].[GeExpectationResults] er
WHERE er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != ''
ORDER BY er.[RunId] DESC;
GO

-- ============================================
-- 3. Count records with partial_unexpected_counts
-- ============================================
SELECT 
    COUNT(*) AS TotalRecords,
    SUM(CASE 
        WHEN JSON_QUERY([ResultDetails], '$.partial_unexpected_counts') IS NOT NULL 
        THEN 1 ELSE 0 
    END) AS HasPartialUnexpectedCounts,
    SUM(CASE 
        WHEN JSON_QUERY([ResultDetails], '$.partial_unexpected_counts') IS NULL 
        THEN 1 ELSE 0 
    END) AS MissingPartialUnexpectedCounts
FROM [dbo].[GeExpectationResults]
WHERE [ResultDetails] IS NOT NULL
  AND [ResultDetails] != '';
GO

-- ============================================
-- 4. Show actual partial_unexpected_counts data
-- ============================================
SELECT TOP 10
    er.[RunId],
    vr.[RunTimestamp],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success],
    er.[UnexpectedCount],
    -- Show the actual JSON array
    JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') AS PartialUnexpectedCounts,
    -- Show full ResultDetails (truncated)
    LEFT(er.[ResultDetails], 500) AS ResultDetailsSample
FROM [dbo].[GeExpectationResults] er
INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL
ORDER BY vr.[RunTimestamp] DESC;
GO

-- ============================================
-- 5. Expand partial_unexpected_counts to verify structure
-- ============================================
SELECT TOP 20
    er.[RunId],
    er.[ColumnName],
    er.[ExpectationType],
    unexpected_value.[value] AS UnexpectedValue,
    unexpected_value.[count] AS ValueCount,
    er.[UnexpectedCount],
    er.[ResultDetails]
FROM [dbo].[GeExpectationResults] er
CROSS APPLY OPENJSON(JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts'))
    WITH (
        [value] NVARCHAR(MAX) '$.value',
        [count] INT '$.count'
    ) AS unexpected_value
WHERE er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != ''
ORDER BY er.[RunId] DESC;
GO

-- ============================================
-- 6. Check all keys in ResultDetails JSON
-- ============================================
SELECT TOP 10
    er.[RunId],
    er.[ColumnName],
    er.[ExpectationType],
    -- Extract all keys from ResultDetails
    (
        SELECT [key] 
        FROM OPENJSON(er.[ResultDetails])
        FOR JSON PATH
    ) AS JsonKeys,
    er.[ResultDetails]
FROM [dbo].[GeExpectationResults] er
WHERE er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != ''
  AND ISJSON(er.[ResultDetails]) = 1
ORDER BY er.[RunId] DESC;
GO



