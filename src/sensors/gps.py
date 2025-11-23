"""
GPS sensor simulation for autonomous taxi.

Characteristics:
- Position with realistic GPS error (±2-5 meters)
- Heading/orientation
- Road network information
- Zone information and speed limits
- Route to destination
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Any, Optional


class GPSSensor:
    """
    Simulates a GPS sensor with realistic positioning errors and map integration.

    Provides position, heading, and map-based information like current road,
    zone, speed limits, and routing information.
    """

    def __init__(
        self,
        position_noise: float = 3.5,  # meters (standard deviation)
        heading_noise: float = 2.0,  # degrees (standard deviation)
        signal_loss_probability: float = 0.01,  # probability of temporary signal loss
        update_rate: float = 1.0  # Hz (updates per second)
    ):
        """
        Initialize the GPS sensor.

        Args:
            position_noise: Standard deviation of position error in meters
            heading_noise: Standard deviation of heading error in degrees
            signal_loss_probability: Probability of losing GPS signal
            update_rate: Update frequency in Hz
        """
        self.position_noise = position_noise
        self.heading_noise = heading_noise
        self.signal_loss_probability = signal_loss_probability
        self.update_rate = update_rate

        # Track signal state
        self.has_signal = True
        self.last_known_position = None
        self.last_known_heading = None

    def sense(
        self,
        car_position: Tuple[float, float],
        car_heading: float,
        map_data: Optional[Dict[str, Any]] = None,
        destination: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Get GPS sensor data including position, heading, and map information.

        Args:
            car_position: Actual position of the car (x, y)
            car_heading: Actual heading in degrees (0 = East, 90 = North)
            map_data: Map data from Agent 1 (zones, roads, etc.)
            destination: Optional destination coordinates

        Returns:
            Dictionary with GPS data
        """
        # Simulate signal loss
        if np.random.random() < self.signal_loss_probability:
            self.has_signal = False
            return self._generate_no_signal_data()
        else:
            self.has_signal = True

        # Add noise to position
        noisy_position = self._add_position_noise(car_position)

        # Add noise to heading
        noisy_heading = self._add_heading_noise(car_heading)

        # Store for potential signal loss recovery
        self.last_known_position = noisy_position
        self.last_known_heading = noisy_heading

        # Build GPS data
        gps_data = {
            "position": noisy_position,
            "heading": noisy_heading,
            "has_signal": True,
            "accuracy": self.position_noise,  # Estimated accuracy in meters
            "sensor_type": "gps"
        }

        # Add map-based information if available
        if map_data is not None:
            # Find current road
            current_road = self._find_current_road(noisy_position, map_data)
            gps_data["current_road"] = current_road

            # Find current zone
            current_zone = self._find_current_zone(noisy_position, map_data)
            gps_data["current_zone"] = current_zone

            # Get speed limit
            speed_limit = self._get_speed_limit(current_road, current_zone)
            gps_data["speed_limit"] = speed_limit

            # Generate route if destination is provided
            if destination is not None:
                route = self._generate_route(noisy_position, destination, map_data)
                gps_data["route"] = route
                gps_data["destination"] = destination
                gps_data["distance_to_destination"] = self._calculate_distance(
                    noisy_position, destination
                )

        return gps_data

    def _add_position_noise(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Add realistic GPS position noise.

        Args:
            position: Actual position

        Returns:
            Position with added noise
        """
        noise_x = np.random.normal(0, self.position_noise)
        noise_y = np.random.normal(0, self.position_noise)

        return (position[0] + noise_x, position[1] + noise_y)

    def _add_heading_noise(self, heading: float) -> float:
        """
        Add realistic heading noise.

        Args:
            heading: Actual heading in degrees

        Returns:
            Heading with added noise
        """
        noise = np.random.normal(0, self.heading_noise)
        noisy_heading = (heading + noise) % 360
        return noisy_heading

    def _generate_no_signal_data(self) -> Dict[str, Any]:
        """
        Generate GPS data when signal is lost.

        Returns last known position or indicates no signal.
        """
        return {
            "position": self.last_known_position,
            "heading": self.last_known_heading,
            "has_signal": False,
            "accuracy": None,
            "sensor_type": "gps",
            "warning": "GPS signal lost"
        }

    def _find_current_road(
        self,
        position: Tuple[float, float],
        map_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the road closest to the current position.

        Args:
            position: Current GPS position
            map_data: Map data with road network

        Returns:
            Road information or None if not on a road
        """
        if "roads" not in map_data:
            return None

        roads = map_data["roads"]

        # Handle different road data structures
        if isinstance(roads, dict) and "lanes" in roads:
            lanes = roads["lanes"]
        elif isinstance(roads, list):
            lanes = roads
        else:
            return None

        # Find closest road/lane
        closest_road = None
        min_distance = float('inf')
        max_distance_threshold = 10.0  # meters

        for lane in lanes:
            # Get lane center line or points
            if "center_line" in lane:
                points = lane["center_line"]
            elif "points" in lane:
                points = lane["points"]
            else:
                continue

            # Calculate distance to lane
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]

                distance = self._point_to_segment_distance(position, p1, p2)

                if distance < min_distance:
                    min_distance = distance
                    closest_road = {
                        "lane_id": lane.get("id", i),
                        "road_type": lane.get("type", "unknown"),
                        "direction": lane.get("direction", "bidirectional"),
                        "distance_from_center": distance
                    }

        # Only return road if within threshold
        if min_distance <= max_distance_threshold:
            return closest_road
        else:
            return None

    def _find_current_zone(
        self,
        position: Tuple[float, float],
        map_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the zone containing the current position.

        Args:
            position: Current GPS position
            map_data: Map data with zone information

        Returns:
            Zone information or None
        """
        if "zones" not in map_data:
            return None

        zones_data = map_data["zones"]

        # Check main zones
        if "main_zones" in zones_data:
            for zone in zones_data["main_zones"]:
                if self._point_in_zone(position, zone):
                    return {
                        "type": zone.get("type", "unknown"),
                        "speed_limit": zone.get("speed_limit", 50),
                        "zone_id": zone.get("id", 0)
                    }

        # Default zone if not found
        return {
            "type": "urban",
            "speed_limit": 60,
            "zone_id": -1
        }

    def _get_speed_limit(
        self,
        current_road: Optional[Dict[str, Any]],
        current_zone: Optional[Dict[str, Any]]
    ) -> int:
        """
        Determine speed limit based on road and zone.

        Args:
            current_road: Current road information
            current_zone: Current zone information

        Returns:
            Speed limit in km/h
        """
        # Default speed limit
        speed_limit = 50

        # Zone-based speed limit
        if current_zone and "speed_limit" in current_zone:
            speed_limit = current_zone["speed_limit"]

        # Road-specific overrides (e.g., highways)
        if current_road:
            road_type = current_road.get("road_type", "unknown")
            if road_type == "highway":
                speed_limit = 110
            elif road_type == "main_road" and current_zone:
                zone_type = current_zone.get("type", "urban")
                if zone_type == "urban":
                    speed_limit = 60
                elif zone_type == "countryside":
                    speed_limit = 90

        return speed_limit

    def _generate_route(
        self,
        start: Tuple[float, float],
        destination: Tuple[float, float],
        map_data: Dict[str, Any]
    ) -> List[Tuple[float, float]]:
        """
        Generate a simple route from start to destination.

        This is a simplified version. A full implementation would use A* or
        similar pathfinding on the road network.

        Args:
            start: Starting position
            destination: Destination position
            map_data: Map data with road network

        Returns:
            List of waypoints forming the route
        """
        # For now, return a simple straight-line route with some intermediate points
        # In a full implementation, this would use the road network graph

        num_waypoints = 5
        waypoints = []

        for i in range(num_waypoints + 1):
            t = i / num_waypoints
            waypoint = (
                start[0] + t * (destination[0] - start[0]),
                start[1] + t * (destination[1] - start[1])
            )
            waypoints.append(waypoint)

        return waypoints

    def _point_to_segment_distance(
        self,
        point: Tuple[float, float],
        seg_start: Tuple[float, float],
        seg_end: Tuple[float, float]
    ) -> float:
        """
        Calculate the minimum distance from a point to a line segment.

        Args:
            point: The point
            seg_start: Segment start point
            seg_end: Segment end point

        Returns:
            Minimum distance in meters
        """
        # Vector from seg_start to seg_end
        dx = seg_end[0] - seg_start[0]
        dy = seg_end[1] - seg_start[1]

        # Handle degenerate case (segment is a point)
        if dx == 0 and dy == 0:
            return self._calculate_distance(point, seg_start)

        # Parameter t for projection
        t = ((point[0] - seg_start[0]) * dx + (point[1] - seg_start[1]) * dy) / (dx * dx + dy * dy)

        # Clamp t to [0, 1] to stay on segment
        t = max(0, min(1, t))

        # Find closest point on segment
        closest_point = (
            seg_start[0] + t * dx,
            seg_start[1] + t * dy
        )

        return self._calculate_distance(point, closest_point)

    def _point_in_zone(
        self,
        point: Tuple[float, float],
        zone: Dict[str, Any]
    ) -> bool:
        """
        Check if a point is inside a zone polygon.

        Args:
            point: Point to check
            zone: Zone with polygon boundary

        Returns:
            True if point is inside zone
        """
        # Simplified version - assumes zone has a bounding box or polygon
        if "bounds" in zone:
            bounds = zone["bounds"]
            return (
                bounds["min_x"] <= point[0] <= bounds["max_x"] and
                bounds["min_y"] <= point[1] <= bounds["max_y"]
            )

        # Ray-casting algorithm for polygon (if polygon is defined)
        if "polygon" in zone:
            polygon = zone["polygon"]
            return self._point_in_polygon(point, polygon)

        return False

    def _point_in_polygon(
        self,
        point: Tuple[float, float],
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """
        Ray-casting algorithm to check if point is in polygon.

        Args:
            point: Point to check
            polygon: List of polygon vertices

        Returns:
            True if point is inside polygon
        """
        x, y = point
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _calculate_distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two positions."""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)

    def get_sensor_info(self) -> Dict[str, Any]:
        """Get information about the sensor configuration."""
        return {
            "type": "gps",
            "position_noise": self.position_noise,
            "heading_noise": self.heading_noise,
            "update_rate": self.update_rate,
            "signal_loss_probability": self.signal_loss_probability,
            "has_signal": self.has_signal
        }
