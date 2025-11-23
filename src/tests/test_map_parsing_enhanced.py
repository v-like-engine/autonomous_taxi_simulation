"""
Enhanced tests for the map parsing system with better test maps.
"""

import sys
import os
import cv2
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from map_parsing import MapParser


def create_realistic_map():
    """
    Create a realistic map image similar to Google/Yandex Maps.
    """
    width, height = 800, 600
    image = np.ones((height, width, 3), dtype=np.uint8) * 242  # Light gray background

    # Add green park areas (BGR format)
    cv2.rectangle(image, (50, 50), (200, 200), (180, 230, 180), -1)  # Light green park
    cv2.rectangle(image, (600, 400), (750, 550), (160, 220, 160), -1)  # Another park

    # Add water body (light blue)
    cv2.circle(image, (650, 150), 80, (220, 180, 130), -1)

    # Add main roads (yellow/orange in Google Maps style - BGR: ~50, 200, 255)
    # Vertical main road
    cv2.rectangle(image, (350, 0), (380, 600), (80, 200, 250), -1)
    # Horizontal main road
    cv2.rectangle(image, (0, 280), (800, 310), (80, 200, 250), -1)

    # Add minor roads (white/light gray)
    cv2.rectangle(image, (150, 250), (157, 350), (255, 255, 255), -1)
    cv2.rectangle(image, (500, 150), (507, 250), (255, 255, 255), -1)

    # Add building areas (beige/tan)
    cv2.rectangle(image, (250, 100), (330, 180), (200, 220, 230), -1)
    cv2.rectangle(image, (420, 350), (550, 450), (200, 220, 230), -1)

    return image


def test_with_realistic_map():
    """Test with a realistic map."""
    print("\n=== Enhanced Test: Realistic Map ===")

    # Create realistic map
    test_image = create_realistic_map()

    # Save the test map for inspection
    cv2.imwrite('/home/user/autonomous_taxi_simulation/test_realistic_map.png', test_image)
    print("✓ Created realistic test map")

    # Create parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    # Get map data
    map_data = parser.get_map_data()

    print(f"✓ Theme: {parser.get_theme()}")
    print(f"✓ Dimensions: {parser.get_map_bounds()}")
    print(f"✓ Main zones: {len(map_data['zones']['main_zones'])}")
    print(f"✓ Road segments: {len(map_data['roads']['network'])}")
    print(f"✓ Lanes: {len(map_data['roads']['lanes'])}")
    print(f"✓ Intersections: {len(map_data['roads']['intersections'])}")

    # Zone breakdown
    zone_types = {}
    for zone in map_data['zones']['main_zones']:
        ztype = zone.get('type', 'unknown')
        zone_types[ztype] = zone_types.get(ztype, 0) + 1

    print("\nZone breakdown:")
    for ztype, count in zone_types.items():
        print(f"  - {ztype}: {count}")

    # Subzone breakdown
    print(f"\nSubzones:")
    print(f"  - Roads: {len(map_data['zones']['subzones']['roads'])}")
    print(f"  - Parking: {len(map_data['zones']['subzones']['parking'])}")
    print(f"  - Sidewalks: {len(map_data['zones']['subzones']['sidewalks'])}")

    # Test specific point queries
    print("\nPoint queries:")

    # Point on main road
    road = parser.get_road_at_point(365, 300)
    if road:
        print(f"  ✓ Road at intersection: type={road.get('type')}, width={road.get('width', 0):.1f}px")
    else:
        print(f"  - No road detected at (365, 300)")

    # Point in park
    zone = parser.get_zone_at_point(100, 100)
    if zone:
        print(f"  ✓ Zone at park: type={zone.get('type')}, speed={zone.get('speed_limit')} km/h")
    else:
        print(f"  - No special zone at park (100, 100)")

    # Speed limit queries
    speed_park = parser.get_speed_limit_at_point(100, 100)
    speed_road = parser.get_speed_limit_at_point(365, 300)
    speed_open = parser.get_speed_limit_at_point(450, 100)

    print(f"\nSpeed limits:")
    print(f"  - Park area: {speed_park} km/h")
    print(f"  - Main road: {speed_road} km/h")
    print(f"  - Open area: {speed_open} km/h")

    # Create visualization
    vis = parser.visualize_map(show_zones=True, show_roads=True)
    cv2.imwrite('/home/user/autonomous_taxi_simulation/test_realistic_map_visualization.png', vis)
    print(f"\n✓ Saved visualization")

    # Export data
    parser.save_map_data('/home/user/autonomous_taxi_simulation/test_realistic_map_data.json')
    print(f"✓ Saved map data")

    return True


def demonstrate_api_usage():
    """Demonstrate typical API usage."""
    print("\n=== API Usage Demonstration ===")

    # Create map
    test_image = create_realistic_map()

    # Initialize parser
    parser = MapParser()
    parser.load_map_from_array(test_image)

    print("Example 1: Get all highways")
    highways = parser.get_zones_by_type('highway')
    print(f"  Found {len(highways)} highway zones")

    print("\nExample 2: Get all urban zones")
    urban = parser.get_zones_by_type('urban')
    print(f"  Found {len(urban)} urban zones")

    print("\nExample 3: Get road network for routing")
    network = parser.get_road_network()
    print(f"  Road network has {len(network)} segments")

    print("\nExample 4: Get all lanes")
    lanes = parser.get_lanes()
    print(f"  Total lanes: {len(lanes)}")

    print("\nExample 5: Get intersections")
    intersections = parser.get_intersections()
    print(f"  Found {len(intersections)} intersections")

    print("\nExample 6: Convert units")
    pixels = 100
    meters = parser.pixel_to_meters(pixels)
    print(f"  {pixels} pixels = {meters} meters")

    print("\n✓ API demonstration complete")

    return True


if __name__ == '__main__':
    print("=" * 70)
    print("ENHANCED MAP PARSING TESTS")
    print("=" * 70)

    try:
        test_with_realistic_map()
        demonstrate_api_usage()

        print("\n" + "=" * 70)
        print("ALL ENHANCED TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print("\nOutput files:")
        print("  - test_realistic_map.png - Original test map")
        print("  - test_realistic_map_visualization.png - Visualization with zones and roads")
        print("  - test_realistic_map_data.json - Exported map data")

    except Exception as e:
        print(f"\n✗ Tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
