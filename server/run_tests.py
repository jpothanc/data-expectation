#!/usr/bin/env python3
"""Simple test runner script for server tests."""

import sys
import subprocess
import os

def main():
    """Run pytest with appropriate options."""
    # Change to server directory
    server_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(server_dir)
    
    # Build pytest command
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short'
    ]
    
    # Add coverage if requested
    if '--coverage' in sys.argv or '-c' in sys.argv:
        cmd.extend(['--cov=.', '--cov-report=term-missing', '--cov-report=html'])
    
    # Add other pytest arguments
    pytest_args = [arg for arg in sys.argv[1:] if arg not in ['--coverage', '-c']]
    cmd.extend(pytest_args)
    
    # Run tests
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()


