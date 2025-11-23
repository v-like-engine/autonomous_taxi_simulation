# Map Parsing - Quick Start Guide

## Installation

Dependencies are already installed:
```bash
pip3 install opencv-python opencv-contrib-python numpy scikit-image scipy
```

## Basic Usage (5 lines of code)

```python
from map_parsing import MapParser

parser = MapParser()
parser.load_map('/path/to/map.png')
map_data = parser.get_map_data()
```

## Common Use Cases

### 1. Get Speed Limit at Vehicle Position
```python
speed_limit = parser.get_speed_limit_at_point(vehicle_x, vehicle_y)
```

### 2. Find Which Lane Vehicle Is In
```python
lane = parser.get_nearest_lane(vehicle_x, vehicle_y)
if lane:
    centerline = lane['centerline']  # Follow this path
    direction = lane['direction']     # 'forward' or 'backward'
```

### 3. Get Road Network for Routing
```python
roads = parser.get_road_network()
for road in roads:
    points = road['points']    # Road path
    lanes = road['lanes']      # Number of lanes
    road_type = road['type']   # 'highway', 'main_road', 'minor_road'
```

### 4. Check if Point is Off-Road
```python
zone = parser.get_zone_at_point(x, y)
if zone and zone['type'] == 'prohibited':
    print("Vehicle is in prohibited area!")
```

### 5. Get All Intersections
```python
intersections = parser.get_intersections()
for intersection in intersections:
    pos = intersection['position']  # [x, y]
```

### 6. Visualize Map
```python
import cv2
vis = parser.visualize_map(show_zones=True, show_roads=True)
cv2.imwrite('visualization.png', vis)
```

### 7. Export Data to JSON
```python
parser.save_map_data('map_data.json')

# Load in another script:
import json
with open('map_data.json') as f:
    data = json.load(f)
```

## Data Structure Reference

### Zone Object
```python
{
    "type": "urban",           # prohibited, yard, urban, countryside, highway
    "polygon": [[x,y], ...],   # Zone boundary
    "speed_limit": 20,         # Base speed in km/h
    "max_speed": 80,           # Max without violation
    "area": 1000               # Square pixels
}
```

### Road Object
```python
{
    "id": 0,
    "points": [[x,y], ...],    # Road centerline
    "length": 150.5,           # Pixels
    "width": 20,               # Pixels
    "lanes": 2,                # Number of lanes
    "type": "main_road",       # highway, main_road, minor_road
    "direction": "two-way"     # one-way, two-way
}
```

### Lane Object
```python
{
    "id": 0,
    "road_id": 5,
    "centerline": [[x,y], ...], # Lane center path
    "width": 10,                # Pixels
    "direction": "forward"      # forward, backward
}
```

## Zone Types & Speed Limits

| Zone Type    | Speed Limit | Max (no violation) | Description |
|--------------|-------------|-------------------|-------------|
| Prohibited   | 0 km/h      | 0 km/h           | No driving  |
| Yard         | 10 km/h     | 30 km/h          | Residential |
| Urban        | 20 km/h     | 80 km/h          | City streets|
| Countryside  | 90 km/h     | 110 km/h         | Rural roads |
| Highway      | 110 km/h    | 130 km/h         | Highways    |

## API Methods

### Loading
- `load_map(file_path)` - Load from image file
- `load_map_from_array(image)` - Load from numpy array

### Queries
- `get_zone_at_point(x, y)` - Get zone at coordinates
- `get_speed_limit_at_point(x, y)` - Get speed limit
- `get_road_at_point(x, y)` - Get road segment
- `get_nearest_lane(x, y)` - Get closest lane

### Collections
- `get_zones_by_type(type)` - Filter zones by type
- `get_road_network()` - Get all roads
- `get_lanes()` - Get all lanes
- `get_intersections()` - Get all intersections

### Utilities
- `get_map_bounds()` - Returns (width, height)
- `get_theme()` - Returns 'light' or 'dark'
- `visualize_map()` - Create visualization
- `save_map_data(path)` - Export to JSON
- `pixel_to_meters(px)` - Convert pixels to meters
- `meters_to_pixels(m)` - Convert meters to pixels

## Examples for Each Agent

### Traffic Simulation (Agent 2)
```python
# Vehicle routing and lane following
roads = parser.get_road_network()
lanes = parser.get_lanes()

# For each vehicle:
lane = parser.get_nearest_lane(vehicle.x, vehicle.y)
speed_limit = parser.get_speed_limit_at_point(vehicle.x, vehicle.y)
```

### Sensors (Agent 4)
```python
# Environment sensing
road = parser.get_road_at_point(sensor_x, sensor_y)
zone = parser.get_zone_at_point(sensor_x, sensor_y)

# Check if on road
on_road = road is not None
```

### Frontend (Agent 5)
```python
# Display map
original = parser.get_original_image()
visualization = parser.visualize_map()
map_data = parser.get_map_data()
```

## Testing

Run tests:
```bash
python3 src/tests/test_map_parsing.py
python3 src/tests/test_map_parsing_enhanced.py
```

## Documentation

- Full docs: `MAP_PARSING_README.md`
- Usage examples: `src/map_parsing/example_usage.py`
- Module docs: `src/map_parsing/__init__.py`

## Support

For issues or questions:
1. Check `example_usage.py` for detailed examples
2. See `MAP_PARSING_README.md` for complete documentation
3. Review inline code documentation in source files
