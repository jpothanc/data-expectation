"""Command-line interface for batch validation generator."""

import argparse
import sys
import logging
from pathlib import Path

from ..core.validator import BatchValidator
from ..core.logging_config import setup_logging
from ..config.config_loader import ConfigLoader
from ..config.config_helper import get_api_base_url


class ValidationCLI:
    """Command-line interface for batch validation."""
    
    def __init__(self):
        """Initialize CLI."""
        self.parser = self._create_parser()
        self.config_loader = None
    
    def _create_parser(self):
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description="Batch validation generator for regions, product types, and exchanges",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Validate all APAC exchanges
  python -m generator.main apac
  
  # Validate multiple regions
  python -m generator.main apac,emea,us
  
  # Validate with custom rules
  python -m generator.main apac --custom-rules status_validation,isin_validation
  
  # Validate multiple regions with custom rules
  python -m generator.main apac,emea --custom-rules status_validation
  
  # Use custom API URL
  python -m generator.main apac --api-url http://localhost:5006
  
  # Save results to database
  python -m generator.main apac --save-to-database
  
  # Validate multiple regions and save to database
  python -m generator.main apac,emea,us --save-to-database
  
  # Save to database with custom connection string
  python -m generator.main apac --save-to-database --database-connection "DRIVER={...};SERVER=..."
  
  # List available regions
  python -m generator.main --list-regions
            """
        )
        
        parser.add_argument(
            'region',
            nargs='?',
            help='Region(s) to validate. Can be a single region (e.g., apac) or comma-separated list (e.g., apac,emea,us)'
        )
        
        parser.add_argument(
            '--custom-rules',
            type=str,
            help='Comma-separated list of custom rule names'
        )
        
        parser.add_argument(
            '--api-url',
            type=str,
            default=None,
            help='Base URL of the validation API (defaults to value in config.json)'
        )
        
        parser.add_argument(
            '--config',
            type=str,
            help='Path to regions.yaml config file'
        )
        
        parser.add_argument(
            '--list-regions',
            action='store_true',
            help='List all available regions and exit'
        )
        
        parser.add_argument(
            '--verbose',
            '-v',
            action='store_true',
            help='Enable verbose logging'
        )
        
        parser.add_argument(
            '--save-to-database',
            action='store_true',
            help='Save validation results to database'
        )
        
        parser.add_argument(
            '--database-connection',
            type=str,
            help='Database connection string (optional, will use config.json if not provided)'
        )

        parser.add_argument(
            '--workers',
            type=int,
            default=4,
            metavar='N',
            help='Number of concurrent exchange validations per region (default: 4)'
        )

        return parser
    
    def setup_logging(self, verbose=False):
        """Setup logging configuration with daily log files."""
        log_file, log_dir = setup_logging(verbose=verbose)
        print(f"📝 Logging to: {log_file}")
    
    def load_config(self, config_path=None):
        """Load configuration."""
        try:
            self.config_loader = ConfigLoader(config_path)
        except Exception as e:
            print(f"❌ Error loading configuration: {str(e)}")
            sys.exit(1)
    
    def list_regions(self):
        """List all available regions and their configurations."""
        print("\nAvailable Regions:")
        print("-" * 40)
        
        for region in self.config_loader.get_regions():
            print(f"  - {region}")
            for product_type in self.config_loader.get_product_types(region):
                exchanges = self.config_loader.get_exchanges(region, product_type)
                print(f"    {product_type}: {', '.join(exchanges)}")
        print()
    
    def validate_region_exists(self, region):
        """Validate that region exists in configuration."""
        try:
            self.config_loader.get_product_types(region)
            return True
        except KeyError as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def parse_regions(self, regions_str):
        """Parse comma-separated region names."""
        if not regions_str:
            return []
        return [region.strip() for region in regions_str.split(',') if region.strip()]
    
    def parse_custom_rules(self, custom_rules_str):
        """Parse comma-separated custom rule names."""
        if not custom_rules_str:
            return None
        return [rule.strip() for rule in custom_rules_str.split(',')]
    
    def run_validation(self, regions, custom_rule_names, api_url, config_path,
                       save_to_database=False, database_connection=None, max_workers=4):
        """Run batch validation for one or more regions."""
        validator = None
        try:
            database_service = None
            if save_to_database:
                from ..database.database_service import DatabaseService
                if database_connection:
                    database_service = DatabaseService(connection_string=database_connection)
                else:
                    database_service = DatabaseService()
                
                # Test connection
                if not database_service.test_connection():
                    print("⚠️  Warning: Database connection test failed. Results may not be saved.")
            
            validator = BatchValidator(
                config_path=config_path,
                api_base_url=api_url,
                save_to_database=save_to_database,
                database_service=database_service
            )
            
            total_failed = 0
            total_successful = 0
            all_summaries = []
            
            for region in regions:
                print(f"\n{'='*60}")
                print(f"Processing Region: {region.upper()}")
                print(f"{'='*60}\n")
                
                summary = validator.validate_region(
                    region=region,
                    custom_rule_names=custom_rule_names,
                    verbose=True,
                    max_workers=max_workers,
                )
                
                all_summaries.append(summary)
                total_failed += summary.failed
                total_successful += summary.successful
            
            # Print overall summary
            print(f"\n{'='*60}")
            print("OVERALL SUMMARY")
            print(f"{'='*60}")
            print(f"  Regions Processed: {len(regions)}")
            print(f"  Total Successful: {total_successful}")
            print(f"  Total Failed: {total_failed}")
            print(f"  Total Validations: {total_successful + total_failed}")
            
            if total_failed > 0:
                print(f"\n❌ {total_failed} validation(s) failed across {len(regions)} region(s)")
                sys.exit(1)
            else:
                print(f"\n✅ All validations passed!")
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Validation interrupted by user")
            if validator:
                validator.close()
            sys.exit(130)
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            if validator:
                validator.close()
            sys.exit(1)
        finally:
            if validator:
                validator.close()
    
    def run(self):
        """Run the CLI."""
        args = self.parser.parse_args()
        self.setup_logging(args.verbose)
        
        self.load_config(args.config)
        
        if args.list_regions:
            self.list_regions()
            sys.exit(0)
        
        if not args.region:
            self.parser.print_help()
            print("\n❌ Error: Region is required")
            print(f"Available regions: {', '.join(self.config_loader.get_regions())}")
            sys.exit(1)
        
        # Parse multiple regions
        regions = self.parse_regions(args.region)
        if not regions:
            print("❌ Error: No valid regions provided")
            sys.exit(1)
        
        # Validate all regions exist
        invalid_regions = []
        for region in regions:
            if not self.validate_region_exists(region):
                invalid_regions.append(region)
        
        if invalid_regions:
            print(f"❌ Error: Invalid region(s): {', '.join(invalid_regions)}")
            print(f"Available regions: {', '.join(self.config_loader.get_regions())}")
            sys.exit(1)
        
        custom_rule_names = self.parse_custom_rules(args.custom_rules)
        self.run_validation(
            regions,
            custom_rule_names,
            args.api_url or get_api_base_url(),
            args.config,
            save_to_database=args.save_to_database,
            database_connection=args.database_connection,
            max_workers=args.workers,
        )

