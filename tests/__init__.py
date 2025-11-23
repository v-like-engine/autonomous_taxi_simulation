"""
Test utilities and shared fixtures for autonomous taxi simulation tests.
"""
import os
import sys
from pathlib import Path

# Add src directory to path for imports
SRC_PATH = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

# Common test utilities
class TestHelpers:
    """Helper functions for tests"""

    @staticmethod
    def get_test_data_path():
        """Get path to test data directory"""
        return Path(__file__).parent / "test_data"

    @staticmethod
    def create_mock_map_image(width=800, height=600):
        """Create a simple mock map image for testing"""
        import numpy as np
        # Create a simple map with some roads (gray) and zones (colored)
        img = np.ones((height, width, 3), dtype=np.uint8) * 240  # Light gray background
        return img

    @staticmethod
    def create_mock_map_data():
        """Create mock map data structure"""
        return {
            "zones": {
                "main_zones": [
                    {"type": "urban", "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]], "speed_limit": 60}
                ],
                "subzones": {
                    "sidewalks": [],
                    "parking": [],
                    "roads": []
                }
            },
            "roads": {
                "network": [],
                "lanes": [],
                "intersections": [],
                "crosswalks": []
            },
            "map_bounds": {"width": 800, "height": 600}
        }
