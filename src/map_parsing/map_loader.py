"""
Map loading and parsing coordination.
Loads map images and orchestrates the parsing process.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple
import json

from .image_processor import ImageProcessor


class MapLoader:
    """Handles loading and parsing of map images."""

    def __init__(self):
        """Initialize the map loader."""
        self.image_processor = ImageProcessor()
        self.original_image = None
        self.processed_image = None
        self.theme = None
        self.map_data = None
        self.scale_factor = 1.0
        self.file_path = None

    def load_from_file(self, file_path: str, max_dimension: int = 2048) -> bool:
        """
        Load a map image from file.

        Args:
            file_path: Path to the map image file
            max_dimension: Maximum dimension for the image (will resize if larger)

        Returns:
            True if successful, False otherwise
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Map file not found: {file_path}")

        if not path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            raise ValueError(f"Unsupported image format: {path.suffix}")

        # Load image
        self.original_image = cv2.imread(str(path))

        if self.original_image is None:
            raise ValueError(f"Failed to load image from: {file_path}")

        self.file_path = str(path)

        # Resize if too large
        self.original_image, self.scale_factor = self.image_processor.resize_image(
            self.original_image, max_dimension
        )

        # Detect theme
        self.theme = self.image_processor.detect_theme(self.original_image)

        # Update color ranges in processor
        self.image_processor.color_ranges = self.image_processor.get_color_ranges(self.theme)

        # Preprocess image
        self.processed_image = self.image_processor.preprocess_image(self.original_image)

        # Initialize map data structure
        self._initialize_map_data()

        return True

    def load_from_array(self, image: np.ndarray) -> bool:
        """
        Load a map image from a numpy array.

        Args:
            image: BGR image array

        Returns:
            True if successful
        """
        if image is None or len(image.shape) != 3:
            raise ValueError("Invalid image array")

        self.original_image = image.copy()
        self.file_path = None

        # Detect theme
        self.theme = self.image_processor.detect_theme(self.original_image)

        # Update color ranges in processor
        self.image_processor.color_ranges = self.image_processor.get_color_ranges(self.theme)

        # Preprocess image
        self.processed_image = self.image_processor.preprocess_image(self.original_image)

        # Initialize map data structure
        self._initialize_map_data()

        return True

    def _initialize_map_data(self):
        """Initialize the map data structure."""
        height, width = self.original_image.shape[:2]

        self.map_data = {
            "zones": {
                "main_zones": [],  # List of zone polygons with type and speed_limit
                "subzones": {
                    "sidewalks": [],
                    "parking": [],
                    "roads": []
                }
            },
            "roads": {
                "network": [],  # Graph structure for routing
                "lanes": [],  # Individual lane information
                "intersections": [],
                "crosswalks": []
            },
            "map_bounds": {
                "width": width,
                "height": height
            },
            "metadata": {
                "theme": self.theme,
                "scale_factor": self.scale_factor,
                "source_file": self.file_path
            }
        }

    def get_map_data(self) -> Dict:
        """
        Get the parsed map data.

        Returns:
            Dictionary containing all parsed map information
        """
        if self.map_data is None:
            raise ValueError("No map loaded. Call load_from_file() or load_from_array() first.")

        return self.map_data

    def get_original_image(self) -> np.ndarray:
        """Get the original loaded image."""
        return self.original_image

    def get_processed_image(self) -> np.ndarray:
        """Get the preprocessed image."""
        return self.processed_image

    def get_theme(self) -> str:
        """Get the detected theme (light or dark)."""
        return self.theme

    def get_map_bounds(self) -> Tuple[int, int]:
        """
        Get the map dimensions.

        Returns:
            Tuple of (width, height)
        """
        if self.original_image is None:
            return (0, 0)

        height, width = self.original_image.shape[:2]
        return (width, height)

    def save_map_data(self, output_path: str):
        """
        Save the parsed map data to a JSON file.

        Args:
            output_path: Path to save the JSON file
        """
        if self.map_data is None:
            raise ValueError("No map data to save")

        # Convert numpy arrays to lists for JSON serialization
        serializable_data = self._make_serializable(self.map_data)

        with open(output_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)

    def _make_serializable(self, data):
        """
        Recursively convert numpy arrays to lists for JSON serialization.

        Args:
            data: Data structure potentially containing numpy arrays

        Returns:
            Serializable data structure
        """
        if isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, dict):
            return {key: self._make_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(item) for item in data]
        elif isinstance(data, (np.int32, np.int64)):
            return int(data)
        elif isinstance(data, (np.float32, np.float64)):
            return float(data)
        else:
            return data

    def visualize_map(self, show_zones: bool = True, show_roads: bool = True) -> np.ndarray:
        """
        Create a visualization of the parsed map data.

        Args:
            show_zones: Whether to show zone boundaries
            show_roads: Whether to show road network

        Returns:
            Visualization image
        """
        if self.original_image is None:
            raise ValueError("No map loaded")

        # Create a copy of the original image
        vis_image = self.original_image.copy()

        if show_zones and self.map_data:
            # Draw main zones
            for zone in self.map_data["zones"]["main_zones"]:
                if "polygon" in zone:
                    polygon = np.array(zone["polygon"], dtype=np.int32)
                    zone_type = zone.get("type", "unknown")

                    # Choose color based on zone type
                    color_map = {
                        "prohibited": (0, 255, 0),      # Green
                        "yard": (0, 165, 255),          # Orange
                        "urban": (0, 0, 255),           # Red
                        "countryside": (255, 255, 0),   # Cyan
                        "highway": (255, 0, 255)        # Magenta
                    }
                    color = color_map.get(zone_type, (128, 128, 128))

                    # Draw polygon
                    cv2.polylines(vis_image, [polygon], True, color, 2)

        if show_roads and self.map_data:
            # Draw road network
            for road in self.map_data["roads"]["network"]:
                if "points" in road:
                    points = np.array(road["points"], dtype=np.int32)
                    cv2.polylines(vis_image, [points], False, (0, 255, 255), 2)

        return vis_image

    def get_pixel_to_meter_ratio(self) -> float:
        """
        Get the pixel to meter conversion ratio.
        This is a placeholder - in real applications, this would be calibrated.

        Returns:
            Approximate meters per pixel
        """
        # Default assumption: 1 pixel ≈ 1 meter for city maps at typical zoom
        # This should be calibrated based on the actual map scale
        return 1.0

    def pixel_to_meters(self, pixels: float) -> float:
        """
        Convert pixels to meters.

        Args:
            pixels: Distance in pixels

        Returns:
            Distance in meters
        """
        return pixels * self.get_pixel_to_meter_ratio()

    def meters_to_pixels(self, meters: float) -> float:
        """
        Convert meters to pixels.

        Args:
            meters: Distance in meters

        Returns:
            Distance in pixels
        """
        return meters / self.get_pixel_to_meter_ratio()
