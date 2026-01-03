"""Service for querying validation analytics data from RubyUsers database."""

import logging
from config.config_service import ConfigService

logger = logging.getLogger(__name__)


class ValidationAnalyticsService:
    """Service for querying validation analytics from RubyUsers database."""
    
    def __init__(self, connection_string=None):
        """
        Initialize validation analytics service.
        
        Args:
            connection_string: SQL Server connection string. If None, will try to get from config.
        """
        try:
            import pyodbc
            self.pyodbc = pyodbc
        except ImportError:
            raise ImportError(
                "pyodbc is required for ValidationAnalyticsService. "
                "Install it with: pip install pyodbc"
            )
        
        if connection_string:
            self.connection_string = connection_string
        else:
            # Try to get connection string from config
            config_service = ConfigService()
            # Default to RubyUsers database - modify connection string to use RubyUsers
            db_config = config_service.get_database_config()
            base_connection = db_config.get('connection_string_apac_uat', '')
            # Replace DATABASE=Instruments with DATABASE=RubyUsers
            if 'DATABASE=' in base_connection:
                self.connection_string = base_connection.replace(
                    'DATABASE=Instruments', 'DATABASE=RubyUsers'
                ).replace(
                    'DATABASE=Instruments;', 'DATABASE=RubyUsers;'
                )
            else:
                # If no DATABASE specified, add it
                self.connection_string = base_connection.rstrip(';') + ';DATABASE=RubyUsers;'
        
        self._connection = None
    
    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            try:
                self._connection = self.pyodbc.connect(self.connection_string)
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
        return self._connection
    
    def _execute_query(self, query, params=None):
        """Execute a SQL query and return results as list of dictionaries."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            raise
    
    def get_pass_fail_by_region(self, days=7):
        """
        Get pass vs fail statistics by region.
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            List of dicts with Region, TotalRuns, SuccessfulRuns, FailedRuns, SuccessRate
        """
        query = """
            SELECT 
                [Region],
                COUNT(*) as [TotalRuns],
                SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulRuns],
                SUM(CASE WHEN [Success] = 0 THEN 1 ELSE 0 END) as [FailedRuns],
                CAST(SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as [SuccessRate]
            FROM [dbo].[GeValidationRuns]
            WHERE [RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
            GROUP BY [Region]
            ORDER BY [Region]
        """
        return self._execute_query(query, (days,))
    
    def get_heatmap_region_product(self, days=7):
        """
        Get success rates by region and product type (heatmap data).
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            List of dicts with Region, ProductType, TotalRuns, SuccessfulRuns, SuccessRate
        """
        query = """
            SELECT 
                [Region],
                [ProductType],
                COUNT(*) as [TotalRuns],
                SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) as [SuccessfulRuns],
                CAST(SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as [SuccessRate]
            FROM [dbo].[GeValidationRuns]
            WHERE [RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
            GROUP BY [Region], [ProductType]
            ORDER BY [Region], [ProductType]
        """
        return self._execute_query(query, (days,))
    
    def get_regional_exchange_breakdown(self, days=7):
        """
        Get exchange breakdown by region and product type (treemap data).
        
        Args:
            days: Number of days to look back (default: 7)
            
        Returns:
            List of dicts with Region, ProductType, Exchange, TotalRuns, SuccessRate
        """
        query = """
            SELECT 
                [Region],
                [ProductType],
                [Exchange],
                COUNT(*) as [TotalRuns],
                CAST(
                    CASE 
                        WHEN SUM([TotalExpectations]) > 0 
                        THEN SUM([SuccessfulExpectations]) * 100.0 / SUM([TotalExpectations])
                        WHEN COUNT(*) > 0
                        THEN SUM(CASE WHEN [Success] = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                        ELSE 0 
                    END 
                    AS DECIMAL(5,2)
                ) as [SuccessRate]
            FROM [dbo].[GeValidationRuns]
            WHERE [RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
            GROUP BY [Region], [ProductType], [Exchange]
            HAVING COUNT(*) > 0
            ORDER BY [Region], [ProductType], [Exchange]
        """
        return self._execute_query(query, (days,))
    
    def get_rule_failure_stats(self, days=7, limit=20):
        """
        Get rule failure statistics (bar chart data).
        
        Args:
            days: Number of days to look back (default: 7)
            limit: Maximum number of rules to return (default: 20)
            
        Returns:
            List of dicts with RuleName, FailureCount, TotalRuns, FailureRate
        """
        query = """
            SELECT TOP (?)
                vra.[RuleName],
                COUNT(*) as [TotalRuns],
                SUM(CASE WHEN vr.[Success] = 0 THEN 1 ELSE 0 END) as [FailureCount],
                CAST(SUM(CASE WHEN vr.[Success] = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) as [FailureRate]
            FROM [dbo].[GeValidationRulesApplied] vra
            JOIN [dbo].[GeValidationRuns] vr ON vra.[RunId] = vr.[RunId]
            WHERE vr.[RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
            GROUP BY vra.[RuleName]
            HAVING SUM(CASE WHEN vr.[Success] = 0 THEN 1 ELSE 0 END) > 0
            ORDER BY [FailureCount] DESC
        """
        return self._execute_query(query, (limit, days))
    
    def get_validation_results_by_exchange(self, exchange, days=7, limit=None):
        """
        Get validation results for a specific exchange.
        
        Args:
            exchange: Exchange code (e.g., 'XHKG', 'XNSE')
            days: Number of days to look back (default: 7)
            limit: Optional limit on number of runs to return (default: 50 to prevent slow queries)
            
        Returns:
            List of validation runs with their expectation results
        """
        # Set default limit to prevent slow queries
        if limit is None:
            limit = 50
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Build query with limit (always use limit to prevent slow queries)
            query = f"""
                SELECT TOP ({limit})
                    vr.[RunId],
                    vr.[RunTimestamp],
                    vr.[Region],
                    vr.[ProductType],
                    vr.[Exchange],
                    vr.[Success],
                    vr.[TotalExpectations],
                    vr.[SuccessfulExpectations],
                    vr.[FailedExpectations],
                    vr.[RulesApplied],
                    vr.[CustomRuleNames],
                    vr.[ApiUrl],
                    vr.[ExecutionDurationMs]
                FROM [dbo].[GeValidationRuns] vr
                WHERE vr.[Exchange] = ?
                  AND vr.[RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
                ORDER BY vr.[RunTimestamp] DESC
            """
            
            logger.info(f"Executing query for exchange {exchange}, days {days}")
            cursor.execute(query, (exchange, days))
            runs = cursor.fetchall()
            logger.info(f"Found {len(runs)} runs for exchange {exchange}")
            
            if not runs:
                logger.info(f"No runs found for exchange {exchange}")
                cursor.close()
                return {
                    "exchange": exchange,
                    "days": days,
                    "total_runs": 0,
                    "runs": []
                }
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Convert runs to dictionaries
            runs_data = []
            for idx, run in enumerate(runs):
                logger.debug(f"Processing run {idx + 1}/{len(runs)}: RunId={run[0] if run else 'N/A'}")
                run_dict = dict(zip(columns, run))
                
                # Get expectation results for this run
                exp_query = """
                    SELECT 
                        [ResultId],
                        [ColumnName],
                        [ExpectationType],
                        [Success],
                        [ElementCount],
                        [UnexpectedCount],
                        [UnexpectedPercent],
                        [MissingCount],
                        [MissingPercent],
                        [ResultDetails]
                    FROM [dbo].[GeExpectationResults]
                    WHERE [RunId] = ?
                    ORDER BY [ColumnName], [ExpectationType]
                """
                
                cursor.execute(exp_query, (run_dict['RunId'],))
                expectations = cursor.fetchall()
                exp_columns = [col[0] for col in cursor.description]
                
                # Convert expectation results to dictionaries and ensure numeric types
                expectation_results = []
                for exp in expectations:
                    exp_dict = dict(zip(exp_columns, exp))
                    # Ensure numeric fields are properly converted
                    for key in ['UnexpectedPercent', 'MissingPercent', 'ElementCount', 
                               'UnexpectedCount', 'MissingCount']:
                        if key in exp_dict and exp_dict[key] is not None:
                            try:
                                exp_dict[key] = float(exp_dict[key])
                            except (ValueError, TypeError):
                                exp_dict[key] = 0.0
                    expectation_results.append(exp_dict)
                
                run_dict['expectation_results'] = expectation_results
                
                # Get rules applied for this run
                rules_query = """
                    SELECT 
                        [RuleName],
                        [RuleType],
                        [RuleLevel],
                        [RuleSource]
                    FROM [dbo].[GeValidationRulesApplied]
                    WHERE [RunId] = ?
                    ORDER BY [RuleType], [RuleLevel]
                """
                
                cursor.execute(rules_query, (run_dict['RunId'],))
                rules = cursor.fetchall()
                rules_columns = [col[0] for col in cursor.description]
                
                run_dict['rules_applied'] = [
                    dict(zip(rules_columns, rule)) for rule in rules
                ]
                
                runs_data.append(run_dict)
            
            return {
                "exchange": exchange,
                "days": days,
                "total_runs": len(runs_data),
                "runs": runs_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching validation results for exchange {exchange}: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
    
    def get_combined_rule_stats(self, combined_rule_name, days=7):
        """
        Get statistics for a specific combined rule (e.g., IsTradableStock).
        
        Args:
            combined_rule_name: Name of the combined rule
            days: Number of days to look back (default: 7)
            
        Returns:
            Dict with TradableCount, NotTradableCount, TotalCount, TradableRate, FailureReasons
        """
        # Check both GeValidationRulesApplied.RuleName and GeValidationRuns.CustomRuleNames
        # Combined rules can be stored in either location depending on how validation was run
        query = """
            SELECT 
                COUNT(DISTINCT vr.[RunId]) as [TotalCount],
                COUNT(DISTINCT CASE WHEN vr.[Success] = 1 THEN vr.[RunId] END) as [TradableCount],
                COUNT(DISTINCT CASE WHEN vr.[Success] = 0 THEN vr.[RunId] END) as [NotTradableCount]
            FROM [dbo].[GeValidationRuns] vr
            LEFT JOIN [dbo].[GeValidationRulesApplied] vra ON vr.[RunId] = vra.[RunId] AND vra.[RuleName] = ?
            WHERE (
                vra.[RuleName] = ? 
                OR vr.[CustomRuleNames] LIKE ? 
                OR vr.[CustomRuleNames] LIKE ?
            )
              AND vr.[RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
        """
        # Create pattern for LIKE queries: %rule_name% and %rule_name, and ,rule_name%
        pattern1 = f'%{combined_rule_name}%'
        pattern2 = f'%,{combined_rule_name}%'
        
        stats = self._execute_query(query, (combined_rule_name, combined_rule_name, pattern1, pattern2, days))
        
        if not stats or stats[0]["TotalCount"] == 0:
            return {
                "TradableCount": 0,
                "NotTradableCount": 0,
                "TotalCount": 0,
                "TradableRate": 0.0,
                "FailureReasons": []
            }
        
        total_count = stats[0]["TotalCount"] or 0
        tradable_count = stats[0]["TradableCount"] or 0
        not_tradable_count = stats[0]["NotTradableCount"] or 0
        
        tradable_rate = (tradable_count * 100.0 / total_count) if total_count > 0 else 0.0
        
        result = {
            "TotalCount": total_count,
            "TradableCount": tradable_count,
            "NotTradableCount": not_tradable_count,
            "TradableRate": round(tradable_rate, 2)
        }
        
        # Get failure reasons (failed expectations for this rule)
        failure_query = """
            SELECT DISTINCT
                er.[ColumnName],
                er.[ExpectationType],
                COUNT(*) as [FailureCount]
            FROM [dbo].[GeExpectationResults] er
            JOIN [dbo].[GeValidationRuns] vr ON er.[RunId] = vr.[RunId]
            LEFT JOIN [dbo].[GeValidationRulesApplied] vra ON vr.[RunId] = vra.[RunId] AND vra.[RuleName] = ?
            WHERE (
                vra.[RuleName] = ? 
                OR vr.[CustomRuleNames] LIKE ? 
                OR vr.[CustomRuleNames] LIKE ?
            )
              AND vr.[Success] = 0
              AND er.[Success] = 0
              AND vr.[RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
            GROUP BY er.[ColumnName], er.[ExpectationType]
            ORDER BY [FailureCount] DESC
        """
        failure_reasons = self._execute_query(failure_query, (combined_rule_name, combined_rule_name, pattern1, pattern2, days))
        
        result["FailureReasons"] = [
            {
                "ColumnName": fr["ColumnName"],
                "ExpectationType": fr["ExpectationType"],
                "FailureCount": fr["FailureCount"]
            }
            for fr in failure_reasons
        ]
        
        return result
    
    def get_regional_trends(self, days=30):
        """
        Get validation trend data by region over time, showing each individual run.
        
        Args:
            days: Number of days to look back (default: 30)
            
        Returns:
            Dictionary with regions as keys, each containing a list of data points:
            {
                "APAC": [{Date, RunId, Exchange, ...}, ...],
                "US": [{Date, RunId, Exchange, ...}, ...],
                "EMEA": [{Date, RunId, Exchange, ...}, ...]
            }
        """
        query = """
            SELECT 
                [Region],
                [RunTimestamp] as [Date],
                [RunId],
                [Exchange],
                [ProductType],
                [Success],
                [FailedExpectations],
                [TotalExpectations],
                [SuccessfulExpectations],
                CAST(
                    CASE 
                        WHEN [TotalExpectations] > 0 
                        THEN [SuccessfulExpectations] * 100.0 / [TotalExpectations]
                        ELSE 0 
                    END 
                    AS DECIMAL(5,2)
                ) as [SuccessRate],
                -- Calculate FailedRuns (1 if failed, 0 if successful) for consistency with frontend
                CASE WHEN [Success] = 0 THEN 1 ELSE 0 END as [FailedRuns],
                CASE WHEN [Success] = 1 THEN 1 ELSE 0 END as [SuccessfulRuns],
                1 as [TotalRuns]
            FROM [dbo].[GeValidationRuns]
            WHERE [RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
            ORDER BY [Region], [RunTimestamp]
        """
        raw_data = self._execute_query(query, (days,))
        
        # Group data by region (normalize to uppercase for consistency)
        grouped_data = {}
        for row in raw_data:
            region = row['Region']
            # Normalize region to uppercase for consistent frontend display
            # Database stores lowercase (us, apac, emea) but frontend expects uppercase (US, APAC, EMEA)
            region_key = region.upper() if region else 'UNKNOWN'
            if region_key not in grouped_data:
                grouped_data[region_key] = []
            # Remove Region from individual data points since it's now the key
            data_point = {k: v for k, v in row.items() if k != 'Region'}
            grouped_data[region_key].append(data_point)
        
        return grouped_data
    
    def get_validation_results_by_region_date(self, region, date, days=7, limit=None):
        """
        Get validation results for a specific region and date.
        
        Args:
            region: Region name (e.g., "APAC", "US", "EMEA")
            date: Date string in format "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
            days: Number of days to look back (default: 7)
            limit: Optional limit on number of runs to return
            
        Returns:
            Dictionary with exchange, days, total_runs, and runs array
        """
        # Set default limit to prevent slow queries
        if limit is None:
            limit = 200
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Normalize region to match database format (lowercase)
            region_normalized = region.lower() if region else None
            
            # Parse date - handle both date-only and datetime formats
            from datetime import datetime
            try:
                # Try parsing as datetime first
                if 'T' in date or ' ' in date:
                    date_obj = datetime.strptime(date.split('T')[0] if 'T' in date else date.split(' ')[0], '%Y-%m-%d')
                else:
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                date_start = date_obj.strftime('%Y-%m-%d 00:00:00')
                date_end = date_obj.strftime('%Y-%m-%d 23:59:59')
            except ValueError:
                # If parsing fails, use the date as-is
                date_start = date
                date_end = date
            
            # Build query with limit
            query = f"""
                SELECT TOP ({limit})
                    vr.[RunId],
                    vr.[RunTimestamp],
                    vr.[Region],
                    vr.[ProductType],
                    vr.[Exchange],
                    vr.[Success],
                    vr.[TotalExpectations],
                    vr.[SuccessfulExpectations],
                    vr.[FailedExpectations],
                    vr.[RulesApplied],
                    vr.[CustomRuleNames],
                    vr.[ApiUrl],
                    vr.[ExecutionDurationMs]
                FROM [dbo].[GeValidationRuns] vr
                WHERE UPPER(vr.[Region]) = UPPER(?)
                  AND CAST(vr.[RunTimestamp] AS DATE) = CAST(? AS DATE)
                  AND vr.[RunTimestamp] >= DATEADD(DAY, -?, GETDATE())
                ORDER BY vr.[RunTimestamp] DESC
            """
            
            logger.info(f"Executing query for region {region}, date {date}, days {days}")
            cursor.execute(query, (region_normalized, date_start, days))
            runs = cursor.fetchall()
            logger.info(f"Found {len(runs)} runs for region {region} on date {date}")
            
            if not runs:
                logger.info(f"No runs found for region {region} on date {date}")
                cursor.close()
                return {
                    "exchange": f"{region} - {date}",
                    "days": days,
                    "total_runs": 0,
                    "runs": []
                }
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Convert runs to dictionaries
            runs_data = []
            for idx, run in enumerate(runs):
                logger.debug(f"Processing run {idx + 1}/{len(runs)}: RunId={run[0] if run else 'N/A'}")
                run_dict = dict(zip(columns, run))
                
                # Only include failed runs
                if run_dict.get('Success') == 0 or run_dict.get('Success') is False:
                    # Get expectation results for this run
                    exp_query = """
                        SELECT 
                            [ResultId],
                            [ColumnName],
                            [ExpectationType],
                            [Success],
                            [ElementCount],
                            [UnexpectedCount],
                            [UnexpectedPercent],
                            [MissingCount],
                            [MissingPercent],
                            [ResultDetails]
                        FROM [dbo].[GeExpectationResults]
                        WHERE [RunId] = ?
                        ORDER BY [ColumnName], [ExpectationType]
                    """
                    
                    cursor.execute(exp_query, (run_dict['RunId'],))
                    expectations = cursor.fetchall()
                    exp_columns = [col[0] for col in cursor.description]
                    
                    # Convert expectation results to dictionaries and ensure numeric types
                    expectation_results = []
                    for exp in expectations:
                        exp_dict = dict(zip(exp_columns, exp))
                        # Ensure numeric fields are properly converted
                        for key in ['UnexpectedPercent', 'MissingPercent', 'ElementCount', 
                                   'UnexpectedCount', 'MissingCount']:
                            if key in exp_dict and exp_dict[key] is not None:
                                try:
                                    exp_dict[key] = float(exp_dict[key])
                                except (ValueError, TypeError):
                                    exp_dict[key] = 0.0
                        expectation_results.append(exp_dict)
                    
                    run_dict['expectation_results'] = expectation_results
                    
                    # Get rules applied for this run
                    rules_query = """
                        SELECT 
                            [RuleName],
                            [RuleType],
                            [RuleLevel],
                            [RuleSource]
                        FROM [dbo].[GeValidationRulesApplied]
                        WHERE [RunId] = ?
                        ORDER BY [RuleType], [RuleLevel]
                    """
                    
                    cursor.execute(rules_query, (run_dict['RunId'],))
                    rules = cursor.fetchall()
                    rules_columns = [col[0] for col in cursor.description]
                    
                    run_dict['rules_applied'] = [
                        dict(zip(rules_columns, rule)) for rule in rules
                    ]
                    
                    runs_data.append(run_dict)
            
            return {
                "exchange": f"{region} - {date}",
                "days": days,
                "total_runs": len(runs_data),
                "runs": runs_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching validation results for region {region} on date {date}: {e}", exc_info=True)
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

