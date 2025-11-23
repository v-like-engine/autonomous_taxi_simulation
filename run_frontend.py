#!/usr/bin/env python3
"""
Autonomous Taxi Simulation - Frontend Launcher
Simple script to start the Flask web application
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the app
from frontend.app import run_app

if __name__ == '__main__':
    print("=" * 60)
    print("Autonomous Taxi Simulation - Frontend")
    print("=" * 60)
    print()
    print("Starting Flask web application...")
    print("The application will be available at: http://localhost:5000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    try:
        run_app(host='0.0.0.0', port=5000, debug=True)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        print("Goodbye!")
    except Exception as e:
        print(f"\n\nError starting server: {e}")
        sys.exit(1)
