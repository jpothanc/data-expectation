#!/usr/bin/env python3
"""Main entry point for batch validation generator.

Usage:
    python -m generator.main apac
    python -m generator.main apac --custom-rules status_validation,isin_validation
    python -m generator.main apac --api-url http://localhost:5006
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.src.cli import ValidationCLI


def main():
    """Main entry point."""
    cli = ValidationCLI()
    cli.run()


if __name__ == "__main__":
    main()
