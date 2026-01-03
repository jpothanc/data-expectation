"""Logging configuration with daily log files."""

import logging
import logging.handlers
import os
import json
from pathlib import Path
from datetime import datetime


def setup_logging(verbose=False, log_dir=None):
    """
    Setup logging with daily log files and console output.
    
    Args:
        verbose: If True, use DEBUG level, otherwise INFO
        log_dir: Optional log directory path. If None, reads from config.json or uses default 'log'
    """
    # Resolve generator directory path
    generator_dir = Path(__file__).parent.parent.parent
    
    # Get log directory from config or use default
    if log_dir is None:
        try:
            # Try to load config.json from generator directory
            config_path = generator_dir / 'config.json'
            
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                log_dir = config.get('logging', {}).get('log_dir', 'log')
            else:
                log_dir = 'log'
        except Exception:
            log_dir = 'log'
    
    # Resolve log directory path (relative to generator directory)
    log_path = Path(log_dir)
    
    # If relative path, make it relative to generator directory
    if not log_path.is_absolute():
        log_path = generator_dir / log_path
    
    # Create log directory if it doesn't exist
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Set up log level
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create daily log file name: generator_YYYY-MM-DD.log
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = log_path / f"generator_{today}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler - daily log file
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when='midnight',
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    file_handler.suffix = '%Y-%m-%d'  # Format: generator_YYYY-MM-DD.log
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log the log file location
    logging.info(f"Logging to file: {log_file}")
    logging.info(f"Log directory: {log_path}")
    
    return str(log_file), str(log_path)

