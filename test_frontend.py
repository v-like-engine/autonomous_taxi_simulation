#!/usr/bin/env python3
"""
Frontend Test Script
Quick tests to verify the frontend is working correctly
"""

import sys
import os

sys.path.insert(0, 'src')

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    try:
        from frontend.app import app, socketio, sim_state
        from frontend.routes import register_routes
        print("✓ All modules import successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_routes():
    """Test that routes are registered"""
    print("\nTesting routes...")
    try:
        from frontend.app import app
        routes = list(app.url_map.iter_rules())
        print(f"✓ {len(routes)} routes registered:")
        for route in routes:
            if route.endpoint != 'static':
                print(f"  - {route.rule} [{', '.join(route.methods - {'HEAD', 'OPTIONS'})}]")
        return True
    except Exception as e:
        print(f"✗ Route test failed: {e}")
        return False

def test_static_files():
    """Test that static files exist"""
    print("\nTesting static files...")
    files_to_check = [
        'static/css/blueprint.css',
        'static/css/style.css',
        'static/js/main.js',
        'static/js/map_viewer.js',
        'static/js/editor.js',
        'static/js/controls.js',
        'static/js/animation.js',
        'templates/index.html',
        'templates/editor.html',
        'templates/simulation.html'
    ]

    all_exist = True
    for file in files_to_check:
        if os.path.exists(file):
            size = os.path.getsize(file) / 1024
            print(f"✓ {file} ({size:.1f} KB)")
        else:
            print(f"✗ {file} - NOT FOUND")
            all_exist = False

    return all_exist

def test_demo_map():
    """Test that demo map exists"""
    print("\nTesting demo map...")
    map_json = 'data/maps/demo_map.json'
    map_png = 'data/maps/demo_map.png'

    all_exist = True
    if os.path.exists(map_json):
        print(f"✓ {map_json}")
    else:
        print(f"✗ {map_json} - NOT FOUND")
        all_exist = False

    if os.path.exists(map_png):
        print(f"✓ {map_png}")
    else:
        print(f"✗ {map_png} - NOT FOUND")
        all_exist = False

    return all_exist

def test_flask_config():
    """Test Flask configuration"""
    print("\nTesting Flask configuration...")
    try:
        from frontend.app import app
        print(f"✓ Template folder: {app.template_folder}")
        print(f"✓ Static folder: {app.static_folder}")
        print(f"✓ Secret key configured: {bool(app.config.get('SECRET_KEY'))}")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Autonomous Taxi Simulation - Frontend Tests")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Routes", test_routes()))
    results.append(("Static Files", test_static_files()))
    results.append(("Demo Map", test_demo_map()))
    results.append(("Flask Config", test_flask_config()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name:20s} {status}")

    all_passed = all(passed for _, passed in results)

    print("=" * 60)
    if all_passed:
        print("✓ All tests passed! Frontend is ready to run.")
        print("\nTo start the server, run:")
        print("  python3 run_frontend.py")
        return 0
    else:
        print("✗ Some tests failed. Please check the output above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
