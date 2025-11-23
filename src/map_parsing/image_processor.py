"""
Image processing utilities for map parsing.
Supports both light and dark theme maps (Yandex/Google Maps style).
"""

import cv2
import numpy as np
from typing import Tuple, Dict, Optional


class ImageProcessor:
    """Handles image preprocessing and theme detection for map images."""

    def __init__(self):
        """Initialize the image processor."""
        self.theme = None  # Will be 'light' or 'dark'
        self.color_ranges = None

    def detect_theme(self, image: np.ndarray) -> str:
        """
        Detect if the map uses light or dark theme.

        Args:
            image: BGR image from OpenCV

        Returns:
            'light' or 'dark'
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Calculate average brightness
        avg_brightness = np.mean(gray)

        # Threshold: if average brightness > 127, it's likely a light theme
        if avg_brightness > 127:
            self.theme = 'light'
        else:
            self.theme = 'dark'

        return self.theme

    def get_color_ranges(self, theme: Optional[str] = None) -> Dict[str, Dict[str, Tuple]]:
        """
        Get color ranges for different map elements based on theme.

        Args:
            theme: 'light' or 'dark', if None uses detected theme

        Returns:
            Dictionary of color ranges for different map elements
        """
        if theme is None:
            theme = self.theme

        if theme == 'light':
            # Light theme (Google Maps / Yandex Maps light mode)
            return {
                # Prohibited zones
                'forest_parks': {
                    'lower': np.array([40, 20, 150]),   # Light green (HSV ~60, 55, 230)
                    'upper': np.array([80, 150, 255])
                },
                'water': {
                    'lower': np.array([90, 50, 130]),   # Blue (HSV ~103, 104, 220)
                    'upper': np.array([120, 200, 255])
                },
                # Roads
                'roads_yellow': {
                    'lower': np.array([15, 100, 200]),  # Yellow roads (HSV ~21, 173, 250)
                    'upper': np.array([30, 255, 255])
                },
                'roads_white': {
                    'lower': np.array([0, 0, 240]),     # White roads (HSV 0, 0, 255)
                    'upper': np.array([180, 20, 255])
                },
                'roads_gray': {
                    'lower': np.array([0, 0, 180]),     # Gray roads (HSV 0, 0, 200)
                    'upper': np.array([180, 30, 230])
                },
                # Parking and sidewalks
                'parking': {
                    'lower': np.array([0, 0, 160]),     # Light gray areas
                    'upper': np.array([180, 25, 210])
                },
                # Buildings/Urban (beige/tan colors)
                'urban': {
                    'lower': np.array([10, 20, 150]),
                    'upper': np.array([30, 100, 255])
                }
            }
        else:
            # Dark theme (Google Maps / Yandex Maps dark mode)
            return {
                # Prohibited zones
                'forest_parks': {
                    'lower': np.array([35, 30, 20]),    # Darker green
                    'upper': np.array([85, 200, 150])
                },
                'water': {
                    'lower': np.array([90, 30, 20]),    # Darker blue
                    'upper': np.array([130, 200, 150])
                },
                # Roads
                'roads_yellow': {
                    'lower': np.array([20, 80, 80]),    # Dimmer yellow
                    'upper': np.array([30, 255, 200])
                },
                'roads_white': {
                    'lower': np.array([0, 0, 150]),     # Gray-white
                    'upper': np.array([180, 20, 220])
                },
                'roads_gray': {
                    'lower': np.array([0, 0, 60]),      # Dark gray roads
                    'upper': np.array([180, 30, 120])
                },
                # Parking and sidewalks
                'parking': {
                    'lower': np.array([0, 0, 50]),      # Dark gray areas
                    'upper': np.array([180, 30, 100])
                },
                # Buildings/Urban
                'urban': {
                    'lower': np.array([0, 0, 80]),
                    'upper': np.array([180, 40, 140])
                }
            }

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess the image for better feature detection.

        Args:
            image: BGR image from OpenCV

        Returns:
            Preprocessed image
        """
        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

        # Enhance contrast
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        return enhanced

    def extract_color_mask(self, image: np.ndarray, color_key: str) -> np.ndarray:
        """
        Extract a binary mask for a specific color category.

        Args:
            image: BGR image from OpenCV
            color_key: Key from color_ranges dictionary

        Returns:
            Binary mask (0 or 255)
        """
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Get color ranges
        if self.color_ranges is None:
            self.color_ranges = self.get_color_ranges()

        if color_key not in self.color_ranges:
            raise ValueError(f"Unknown color key: {color_key}")

        # Create mask
        color_range = self.color_ranges[color_key]
        mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])

        # Clean up mask with morphological operations
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def combine_masks(self, masks: list) -> np.ndarray:
        """
        Combine multiple masks using OR operation.

        Args:
            masks: List of binary masks

        Returns:
            Combined binary mask
        """
        if not masks:
            return None

        result = masks[0].copy()
        for mask in masks[1:]:
            result = cv2.bitwise_or(result, mask)

        return result

    def detect_edges(self, image: np.ndarray) -> np.ndarray:
        """
        Detect edges in the image using Canny edge detection.

        Args:
            image: BGR or grayscale image

        Returns:
            Binary edge map
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred, 50, 150)

        return edges

    def find_contours(self, mask: np.ndarray, min_area: int = 100) -> list:
        """
        Find contours in a binary mask.

        Args:
            mask: Binary mask
            min_area: Minimum contour area to keep

        Returns:
            List of contours
        """
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter by area
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= min_area]

        return filtered_contours

    def get_bounding_boxes(self, contours: list) -> list:
        """
        Get bounding boxes for contours.

        Args:
            contours: List of contours

        Returns:
            List of (x, y, w, h) tuples
        """
        boxes = [cv2.boundingRect(cnt) for cnt in contours]
        return boxes

    def resize_image(self, image: np.ndarray, max_dimension: int = 1024) -> Tuple[np.ndarray, float]:
        """
        Resize image if it's too large, maintaining aspect ratio.

        Args:
            image: Input image
            max_dimension: Maximum width or height

        Returns:
            Tuple of (resized image, scale factor)
        """
        height, width = image.shape[:2]

        if max(height, width) <= max_dimension:
            return image, 1.0

        if height > width:
            scale = max_dimension / height
        else:
            scale = max_dimension / width

        new_width = int(width * scale)
        new_height = int(height * scale)

        resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

        return resized, scale
