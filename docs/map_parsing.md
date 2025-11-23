# Map Parsing Documentation

Documentation for the Map Parsing module (Agent 1).

## Overview

The Map Parsing module is responsible for loading map images and automatically detecting zones, roads, lanes, and other features needed for the simulation.

## Components

### MapLoader

Loads and preprocesses map images.

**Key Features:**
- Supports multiple image formats (PNG, JPG, BMP)
- Handles both light and dark theme maps
- Validates image quality and dimensions
- Preprocesses images for detection algorithms

**Usage:**
```python
from src.map_parsing.map_loader import MapLoader

loader = MapLoader()
image = loader.load("maps/city_map.png")
```

### ZoneDetector

Automatically detects zones from map images using computer vision.

**Detected Zones:**
1. **Prohibited zones** (forests, parks, water) - Green/blue areas
2. **Yard areas** - Residential zones, 10 km/h limit
3. **Urban zones** - City areas, 60 km/h limit
4. **Countryside zones** - Rural areas, 90 km/h limit
5. **Highway zones** - Highway areas, 110 km/h limit

**Detection Method:**
- Color-based segmentation
- Contour detection for boundaries
- Polygon simplification
- Zone classification using color ranges

**Usage:**
```python
from src.map_parsing.zone_detector import ZoneDetector

detector = ZoneDetector()
zones = detector.detect_zones(image)
```

### RoadDetector

Detects roads, lanes, and creates a road network graph.

**Detected Features:**
- Road centerlines
- Road width (for lane calculation)
- Road directions (one-way vs two-way)
- Intersections
- Crosswalks
- Lane divisions

**Detection Method:**
- Morphological operations (erosion, dilation)
- Skeleton extraction for road centerlines
- Width analysis along roads
- Intersection detection at road crossings
- Graph construction for routing

**Usage:**
```python
from src.map_parsing.road_detector import RoadDetector

detector = RoadDetector()
roads = detector.detect_roads(image, zones)
```

### ImageProcessor

Image processing utilities for map preprocessing.

**Functions:**
- `preprocess()`: Prepare image for detection
- `detect_theme()`: Determine if map is light or dark theme
- `color_segmentation()`: Segment image by color
- `morphological_ops()`: Apply morphological operations
- `extract_contours()`: Extract zone boundaries

## Output Data Structure

```python
{
    "zones": {
        "main_zones": [
            {
                "type": "urban",
                "polygon": [[x1, y1], [x2, y2], ...],
                "speed_limit": 60,
                "area": float
            }
        ],
        "subzones": {
            "sidewalks": [...],
            "parking": [...],
            "roads": [...]
        }
    },
    "roads": {
        "network": NetworkX.Graph,
        "lanes": [
            {
                "id": "lane_1",
                "points": [[x1, y1], [x2, y2], ...],
                "width": float,
                "direction": "forward|backward|both"
            }
        ],
        "intersections": [
            {
                "position": [x, y],
                "connected_roads": ["road_1", "road_2", ...]
            }
        ],
        "crosswalks": [
            {
                "start": [x1, y1],
                "end": [x2, y2],
                "road_id": "road_1"
            }
        ]
    },
    "map_bounds": {
        "width": 1920,
        "height": 1080
    }
}
```

## Configuration

Edit `config/map_parsing.yaml`:

```yaml
zone_detection:
  prohibited_color_ranges:
    green: [[35, 40, 40], [85, 255, 255]]  # HSV ranges
    blue: [[90, 40, 40], [130, 255, 255]]

  urban_color_ranges:
    gray: [[0, 0, 100], [180, 30, 200]]

road_detection:
  min_road_width: 5  # pixels
  max_road_width: 100
  intersection_threshold: 10  # pixels

preprocessing:
  resize_max: 2048
  blur_kernel: 5
  theme_threshold: 128
```

## Best Practices

1. **Map Quality**: Use high-resolution images (≥1024x768)
2. **Color Contrast**: Ensure good color contrast between zones
3. **Verification**: Always verify automatic detection results
4. **Manual Editing**: Use map editor to fix detection errors

## Troubleshooting

**Issue: Zones not detected correctly**
- Adjust color ranges in configuration
- Check if map theme (light/dark) is detected correctly
- Try preprocessing with different parameters

**Issue: Roads broken or incomplete**
- Increase max_road_width if roads are wide
- Adjust morphological operation parameters
- Manually connect road segments in editor

**Issue: Performance is slow**
- Reduce image resolution
- Disable detailed detection options
- Use simpler maps

## API Reference

See [API Documentation](api.md#map-parsing-api) for complete API reference.
