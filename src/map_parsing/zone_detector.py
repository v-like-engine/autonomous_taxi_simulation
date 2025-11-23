"""
Zone detection and classification.
Automatically detects and labels different zones from map images.
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from .image_processor import ImageProcessor


class ZoneDetector:
    """Detects and classifies zones from map images."""

    def __init__(self, image_processor: ImageProcessor):
        """
        Initialize the zone detector.

        Args:
            image_processor: ImageProcessor instance with loaded map
        """
        self.image_processor = image_processor
        self.zones = {
            "main_zones": [],
            "subzones": {
                "sidewalks": [],
                "parking": [],
                "roads": []
            }
        }

    def detect_all_zones(self, image: np.ndarray, road_mask: Optional[np.ndarray] = None) -> Dict:
        """
        Detect all zones in the map image.

        Args:
            image: Preprocessed map image
            road_mask: Optional mask of detected roads (for better classification)

        Returns:
            Dictionary containing detected zones
        """
        # Reset zones
        self.zones = {
            "main_zones": [],
            "subzones": {
                "sidewalks": [],
                "parking": [],
                "roads": []
            }
        }

        height, width = image.shape[:2]

        # Detect prohibited zones (forests, parks, water)
        prohibited_zones = self._detect_prohibited_zones(image)

        # Detect road zones (will be used for other classifications)
        road_zones = self._detect_road_zones(image, road_mask)

        # Detect parking zones
        parking_zones = self._detect_parking_zones(image, road_mask)

        # Detect sidewalk zones
        sidewalk_zones = self._detect_sidewalk_zones(image, road_mask)

        # Create a combined mask of special zones
        special_zones_mask = np.zeros((height, width), dtype=np.uint8)

        # Add prohibited zones to mask
        for zone in prohibited_zones:
            if "polygon" in zone:
                polygon = np.array(zone["polygon"], dtype=np.int32)
                cv2.fillPoly(special_zones_mask, [polygon], 255)

        # Add road zones to mask
        for zone in road_zones:
            if "polygon" in zone:
                polygon = np.array(zone["polygon"], dtype=np.int32)
                cv2.fillPoly(special_zones_mask, [polygon], 255)

        # Classify remaining areas into yard, urban, countryside, highway
        other_zones = self._classify_general_zones(image, special_zones_mask, road_mask)

        # Combine all zones
        self.zones["main_zones"] = prohibited_zones + other_zones
        self.zones["subzones"]["roads"] = road_zones
        self.zones["subzones"]["parking"] = parking_zones
        self.zones["subzones"]["sidewalks"] = sidewalk_zones

        return self.zones

    def _detect_prohibited_zones(self, image: np.ndarray) -> List[Dict]:
        """
        Detect prohibited zones (forests, parks, water).

        Args:
            image: Map image

        Returns:
            List of prohibited zone dictionaries
        """
        prohibited_zones = []

        # Detect green areas (forests, parks)
        forest_mask = self.image_processor.extract_color_mask(image, 'forest_parks')
        forest_contours = self.image_processor.find_contours(forest_mask, min_area=500)

        for contour in forest_contours:
            polygon = contour.squeeze().tolist()
            if len(polygon) > 2:  # Valid polygon
                area = cv2.contourArea(contour)
                prohibited_zones.append({
                    "type": "prohibited",
                    "subtype": "forest_park",
                    "polygon": polygon,
                    "area": area,
                    "speed_limit": 0,  # No driving allowed
                    "description": "Forest/Park area - No driving"
                })

        # Detect water bodies
        water_mask = self.image_processor.extract_color_mask(image, 'water')
        water_contours = self.image_processor.find_contours(water_mask, min_area=500)

        for contour in water_contours:
            polygon = contour.squeeze().tolist()
            if len(polygon) > 2:
                area = cv2.contourArea(contour)
                prohibited_zones.append({
                    "type": "prohibited",
                    "subtype": "water",
                    "polygon": polygon,
                    "area": area,
                    "speed_limit": 0,
                    "description": "Water body - No driving"
                })

        return prohibited_zones

    def _detect_road_zones(self, image: np.ndarray, road_mask: Optional[np.ndarray] = None) -> List[Dict]:
        """
        Detect road zones.

        Args:
            image: Map image
            road_mask: Optional pre-detected road mask

        Returns:
            List of road zone dictionaries
        """
        if road_mask is None:
            # Combine all road types
            yellow_roads = self.image_processor.extract_color_mask(image, 'roads_yellow')
            white_roads = self.image_processor.extract_color_mask(image, 'roads_white')
            gray_roads = self.image_processor.extract_color_mask(image, 'roads_gray')

            road_mask = self.image_processor.combine_masks([yellow_roads, white_roads, gray_roads])

        if road_mask is None:
            return []

        # Dilate slightly to get full road area
        kernel = np.ones((5, 5), np.uint8)
        dilated_roads = cv2.dilate(road_mask, kernel, iterations=1)

        road_contours = self.image_processor.find_contours(dilated_roads, min_area=200)

        road_zones = []
        for contour in road_contours:
            polygon = contour.squeeze().tolist()
            if len(polygon) > 2:
                area = cv2.contourArea(contour)
                road_zones.append({
                    "type": "road",
                    "polygon": polygon,
                    "area": area,
                    "description": "Drivable road area"
                })

        return road_zones

    def _detect_parking_zones(self, image: np.ndarray, road_mask: Optional[np.ndarray] = None) -> List[Dict]:
        """
        Detect parking zones.

        Args:
            image: Map image
            road_mask: Optional road mask to exclude roads

        Returns:
            List of parking zone dictionaries
        """
        parking_mask = self.image_processor.extract_color_mask(image, 'parking')

        # Remove road areas from parking mask
        if road_mask is not None:
            parking_mask = cv2.bitwise_and(parking_mask, cv2.bitwise_not(road_mask))

        parking_contours = self.image_processor.find_contours(parking_mask, min_area=300)

        parking_zones = []
        for contour in parking_contours:
            polygon = contour.squeeze().tolist()
            if len(polygon) > 2:
                area = cv2.contourArea(contour)
                parking_zones.append({
                    "type": "parking",
                    "polygon": polygon,
                    "area": area,
                    "description": "Parking area"
                })

        return parking_zones

    def _detect_sidewalk_zones(self, image: np.ndarray, road_mask: Optional[np.ndarray] = None) -> List[Dict]:
        """
        Detect sidewalk zones (areas adjacent to roads).

        Args:
            image: Map image
            road_mask: Optional road mask

        Returns:
            List of sidewalk zone dictionaries
        """
        if road_mask is None:
            return []

        # Dilate road mask to find areas adjacent to roads
        kernel = np.ones((7, 7), np.uint8)
        dilated_roads = cv2.dilate(road_mask, kernel, iterations=2)

        # Sidewalks are the difference between dilated roads and original roads
        sidewalk_mask = cv2.subtract(dilated_roads, road_mask)

        sidewalk_contours = self.image_processor.find_contours(sidewalk_mask, min_area=100)

        sidewalk_zones = []
        for contour in sidewalk_contours:
            polygon = contour.squeeze().tolist()
            if len(polygon) > 2:
                area = cv2.contourArea(contour)
                sidewalk_zones.append({
                    "type": "sidewalk",
                    "polygon": polygon,
                    "area": area,
                    "description": "Sidewalk/Pedestrian area"
                })

        return sidewalk_zones

    def _classify_general_zones(self, image: np.ndarray, special_zones_mask: np.ndarray,
                                road_mask: Optional[np.ndarray] = None) -> List[Dict]:
        """
        Classify remaining areas into yard, urban, countryside, or highway zones.

        Args:
            image: Map image
            special_zones_mask: Mask of already classified zones
            road_mask: Optional road mask for density analysis

        Returns:
            List of zone dictionaries
        """
        height, width = image.shape[:2]
        zones = []

        # Create a grid to analyze different regions
        grid_size = 100  # pixels

        for y in range(0, height, grid_size):
            for x in range(0, width, grid_size):
                # Define region
                x_end = min(x + grid_size, width)
                y_end = min(y + grid_size, height)

                # Skip if mostly special zones
                region_mask = special_zones_mask[y:y_end, x:x_end]
                special_ratio = np.sum(region_mask > 0) / (region_mask.size + 1e-6)

                if special_ratio > 0.5:  # More than 50% is special zones
                    continue

                # Analyze road density in this region
                road_density = 0
                avg_road_width = 0

                if road_mask is not None:
                    road_region = road_mask[y:y_end, x:x_end]
                    road_density = np.sum(road_region > 0) / (road_region.size + 1e-6)

                    # Estimate average road width
                    if road_density > 0:
                        # Use distance transform to estimate road width
                        dist_transform = cv2.distanceTransform(road_region, cv2.DIST_L2, 5)
                        avg_road_width = np.mean(dist_transform[dist_transform > 0]) * 2 if np.any(dist_transform > 0) else 0

                # Classify based on road density and width
                zone_type = self._classify_zone_type(road_density, avg_road_width)

                if zone_type:
                    # Create polygon for this region
                    polygon = [
                        [x, y],
                        [x_end, y],
                        [x_end, y_end],
                        [x, y_end]
                    ]

                    zone_info = self._get_zone_info(zone_type)

                    zones.append({
                        "type": zone_type,
                        "polygon": polygon,
                        "area": (x_end - x) * (y_end - y),
                        "speed_limit": zone_info["speed_limit"],
                        "max_speed": zone_info["max_speed"],
                        "description": zone_info["description"]
                    })

        # Merge adjacent zones of the same type
        zones = self._merge_adjacent_zones(zones)

        return zones

    def _classify_zone_type(self, road_density: float, avg_road_width: float) -> Optional[str]:
        """
        Classify zone type based on road characteristics.

        Args:
            road_density: Ratio of road pixels in the region
            avg_road_width: Average road width in pixels

        Returns:
            Zone type string or None
        """
        # Highway: wide roads (>20px), lower density
        if avg_road_width > 20 and road_density < 0.4:
            return "highway"

        # Urban: moderate road density, moderate width
        elif road_density > 0.1 and avg_road_width > 8:
            return "urban"

        # Countryside: low road density, medium width
        elif road_density < 0.15 and avg_road_width > 6:
            return "countryside"

        # Yard: very low road density or very narrow roads
        elif road_density < 0.1 or avg_road_width < 6:
            return "yard"

        # Default to urban if has some roads
        elif road_density > 0:
            return "urban"

        return None

    def _get_zone_info(self, zone_type: str) -> Dict:
        """
        Get speed limit and description for a zone type.

        Args:
            zone_type: Type of zone

        Returns:
            Dictionary with zone information
        """
        zone_info_map = {
            "yard": {
                "speed_limit": 10,
                "max_speed": 30,  # Can do +20 km/h
                "description": "Yard area - 10 km/h base speed"
            },
            "urban": {
                "speed_limit": 20,
                "max_speed": 80,  # 60 km/h on main roads, +20 km/h tolerance
                "description": "Urban zone - 20 km/h base, 60 km/h on main roads"
            },
            "countryside": {
                "speed_limit": 90,
                "max_speed": 110,  # Can do +20 km/h
                "description": "Countryside zone - 90 km/h speed limit"
            },
            "highway": {
                "speed_limit": 110,
                "max_speed": 130,  # Can do +20 km/h
                "description": "Highway zone - 110 km/h speed limit"
            }
        }

        return zone_info_map.get(zone_type, {
            "speed_limit": 20,
            "max_speed": 40,
            "description": "Unknown zone type"
        })

    def _merge_adjacent_zones(self, zones: List[Dict]) -> List[Dict]:
        """
        Merge adjacent zones of the same type.

        Args:
            zones: List of zone dictionaries

        Returns:
            List of merged zone dictionaries
        """
        if not zones:
            return []

        # Group zones by type
        zones_by_type = {}
        for zone in zones:
            zone_type = zone["type"]
            if zone_type not in zones_by_type:
                zones_by_type[zone_type] = []
            zones_by_type[zone_type].append(zone)

        merged_zones = []

        for zone_type, type_zones in zones_by_type.items():
            if not type_zones:
                continue

            # For simplification, we'll keep zones as-is
            # In a more sophisticated implementation, we would merge adjacent rectangles
            merged_zones.extend(type_zones)

        return merged_zones

    def get_zone_at_point(self, x: int, y: int) -> Optional[Dict]:
        """
        Get the zone at a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Zone dictionary or None if no zone at that point
        """
        # Check main zones
        for zone in self.zones["main_zones"]:
            if "polygon" in zone:
                polygon = np.array(zone["polygon"], dtype=np.int32)
                if cv2.pointPolygonTest(polygon, (x, y), False) >= 0:
                    return zone

        return None

    def get_zones_by_type(self, zone_type: str) -> List[Dict]:
        """
        Get all zones of a specific type.

        Args:
            zone_type: Type of zone to filter

        Returns:
            List of zones of the specified type
        """
        return [zone for zone in self.zones["main_zones"] if zone.get("type") == zone_type]

    def get_speed_limit_at_point(self, x: int, y: int) -> int:
        """
        Get the speed limit at a specific point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Speed limit in km/h
        """
        zone = self.get_zone_at_point(x, y)
        if zone:
            return zone.get("speed_limit", 20)
        return 20  # Default urban speed
