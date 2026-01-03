"""Helper functions for reading configuration from config.json."""

import os
import json
import logging

logger = logging.getLogger(__name__)


def get_config_path():
    """
    Get the path to config.json, checking generator directory first, then parent directory.
    
    Returns:
        str: Path to config.json file
        
    Raises:
        FileNotFoundError: If config.json is not found in either location
    """
    # From generator/src/config/config_helper.py, go up to generator/config.json
    generator_config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'config.json'
    )
    # Also check parent directory (instruments_ge_app/config.json)
    parent_config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        'config.json'
    )
    
    if os.path.exists(generator_config_path):
        return generator_config_path
    elif os.path.exists(parent_config_path):
        return parent_config_path
    else:
        raise FileNotFoundError(
            f"Config file not found. Tried:\n"
            f"  - {generator_config_path}\n"
            f"  - {parent_config_path}"
        )


def load_config():
    """
    Load configuration from config.json.
    
    Returns:
        dict: Configuration dictionary
    """
    config_path = get_config_path()
    logger.info(f"Loading config from: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_api_base_url():
    """
    Get API base URL from config.json.
    
    Returns:
        str: API base URL (defaults to 'http://127.0.0.1:5006' if not configured)
    """
    try:
        config = load_config()
        api_url = config.get('api', {}).get('base_url', 'http://127.0.0.1:5006')
        logger.info(f"Using API base URL from config: {api_url}")
        return api_url
    except Exception as e:
        logger.warning(f"Could not load API URL from config: {e}. Using default: http://127.0.0.1:5006")
        return 'http://127.0.0.1:5006'

