"""
Example usage of the Map Parsing system.
This demonstrates how other agents should use the map parsing functionality.
"""

import sys
import os

# For other agents: add src to path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from map_parsing import MapParser


def example_basic_usage():
    """
    Basic usage: Load a map and get basic information.
    """
    print("=" * 70)
    print("EXAMPLE 1: Basic Map Loading")
    print("=" * 70)

    # Create a map parser instance
    parser = MapParser()

    # Load a map from file
    # parser.load_map('/path/to/your/map.png')

    # Or load from numpy array (for programmatically generated maps)
    # parser.load_map_from_array(image_array)

    # Get basic information
    # theme = parser.get_theme()  # 'light' or 'dark'
    # width, height = parser.get_map_bounds()

    print("✓ Map parser initialized")
    print("  Use parser.load_map(path) to load a map image")


def example_zone_queries():
    """
    Example: Query zone information at specific points.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Zone Queries")
    print("=" * 70)

    print("""
# After loading a map:
parser = MapParser()
parser.load_map('map.png')

# Get zone at a specific point
zone = parser.get_zone_at_point(x=100, y=200)
if zone:
    zone_type = zone['type']  # 'prohibited', 'yard', 'urban', 'countryside', 'highway'
    speed_limit = zone['speed_limit']  # Speed limit in km/h
    max_speed = zone['max_speed']  # Max speed without violation

# Get speed limit at a point
speed = parser.get_speed_limit_at_point(x=100, y=200)

# Get all zones of a specific type
urban_zones = parser.get_zones_by_type('urban')
highways = parser.get_zones_by_type('highway')
prohibited = parser.get_zones_by_type('prohibited')
    """)


def example_road_queries():
    """
    Example: Query road and lane information.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Road and Lane Queries")
    print("=" * 70)

    print("""
# After loading a map:
parser = MapParser()
parser.load_map('map.png')

# Get road at a specific point
road = parser.get_road_at_point(x=100, y=200)
if road:
    road_type = road['type']  # 'highway', 'main_road', 'minor_road'
    width = road['width']  # Road width in pixels
    lanes = road['lanes']  # Number of lanes
    direction = road['direction']  # 'one-way' or 'two-way'

# Get nearest lane to a point (for vehicle positioning)
lane = parser.get_nearest_lane(x=100, y=200)
if lane:
    lane_id = lane['id']
    centerline = lane['centerline']  # List of [x, y] points
    lane_width = lane['width']
    direction = lane['direction']  # 'forward' or 'backward'

# Get complete road network (for routing)
network = parser.get_road_network()
for road in network:
    road_id = road['id']
    points = road['points']  # Path points
    length = road['length']  # Length in pixels

# Get all lanes (for traffic simulation)
lanes = parser.get_lanes()

# Get intersections (for traffic lights, etc.)
intersections = parser.get_intersections()
    """)


def example_full_map_data():
    """
    Example: Get complete map data structure.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Complete Map Data Structure")
    print("=" * 70)

    print("""
parser = MapParser()
parser.load_map('map.png')

# Get complete map data
map_data = parser.get_map_data()

# Structure:
{
    "zones": {
        "main_zones": [
            {
                "type": "urban",
                "polygon": [[x1, y1], [x2, y2], ...],
                "area": 1000,
                "speed_limit": 20,
                "max_speed": 80,
                "description": "Urban zone - 20 km/h base, 60 km/h on main roads"
            },
            ...
        ],
        "subzones": {
            "sidewalks": [...],
            "parking": [...],
            "roads": [...]
        }
    },
    "roads": {
        "network": [
            {
                "id": 0,
                "points": [[x1, y1], [x2, y2], ...],
                "length": 150.5,
                "width": 20,
                "lanes": 2,
                "type": "main_road",
                "direction": "two-way"
            },
            ...
        ],
        "lanes": [...],
        "intersections": [...],
        "crosswalks": [...]
    },
    "map_bounds": {
        "width": 800,
        "height": 600
    },
    "metadata": {
        "theme": "light",
        "scale_factor": 1.0,
        "source_file": "/path/to/map.png"
    }
}
    """)


def example_visualization():
    """
    Example: Create visualizations.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Visualization")
    print("=" * 70)

    print("""
parser = MapParser()
parser.load_map('map.png')

# Create visualization with zones and roads
vis_image = parser.visualize_map(show_zones=True, show_roads=True)

# Save visualization
import cv2
cv2.imwrite('map_visualization.png', vis_image)

# Get original image (for overlay operations)
original = parser.get_original_image()
    """)


def example_data_export():
    """
    Example: Export map data.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Data Export")
    print("=" * 70)

    print("""
parser = MapParser()
parser.load_map('map.png')

# Export to JSON for use by other systems
parser.save_map_data('map_data.json')

# Can be loaded by other agents using:
import json
with open('map_data.json', 'r') as f:
    map_data = json.load(f)
    """)


def example_unit_conversion():
    """
    Example: Convert between pixels and meters.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Unit Conversion")
    print("=" * 70)

    print("""
parser = MapParser()
parser.load_map('map.png')

# Convert pixels to meters
distance_m = parser.pixel_to_meters(100)  # pixels -> meters

# Convert meters to pixels
distance_px = parser.meters_to_pixels(50)  # meters -> pixels

# Note: Default conversion is 1 pixel = 1 meter
# This should be calibrated based on actual map scale
    """)


def example_for_traffic_agent():
    """
    Example: Typical usage for Traffic Simulation Agent.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 8: Usage for Traffic Simulation Agent (Agent 2)")
    print("=" * 70)

    print("""
# Traffic Agent needs: road network, lanes, intersections, speed limits

from map_parsing import MapParser

parser = MapParser()
parser.load_map('city_map.png')

# Get road network for vehicle routing
road_network = parser.get_road_network()
lanes = parser.get_lanes()
intersections = parser.get_intersections()

# For each vehicle, find which lane they're in
vehicle_x, vehicle_y = 100, 200
lane = parser.get_nearest_lane(vehicle_x, vehicle_y)

if lane:
    # Follow lane centerline
    path = lane['centerline']
    lane_direction = lane['direction']

# Get speed limit for vehicle position
speed_limit = parser.get_speed_limit_at_point(vehicle_x, vehicle_y)

# Check if vehicle is in prohibited zone
zone = parser.get_zone_at_point(vehicle_x, vehicle_y)
if zone and zone['type'] == 'prohibited':
    # Vehicle is off-road!
    pass
    """)


def example_for_sensor_agent():
    """
    Example: Typical usage for Sensor Simulation Agent.
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 9: Usage for Sensor Simulation Agent (Agent 4)")
    print("=" * 70)

    print("""
# Sensor Agent needs: map structure for obstacle detection, road boundaries

from map_parsing import MapParser
import numpy as np

parser = MapParser()
parser.load_map('city_map.png')

# Get map data for raycasting
map_data = parser.get_map_data()

# Check if point is on road (for obstacle detection)
def is_on_road(x, y):
    road = parser.get_road_at_point(x, y)
    return road is not None

# Get nearby road boundaries (for camera/LIDAR simulation)
def get_road_boundaries(vehicle_x, vehicle_y, range_pixels=50):
    lane = parser.get_nearest_lane(vehicle_x, vehicle_y)
    if lane:
        centerline = np.array(lane['centerline'])
        lane_width = lane['width']
        # Calculate boundaries...
        return centerline, lane_width
    return None, None

# Detect if there are buildings/obstacles nearby
zone = parser.get_zone_at_point(x, y)
if zone and zone.get('subtype') == 'building':
    # There's a building here
    pass
    """)


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("MAP PARSING SYSTEM - USAGE EXAMPLES")
    print("For Autonomous Taxi Simulation - Multi-Agent System")
    print("=" * 70)

    example_basic_usage()
    example_zone_queries()
    example_road_queries()
    example_full_map_data()
    example_visualization()
    example_data_export()
    example_unit_conversion()
    example_for_traffic_agent()
    example_for_sensor_agent()

    print("\n" + "=" * 70)
    print("For more details, see the module documentation:")
    print("  - map_parsing/__init__.py")
    print("  - map_parsing/map_loader.py")
    print("  - map_parsing/zone_detector.py")
    print("  - map_parsing/road_detector.py")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
