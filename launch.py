#!/usr/bin/env python3
"""
Autonomous Taxi Simulation - Main Launcher

This script launches the complete autonomous taxi simulation system,
integrating all 6 agent components:
1. Map Parsing
2. Traffic Simulation
3. Frontend (Web UI)
4. Sensor Simulation
5. RL Agent
6. Testing & Documentation

Usage:
    python launch.py                    # Launch with default settings
    python launch.py --host 0.0.0.0    # Launch accessible from network
    python launch.py --port 8080       # Use custom port
    python launch.py --debug           # Enable debug mode
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def setup_logging(debug=False):
    """Configure logging for the application"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('simulation.log')
        ]
    )

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("=" * 60)
    print("Checking dependencies...")
    print("=" * 60)

    required_modules = [
        ('numpy', 'NumPy'),
        ('cv2', 'OpenCV'),
        ('flask', 'Flask'),
        ('torch', 'PyTorch'),
        ('PIL', 'Pillow'),
        ('scipy', 'SciPy'),
    ]

    missing = []
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"✓ {display_name:20s} - OK")
        except ImportError:
            print(f"✗ {display_name:20s} - MISSING")
            missing.append(display_name)

    if missing:
        print("\n" + "=" * 60)
        print("ERROR: Missing dependencies!")
        print("=" * 60)
        print("\nPlease install missing packages:")
        print("  pip install -r requirements.txt")
        print("\nMissing:", ", ".join(missing))
        return False

    print("=" * 60)
    print("✓ All dependencies installed!")
    print("=" * 60)
    return True

def verify_components():
    """Verify all agent components are available"""
    print("\n" + "=" * 60)
    print("Verifying agent components...")
    print("=" * 60)

    components = [
        ('src.map_parsing', 'Agent 1: Map Parsing'),
        ('src.traffic_simulation', 'Agent 2: Traffic Simulation'),
        ('src.frontend', 'Agent 3: Frontend'),
        ('src.sensors', 'Agent 4: Sensor Simulation'),
        ('src.rl_agent', 'Agent 5: RL Agent'),
    ]

    all_ok = True
    for module_name, display_name in components:
        try:
            __import__(module_name)
            print(f"✓ {display_name:35s} - OK")
        except ImportError as e:
            print(f"✗ {display_name:35s} - ERROR: {e}")
            all_ok = False

    print("=" * 60)
    if all_ok:
        print("✓ All components available!")
    else:
        print("✗ Some components missing!")
    print("=" * 60)
    return all_ok

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'data/maps',
        'data/models',
        'logs',
        'checkpoints/rl_agent',
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print(f"\n✓ Created necessary directories")

def launch_application(host='127.0.0.1', port=5000, debug=False):
    """Launch the Flask application"""
    print("\n" + "=" * 60)
    print("LAUNCHING AUTONOMOUS TAXI SIMULATION")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Debug: {debug}")
    print(f"\n  Access at: http://{host}:{port}")
    print("\n" + "=" * 60)
    print("Starting server...")
    print("=" * 60)
    print("\nPress Ctrl+C to stop the server\n")

    try:
        from frontend.app import app, socketio

        # Run the application with SocketIO support
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,
            log_output=debug
        )
    except ImportError as e:
        print(f"\nERROR: Could not import Flask application: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"\nERROR: Could not start server: {e}")
        return False

    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Launch the Autonomous Taxi Simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch.py                     # Default: localhost:5000
  python launch.py --port 8080        # Custom port
  python launch.py --host 0.0.0.0     # Accessible from network
  python launch.py --debug            # Enable debug mode
        """
    )

    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host address to bind to (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to listen on (default: 5000)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip dependency and component checks'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.debug)

    # Print banner
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  AUTONOMOUS TAXI SIMULATION  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("║" + "  A Multi-Agent RL Testing Environment  ".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    # Run checks unless skipped
    if not args.skip_checks:
        if not check_dependencies():
            sys.exit(1)

        if not verify_components():
            print("\nWARNING: Some components are missing!")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)

    # Create necessary directories
    create_directories()

    # Launch the application
    try:
        launch_application(args.host, args.port, args.debug)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Shutting down...")
        print("=" * 60)
        print("\nGoodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        if args.debug:
            raise
        sys.exit(1)

if __name__ == '__main__':
    main()
