#!/usr/bin/env python3
"""
Startup script for Nkolo Pass application.
This script initializes the database and creates default data.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Initialize the application for production deployment"""
    try:
        # Import after setting up the path
        from app import app, init_database
        
        print("Starting Nkolo Pass application initialization...")
        
        # Initialize database
        init_database()
        
        print("Application initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during application initialization: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()