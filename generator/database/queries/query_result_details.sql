-- ============================================
-- Query Result Details with partial_unexpected_counts
-- ============================================
-- Extracts and displays detailed result information from ResultDetails JSON
-- ============================================

USE [RubyUsers];
GO

-- ============================================
-- 1. Basic Result Details Query
-- ============================================
-- Shows all result details with parsed JSON information

SELECT 
    er.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success],
    er.[ElementCount],
    er.[UnexpectedCount],
    er.[UnexpectedPercent],
    er.[MissingCount],
    er.[MissingPercent],
    er.[ResultDetails]
FROM [dbo].[GeExpectationResults] er
INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE er.[ResultDetails] IS NOT NULL
ORDER BY vr.[RunTimestamp] DESC, er.[ColumnName], er.[ExpectationType];
GO

-- ============================================
-- 2. Extract partial_unexpected_counts from JSON
-- ============================================
-- Parses the ResultDetails JSON to extract partial_unexpected_counts array

SELECT 
    er.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success],
    er.[UnexpectedCount],
    er.[UnexpectedPercent],
    -- Extract partial_unexpected_counts array
    JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') AS PartialUnexpectedCounts,
    -- Extract partial_unexpected_list
    JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_list') AS PartialUnexpectedList,
    -- Extract element_count
    JSON_VALUE(er.[ResultDetails], '$.element_count') AS ElementCountFromJSON,
    -- Extract missing_count
    JSON_VALUE(er.[ResultDetails], '$.missing_count') AS MissingCountFromJSON,
    -- Extract missing_percent
    JSON_VALUE(er.[ResultDetails], '$.missing_percent') AS MissingPercentFromJSON,
    er.[ResultDetails] AS FullResultDetails
FROM [dbo].[GeExpectationResults] er
INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
WHERE er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != 'null'
  AND JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL
ORDER BY vr.[RunTimestamp] DESC, er.[ColumnName], er.[ExpectationType];
GO

-- ============================================
-- 3. Expand partial_unexpected_counts into rows
-- ============================================
-- Uses OPENJSON to expand the array into individual rows with value and count

SELECT 
    er.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    er.[Success],
    er.[UnexpectedCount],
    er.[UnexpectedPercent],
    -- Expand partial_unexpected_counts array
    unexpected_value.[value] AS UnexpectedValue,
    unexpected_value.[count] AS ValueCount,
    -- Other details
    JSON_VALUE(er.[ResultDetails], '$.element_count') AS ElementCount,
    JSON_VALUE(er.[ResultDetails], '$.missing_count') AS MissingCount,
    JSON_VALUE(er.[ResultDetails], '$.missing_percent') AS MissingPercent
FROM [dbo].[GeExpectationResults] er
INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
CROSS APPLY OPENJSON(JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts'))
    WITH (
        [value] NVARCHAR(MAX) '$.value',
        [count] INT '$.count'
    ) AS unexpected_value
WHERE er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != 'null'
  AND JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL
ORDER BY vr.[RunTimestamp] DESC, er.[ColumnName], er.[ExpectationType], unexpected_value.[count] DESC;
GO

-- ============================================
-- 4. Summary of Unexpected Values by Column
-- ============================================
-- Groups unexpected values by column and shows counts

SELECT 
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    unexpected_value.[value] AS UnexpectedValue,
    SUM(CAST(unexpected_value.[count] AS INT)) AS TotalOccurrences,
    COUNT(DISTINCT er.[RunId]) AS NumberOfRuns
FROM [dbo].[GeExpectationResults] er
INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
CROSS APPLY OPENJSON(JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts'))
    WITH (
        [value] NVARCHAR(MAX) '$.value',
        [count] INT '$.count'
    ) AS unexpected_value
WHERE er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != 'null'
  AND JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL
  AND er.[Success] = 0  -- Only show failed expectations
GROUP BY 
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    unexpected_value.[value]
ORDER BY 
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    TotalOccurrences DESC;
GO

-- ============================================
-- 5. Latest Run - Detailed Unexpected Values
-- ============================================
-- Shows unexpected values for the most recent validation run

DECLARE @LatestRunId INT;
SELECT @LatestRunId = MAX([RunId]) FROM [dbo].[GeValidationRuns];

IF @LatestRunId IS NOT NULL
BEGIN
    SELECT 
        er.[RunId],
        vr.[RunTimestamp],
        vr.[Region],
        vr.[ProductType],
        vr.[Exchange],
        er.[ColumnName],
        er.[ExpectationType],
        er.[Success],
        er.[UnexpectedCount],
        er.[UnexpectedPercent],
        unexpected_value.[value] AS UnexpectedValue,
        unexpected_value.[count] AS ValueCount,
        JSON_VALUE(er.[ResultDetails], '$.element_count') AS ElementCount,
        JSON_VALUE(er.[ResultDetails], '$.missing_count') AS MissingCount,
        JSON_VALUE(er.[ResultDetails], '$.missing_percent') AS MissingPercent,
        JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_list') AS PartialUnexpectedList
    FROM [dbo].[GeExpectationResults] er
    INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
    CROSS APPLY OPENJSON(JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts'))
        WITH (
            [value] NVARCHAR(MAX) '$.value',
            [count] INT '$.count'
        ) AS unexpected_value
    WHERE er.[RunId] = @LatestRunId
      AND er.[ResultDetails] IS NOT NULL
      AND er.[ResultDetails] != 'null'
      AND JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL
    ORDER BY er.[ColumnName], er.[ExpectationType], unexpected_value.[count] DESC;
END
ELSE
BEGIN
    PRINT 'No validation runs found';
END
GO

-- ============================================
-- 6. Failed Expectations with Unexpected Values
-- ============================================
-- Shows only failed expectations with their unexpected values expanded

SELECT 
    er.[RunId],
    vr.[RunTimestamp],
    vr.[Region],
    vr.[ProductType],
    vr.[Exchange],
    er.[ColumnName],
    er.[ExpectationType],
    er.[UnexpectedCount],
    er.[UnexpectedPercent],
    unexpected_value.[value] AS UnexpectedValue,
    unexpected_value.[count] AS ValueCount,
    er.[ElementCount],
    er.[MissingCount],
    er.[MissingPercent]
FROM [dbo].[GeExpectationResults] er
INNER JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
CROSS APPLY OPENJSON(JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts'))
    WITH (
        [value] NVARCHAR(MAX) '$.value',
        [count] INT '$.count'
    ) AS unexpected_value
WHERE er.[Success] = 0
  AND er.[ResultDetails] IS NOT NULL
  AND er.[ResultDetails] != 'null'
  AND JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL
ORDER BY vr.[RunTimestamp] DESC, er.[UnexpectedPercent] DESC, unexpected_value.[count] DESC;
GO

-- ============================================
-- 7. Check JSON Structure
-- ============================================
-- Verify that ResultDetails contains valid JSON and check structure

SELECT TOP 10
    er.[RunId],
    er.[ColumnName],
    er.[ExpectationType],
    er.[ResultDetails],
    -- Check if JSON is valid
    CASE 
        WHEN ISJSON(er.[ResultDetails]) = 1 THEN 'Valid JSON'
        ELSE 'Invalid JSON'
    END AS JsonStatus,
    -- Check if partial_unexpected_counts exists
    CASE 
        WHEN JSON_QUERY(er.[ResultDetails], '$.partial_unexpected_counts') IS NOT NULL 
        THEN 'Has partial_unexpected_counts'
        ELSE 'No partial_unexpected_counts'
    END AS HasPartialUnexpectedCounts
FROM [dbo].[GeExpectationResults] er
WHERE er.[ResultDetails] IS NOT NULL
ORDER BY er.[RunId] DESC;
GO



