"""
Tests for the map parsing system.
"""

import sys
import os
import cv2
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from map_parsing import MapParser


def create_test_map(width=500, height=500, theme='light'):
    """
    Create a simple test map image.

    Args:
        width: Image width
        height: Image height
        theme: 'light' or 'dark'

    Returns:
        Test map image
    """
    if theme == 'light':
        # White background
        image = np.ones((height, width, 3), dtype=np.uint8) * 255

        # Add some green areas (parks)
        cv2.rectangle(image, (50, 50), (150, 150), (100, 200, 100), -1)
        cv2.rectangle(image, (350, 350), (450, 450), (100, 200, 100), -1)

        # Add blue area (water)
        cv2.circle(image, (400, 100), 50, (200, 150, 100), -1)

        # Add yellow roads (main roads)
        cv2.rectangle(image, (200, 0), (220, 500), (0, 200, 255), -1)  # Vertical main road
        cv2.rectangle(image, (0, 250), (500, 270), (0, 200, 255), -1)  # Horizontal main road

        # Add gray roads (minor roads)
        cv2.rectangle(image, (100, 200), (105, 300), (150, 150, 150), -1)  # Minor road
        cv2.rectangle(image, (300, 200), (305, 300), (150, 150, 150), -1)  # Minor road

    else:  # dark theme
        # Dark background
        image = np.ones((height, width, 3), dtype=np.uint8) * 50

        # Add some dark green areas (parks)
        cv2.rectangle(image, (50, 50), (150, 150), (30, 80, 30), -1)
        cv2.rectangle(image, (350, 350), (450, 450), (30, 80, 30), -1)

        # Add dark blue area (water)
        cv2.circle(image, (400, 100), 50, (80, 50, 30), -1)

        # Add yellow roads (dimmer in dark mode)
        cv2.rectangle(image, (200, 0), (220, 500), (0, 150, 200), -1)  # Vertical main road
        cv2.rectangle(image, (0, 250), (500, 270), (0, 150, 200), -1)  # Horizontal main road

        # Add gray roads
        cv2.rectangle(image, (100, 200), (105, 300), (80, 80, 80), -1)  # Minor road
        cv2.rectangle(image, (300, 200), (305, 300), (80, 80, 80), -1)  # Minor road

    return image


def test_basic_loading():
    """Test basic map loading from array."""
    print("\n=== Test 1: Basic Map Loading ===")

    # Create test map
    test_image = create_test_map(theme='light')

    # Create parser
    parser = MapParser()

    # Load map
    success = parser.load_map_from_array(test_image)

    if success:
        print("✓ Map loaded successfully")
    else:
        print("✗ Failed to load map")
        return False

    # Check theme detection
    theme = parser.get_theme()
    print(f"✓ Detected theme: {theme}")

    # Check map bounds
    width, height = parser.get_map_bounds()
    print(f"✓ Map dimensions: {width}x{height}")

    return True


def test_zone_detection():
    """Test zone detection."""
    print("\n=== Test 2: Zone Detection ===")

    # Create test map
    test_image = create_test_map(theme='light')

    # Create parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    # Get zones
    map_data = parser.get_map_data()
    zones = map_data['zones']['main_zones']

    print(f"✓ Detected {len(zones)} main zones")

    # Check for prohibited zones (parks/water)
    prohibited_zones = parser.get_zones_by_type('prohibited')
    print(f"✓ Found {len(prohibited_zones)} prohibited zones")

    # Test point queries
    # Point in park area
    zone_at_park = parser.get_zone_at_point(100, 100)
    if zone_at_park:
        print(f"✓ Zone at park (100, 100): {zone_at_park.get('type', 'unknown')}")

    # Point in open area
    zone_at_open = parser.get_zone_at_point(300, 100)
    if zone_at_open:
        print(f"✓ Zone at open area (300, 100): {zone_at_open.get('type', 'unknown')}")

    # Speed limit query
    speed_limit = parser.get_speed_limit_at_point(300, 100)
    print(f"✓ Speed limit at (300, 100): {speed_limit} km/h")

    return True


def test_road_detection():
    """Test road detection."""
    print("\n=== Test 3: Road Detection ===")

    # Create test map
    test_image = create_test_map(theme='light')

    # Create parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    # Get road data
    map_data = parser.get_map_data()
    roads = map_data['roads']

    print(f"✓ Detected {len(roads['network'])} road segments")
    print(f"✓ Detected {len(roads['lanes'])} lanes")
    print(f"✓ Detected {len(roads['intersections'])} intersections")

    # Test road query
    road_at_point = parser.get_road_at_point(210, 250)
    if road_at_point:
        print(f"✓ Road at (210, 250): {road_at_point.get('type', 'unknown')}")
        print(f"  - Width: {road_at_point.get('width', 0):.1f} pixels")
        print(f"  - Lanes: {road_at_point.get('lanes', 0)}")

    # Test lane query
    lane = parser.get_nearest_lane(210, 250)
    if lane:
        print(f"✓ Nearest lane at (210, 250): Lane {lane.get('id', -1)}")

    return True


def test_dark_theme():
    """Test dark theme detection."""
    print("\n=== Test 4: Dark Theme ===")

    # Create dark theme map
    test_image = create_test_map(theme='dark')

    # Create parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    # Check theme
    theme = parser.get_theme()
    print(f"✓ Detected theme: {theme}")

    if theme != 'dark':
        print("✗ Failed to detect dark theme")
        return False

    # Get map data
    map_data = parser.get_map_data()
    print(f"✓ Detected {len(map_data['zones']['main_zones'])} zones in dark theme")
    print(f"✓ Detected {len(map_data['roads']['network'])} roads in dark theme")

    return True


def test_visualization():
    """Test map visualization."""
    print("\n=== Test 5: Visualization ===")

    # Create test map
    test_image = create_test_map(theme='light')

    # Create parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    # Create visualization
    vis_image = parser.visualize_map(show_zones=True, show_roads=True)

    if vis_image is not None:
        print(f"✓ Created visualization: {vis_image.shape}")

        # Save visualization
        output_path = '/home/user/autonomous_taxi_simulation/test_map_visualization.png'
        cv2.imwrite(output_path, vis_image)
        print(f"✓ Saved visualization to {output_path}")
    else:
        print("✗ Failed to create visualization")
        return False

    return True


def test_data_export():
    """Test data export to JSON."""
    print("\n=== Test 6: Data Export ===")

    # Create test map
    test_image = create_test_map(theme='light')

    # Create parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    # Export to JSON
    output_path = '/home/user/autonomous_taxi_simulation/test_map_data.json'
    try:
        parser.save_map_data(output_path)
        print(f"✓ Saved map data to {output_path}")

        # Check file exists
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✓ File size: {file_size} bytes")
        else:
            print("✗ File was not created")
            return False

    except Exception as e:
        print(f"✗ Failed to export data: {e}")
        return False

    return True


def test_unit_conversions():
    """Test pixel to meter conversions."""
    print("\n=== Test 7: Unit Conversions ===")

    # Create test map
    test_image = create_test_map(theme='light')

    # Create parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    # Test conversions
    pixels = 100
    meters = parser.pixel_to_meters(pixels)
    print(f"✓ {pixels} pixels = {meters} meters")

    meters = 50
    pixels = parser.meters_to_pixels(meters)
    print(f"✓ {meters} meters = {pixels} pixels")

    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("MAP PARSING SYSTEM TESTS")
    print("=" * 60)

    tests = [
        ("Basic Loading", test_basic_loading),
        ("Zone Detection", test_zone_detection),
        ("Road Detection", test_road_detection),
        ("Dark Theme", test_dark_theme),
        ("Visualization", test_visualization),
        ("Data Export", test_data_export),
        ("Unit Conversions", test_unit_conversions)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
