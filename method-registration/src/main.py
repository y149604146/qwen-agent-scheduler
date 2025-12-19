"""
Method Registration System - Main Entry Point

This module provides the main entry point for the Method Registration System.
It integrates ConfigParser, MetadataValidator, and DatabaseWriter to:
1. Load model and method configurations
2. Validate method metadata
3. Write validated methods to PostgreSQL database

Usage:
    python src/main.py --model-config config/model_config.yaml --methods-config config/methods.yaml

Requirements: 10.1, 10.2
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from shared.config_loader import load_model_config, load_database_config
from shared.models import ModelConfig, DatabaseConfig
from config_parser import ConfigParser
from validator import MetadataValidator
from db_client import DatabaseWriter


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler()]
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Method Registration System - Register methods to database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register methods using default config files
  python src/main.py
  
  # Register methods with custom config files
  python src/main.py --model-config custom_model.yaml --methods-config custom_methods.yaml
  
  # Register methods with debug logging
  python src/main.py --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--model-config',
        type=str,
        default='config/model_config.yaml',
        help='Path to model configuration file (default: config/model_config.yaml)'
    )
    
    parser.add_argument(
        '--methods-config',
        type=str,
        default='config/methods.yaml',
        help='Path to methods configuration file (default: config/methods.yaml)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Optional log file path'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate methods without writing to database'
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for Method Registration System
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("Method Registration System Starting")
        logger.info("=" * 60)
        
        # Step 1: Load model configuration
        logger.info(f"Loading model configuration from: {args.model_config}")
        try:
            model_config = load_model_config(args.model_config)
            db_config = load_database_config(args.model_config)
            
            logger.info(f"Model: {model_config.model_name}")
            logger.info(f"Database: {db_config.database} on {db_config.host}:{db_config.port}")
            
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {args.model_config}")
            logger.error(f"Error: {e}")
            return 1
        except Exception as e:
            logger.error(f"Failed to load model configuration: {e}")
            return 1
        
        # Step 2: Load methods configuration
        logger.info(f"Loading methods configuration from: {args.methods_config}")
        try:
            config_parser = ConfigParser()
            methods = config_parser.load_methods_config(args.methods_config)
            logger.info(f"Loaded {len(methods)} method(s) from configuration")
            
        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {args.methods_config}")
            logger.error(f"Error: {e}")
            return 1
        except Exception as e:
            logger.error(f"Failed to load methods configuration: {e}")
            return 1
        
        # Step 3: Validate methods
        logger.info("Validating method metadata...")
        validator = MetadataValidator()
        validation_results = validator.validate_methods(methods)
        
        # Check validation results
        failed_validations = [r for r in validation_results if not r.valid]
        if failed_validations:
            logger.error(f"Validation failed for {len(failed_validations)} method(s):")
            for result in failed_validations:
                logger.error(f"  - {result.method_name}: {', '.join(result.errors)}")
            return 1
        
        logger.info(f"All {len(methods)} method(s) validated successfully")
        
        # Step 4: Write to database (unless dry-run)
        if args.dry_run:
            logger.info("Dry-run mode: Skipping database write")
            logger.info("Validation completed successfully")
            return 0
        
        logger.info("Writing methods to database...")
        try:
            db_writer = DatabaseWriter(db_config)
            
            # Ensure database schema exists
            logger.info("Ensuring database schema exists...")
            db_writer.ensure_schema()
            
            # Convert MethodConfig to MethodMetadata
            from shared.models import MethodMetadata
            import json
            
            method_metadata_list = []
            for method in methods:
                # Serialize parameters to JSON
                params_json = json.dumps([
                    {
                        'name': p.name,
                        'type': p.type,
                        'description': p.description,
                        'required': p.required,
                        'default': p.default
                    }
                    for p in method.parameters
                ])
                
                metadata = MethodMetadata(
                    id=None,
                    name=method.name,
                    description=method.description,
                    parameters_json=params_json,
                    return_type=method.return_type,
                    module_path=method.module_path,
                    function_name=method.function_name,
                    created_at=None,
                    updated_at=None
                )
                method_metadata_list.append(metadata)
            
            # Upsert methods
            db_writer.upsert_methods(method_metadata_list)
            logger.info(f"Successfully registered {len(methods)} method(s) to database")
            
        except Exception as e:
            logger.error(f"Failed to write methods to database: {e}")
            logger.exception("Database error details:")
            return 1
        
        # Success
        # Success
        logger.info("=" * 60)
        logger.info("Method Registration Completed Successfully")
        logger.info("=" * 60)
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Error details:")
        return 1


if __name__ == '__main__':
    sys.exit(main())
