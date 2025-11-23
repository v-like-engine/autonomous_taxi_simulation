"""
Map Parsing Module

This module provides functionality for loading, parsing, and analyzing map images.
It supports automatic detection of zones, roads, lanes, and other map features.

Main Components:
- MapLoader: Load and manage map images
- ZoneDetector: Detect and classify zones (prohibited, yard, urban, countryside, highway)
- RoadDetector: Detect roads, lanes, and build routing network
- ImageProcessor: Low-level image processing utilities

Example Usage:
    from map_parsing import MapParser

    # Create parser and load map
    parser = MapParser()
    parser.load_map('path/to/map.png')

    # Get parsed data
    map_data = parser.get_map_data()

    # Query specific information
    zone = parser.get_zone_at_point(100, 200)
    speed_limit = parser.get_speed_limit_at_point(100, 200)
    road = parser.get_road_at_point(150, 250)
"""

from .map_loader import MapLoader
from .zone_detector import ZoneDetector
from .road_detector import RoadDetector
from .image_processor import ImageProcessor


class MapParser:
    """
    High-level interface for map parsing.
    Combines all map parsing functionality into a single easy-to-use class.
    """

    def __init__(self):
        """Initialize the map parser."""
        self.image_processor = ImageProcessor()
        self.map_loader = MapLoader()
        self.zone_detector = None
        self.road_detector = None
        self._map_loaded = False

    def load_map(self, file_path: str, max_dimension: int = 2048) -> bool:
        """
        Load and parse a map image from file.

        Args:
            file_path: Path to the map image file
            max_dimension: Maximum dimension for the image

        Returns:
            True if successful

        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is not supported
        """
        # Load the map
        success = self.map_loader.load_from_file(file_path, max_dimension)

        if not success:
            return False

        # Initialize detectors
        self.zone_detector = ZoneDetector(self.image_processor)
        self.road_detector = RoadDetector(self.image_processor)

        # Perform detection
        self._parse_map()

        self._map_loaded = True
        return True

    def load_map_from_array(self, image) -> bool:
        """
        Load and parse a map from a numpy array.

        Args:
            image: BGR image array

        Returns:
            True if successful
        """
        # Load the map
        success = self.map_loader.load_from_array(image)

        if not success:
            return False

        # Initialize detectors
        self.zone_detector = ZoneDetector(self.image_processor)
        self.road_detector = RoadDetector(self.image_processor)

        # Perform detection
        self._parse_map()

        self._map_loaded = True
        return True

    def _parse_map(self):
        """Parse the loaded map (internal method)."""
        processed_image = self.map_loader.get_processed_image()

        # Detect roads first (needed for zone classification)
        road_data = self.road_detector.detect_roads(processed_image)

        # Detect zones (using road mask for better classification)
        road_mask = self.road_detector.get_road_mask()
        zone_data = self.zone_detector.detect_all_zones(processed_image, road_mask)

        # Update map loader's data
        self.map_loader.map_data["zones"] = zone_data
        self.map_loader.map_data["roads"] = road_data

    def get_map_data(self):
        """
        Get the complete parsed map data.

        Returns:
            Dictionary containing all parsed map information
        """
        self._check_loaded()
        return self.map_loader.get_map_data()

    def get_zone_at_point(self, x: int, y: int):
        """
        Get the zone at a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Zone dictionary or None
        """
        self._check_loaded()
        return self.zone_detector.get_zone_at_point(x, y)

    def get_speed_limit_at_point(self, x: int, y: int) -> int:
        """
        Get the speed limit at a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Speed limit in km/h
        """
        self._check_loaded()
        return self.zone_detector.get_speed_limit_at_point(x, y)

    def get_road_at_point(self, x: int, y: int):
        """
        Get the road segment at a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Road segment dictionary or None
        """
        self._check_loaded()
        return self.road_detector.get_road_at_point(x, y)

    def get_nearest_lane(self, x: int, y: int):
        """
        Get the nearest lane to a point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Lane dictionary or None
        """
        self._check_loaded()
        return self.road_detector.get_nearest_lane(x, y)

    def get_zones_by_type(self, zone_type: str):
        """
        Get all zones of a specific type.

        Args:
            zone_type: Type of zone ('prohibited', 'yard', 'urban', 'countryside', 'highway')

        Returns:
            List of zone dictionaries
        """
        self._check_loaded()
        return self.zone_detector.get_zones_by_type(zone_type)

    def get_map_bounds(self):
        """
        Get the map dimensions.

        Returns:
            Tuple of (width, height)
        """
        self._check_loaded()
        return self.map_loader.get_map_bounds()

    def get_theme(self) -> str:
        """
        Get the detected map theme.

        Returns:
            'light' or 'dark'
        """
        self._check_loaded()
        return self.map_loader.get_theme()

    def save_map_data(self, output_path: str):
        """
        Save the parsed map data to a JSON file.

        Args:
            output_path: Path to save the JSON file
        """
        self._check_loaded()
        self.map_loader.save_map_data(output_path)

    def visualize_map(self, show_zones: bool = True, show_roads: bool = True):
        """
        Create a visualization of the parsed map.

        Args:
            show_zones: Whether to show zone boundaries
            show_roads: Whether to show road network

        Returns:
            Visualization image (BGR numpy array)
        """
        self._check_loaded()
        return self.map_loader.visualize_map(show_zones, show_roads)

    def get_original_image(self):
        """Get the original loaded map image."""
        self._check_loaded()
        return self.map_loader.get_original_image()

    def get_road_network(self):
        """Get the road network graph."""
        self._check_loaded()
        return self.map_loader.map_data["roads"]["network"]

    def get_lanes(self):
        """Get all detected lanes."""
        self._check_loaded()
        return self.map_loader.map_data["roads"]["lanes"]

    def get_intersections(self):
        """Get all detected intersections."""
        self._check_loaded()
        return self.map_loader.map_data["roads"]["intersections"]

    def pixel_to_meters(self, pixels: float) -> float:
        """
        Convert pixels to meters.

        Args:
            pixels: Distance in pixels

        Returns:
            Distance in meters
        """
        self._check_loaded()
        return self.map_loader.pixel_to_meters(pixels)

    def meters_to_pixels(self, meters: float) -> float:
        """
        Convert meters to pixels.

        Args:
            meters: Distance in meters

        Returns:
            Distance in pixels
        """
        self._check_loaded()
        return self.map_loader.meters_to_pixels(meters)

    def _check_loaded(self):
        """Check if a map has been loaded."""
        if not self._map_loaded:
            raise ValueError("No map loaded. Call load_map() first.")


# Export main classes
__all__ = [
    'MapParser',
    'MapLoader',
    'ZoneDetector',
    'RoadDetector',
    'ImageProcessor'
]

# Version
__version__ = '1.0.0'
