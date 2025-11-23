"""
Lidar sensor simulation for autonomous taxi.

Characteristics:
- Accurate distance measurements (30-50m range)
- 360-degree scanning capability
- Ray-casting at regular angle intervals
- Point cloud output
- Handles occlusion (can't see through objects)
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Any, Optional


class LidarSensor:
    """
    Simulates a Lidar sensor with accurate distance measurements.

    The Lidar casts rays in all directions and measures precise distances
    to objects within range, producing a point cloud representation.
    """

    def __init__(
        self,
        max_range: float = 40.0,  # meters
        angle_resolution: float = 1.0,  # degrees between rays
        start_angle: float = 0.0,  # degrees (0 = East)
        end_angle: float = 360.0,  # degrees
        position_offset: Tuple[float, float] = (0.0, 0.0),  # offset from car center
        distance_noise: float = 0.02,  # 2cm standard deviation
        intensity_variation: float = 0.15  # intensity variation based on material
    ):
        """
        Initialize the Lidar sensor.

        Args:
            max_range: Maximum detection range in meters
            angle_resolution: Angular resolution in degrees (smaller = more rays)
            start_angle: Starting angle for scanning in degrees
            end_angle: Ending angle for scanning in degrees
            position_offset: Offset from car center (x, y) in meters
            distance_noise: Standard deviation of distance measurement noise in meters
            intensity_variation: Variation in return intensity (0-1)
        """
        self.max_range = max_range
        self.angle_resolution = angle_resolution
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.position_offset = position_offset
        self.distance_noise = distance_noise
        self.intensity_variation = intensity_variation

        # Calculate number of rays
        angle_span = end_angle - start_angle
        self.num_rays = int(angle_span / angle_resolution) + 1

    def sense(
        self,
        car_position: Tuple[float, float],
        car_heading: float,
        environment_state: Dict[str, Any],
        map_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform Lidar scan and return point cloud data.

        Args:
            car_position: Current position of the car (x, y)
            car_heading: Current heading in degrees (0 = East, 90 = North)
            environment_state: Current state of the environment
            map_data: Optional map data for detecting boundaries

        Returns:
            Dictionary with point cloud data
        """
        # Calculate actual sensor position considering offset and car heading
        sensor_position = self._calculate_sensor_position(car_position, car_heading)

        # Collect all detectable objects
        objects = self._collect_objects(environment_state, map_data)

        # Perform ray-casting
        point_cloud = []
        for i in range(self.num_rays):
            angle = self.start_angle + i * self.angle_resolution
            # Convert to absolute angle considering car heading
            absolute_angle = (angle + car_heading) % 360

            # Cast ray and find closest intersection
            hit = self._cast_ray(sensor_position, absolute_angle, objects)

            if hit is not None:
                point_cloud.append({
                    "angle": angle,  # Relative to car
                    "absolute_angle": absolute_angle,
                    "distance": hit["distance"],
                    "intensity": hit["intensity"],
                    "object_type": hit.get("object_type", "unknown")
                })

        return {
            "points": point_cloud,
            "sensor_type": "lidar",
            "max_range": self.max_range,
            "num_rays": self.num_rays,
            "sensor_position": sensor_position
        }

    def _calculate_sensor_position(
        self,
        car_position: Tuple[float, float],
        car_heading: float
    ) -> Tuple[float, float]:
        """
        Calculate the actual sensor position considering offset from car center.

        Args:
            car_position: Position of car center
            car_heading: Heading of car in degrees

        Returns:
            Actual sensor position
        """
        if self.position_offset == (0.0, 0.0):
            return car_position

        # Convert heading to radians
        heading_rad = math.radians(car_heading)

        # Rotate offset by car heading
        cos_h = math.cos(heading_rad)
        sin_h = math.sin(heading_rad)

        offset_x = self.position_offset[0] * cos_h - self.position_offset[1] * sin_h
        offset_y = self.position_offset[0] * sin_h + self.position_offset[1] * cos_h

        return (car_position[0] + offset_x, car_position[1] + offset_y)

    def _collect_objects(
        self,
        environment_state: Dict[str, Any],
        map_data: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Collect all objects that can be detected by Lidar.

        Args:
            environment_state: Current environment state
            map_data: Map data with boundaries

        Returns:
            List of detectable objects with their geometries
        """
        objects = []

        # Add vehicles as rectangular obstacles
        if "vehicles" in environment_state:
            for vehicle in environment_state["vehicles"]:
                position = vehicle.get("position", (0, 0))
                heading = vehicle.get("heading", 0)
                # Approximate vehicle size (can be refined)
                length = vehicle.get("length", 4.5)
                width = vehicle.get("width", 2.0)

                objects.append({
                    "type": "vehicle",
                    "geometry": "rectangle",
                    "position": position,
                    "heading": heading,
                    "length": length,
                    "width": width,
                    "intensity_base": 0.7
                })

        # Add pedestrians as circular obstacles
        if "pedestrians" in environment_state:
            for pedestrian in environment_state["pedestrians"]:
                position = pedestrian.get("position", (0, 0))
                radius = pedestrian.get("radius", 0.3)  # ~30cm radius

                objects.append({
                    "type": "pedestrian",
                    "geometry": "circle",
                    "position": position,
                    "radius": radius,
                    "intensity_base": 0.5
                })

        # Add obstacles
        if "obstacles" in environment_state:
            for obstacle in environment_state["obstacles"]:
                objects.append({
                    "type": "obstacle",
                    "geometry": obstacle.get("geometry", "circle"),
                    "position": obstacle.get("position", (0, 0)),
                    "radius": obstacle.get("radius", 0.5),
                    "intensity_base": 0.8
                })

        # Add map boundaries
        if map_data and "boundaries" in map_data:
            for boundary in map_data["boundaries"]:
                objects.append({
                    "type": "boundary",
                    "geometry": "line",
                    "start": boundary.get("start", (0, 0)),
                    "end": boundary.get("end", (0, 0)),
                    "intensity_base": 0.9
                })

        # Add road edges if available
        if map_data and "roads" in map_data and "edges" in map_data["roads"]:
            for edge in map_data["roads"]["edges"]:
                objects.append({
                    "type": "road_edge",
                    "geometry": "line",
                    "start": edge.get("start", (0, 0)),
                    "end": edge.get("end", (0, 0)),
                    "intensity_base": 0.6
                })

        return objects

    def _cast_ray(
        self,
        origin: Tuple[float, float],
        angle: float,
        objects: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Cast a single ray and find the closest intersection.

        Args:
            origin: Starting position of the ray
            angle: Angle of the ray in degrees (absolute)
            objects: List of objects to test for intersection

        Returns:
            Dictionary with hit information, or None if no hit within range
        """
        # Convert angle to radians
        angle_rad = math.radians(angle)
        ray_dir = (math.cos(angle_rad), math.sin(angle_rad))

        closest_hit = None
        closest_distance = self.max_range

        for obj in objects:
            hit = None

            if obj["geometry"] == "circle":
                hit = self._ray_circle_intersection(
                    origin, ray_dir, obj["position"], obj["radius"]
                )
            elif obj["geometry"] == "rectangle":
                hit = self._ray_rectangle_intersection(
                    origin, ray_dir, obj["position"], obj["heading"],
                    obj["length"], obj["width"]
                )
            elif obj["geometry"] == "line":
                hit = self._ray_line_intersection(
                    origin, ray_dir, obj["start"], obj["end"]
                )

            if hit is not None and hit < closest_distance:
                closest_distance = hit
                closest_hit = {
                    "distance": self._add_distance_noise(hit),
                    "intensity": self._calculate_intensity(obj["intensity_base"]),
                    "object_type": obj["type"]
                }

        return closest_hit

    def _ray_circle_intersection(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        center: Tuple[float, float],
        radius: float
    ) -> Optional[float]:
        """
        Calculate ray-circle intersection using geometric method.

        Returns:
            Distance to intersection point, or None if no intersection
        """
        # Vector from ray origin to circle center
        oc_x = origin[0] - center[0]
        oc_y = origin[1] - center[1]

        # Quadratic equation coefficients: at^2 + bt + c = 0
        a = direction[0] ** 2 + direction[1] ** 2
        b = 2 * (oc_x * direction[0] + oc_y * direction[1])
        c = oc_x ** 2 + oc_y ** 2 - radius ** 2

        discriminant = b ** 2 - 4 * a * c

        if discriminant < 0:
            return None  # No intersection

        # Calculate the two intersection points
        sqrt_discriminant = math.sqrt(discriminant)
        t1 = (-b - sqrt_discriminant) / (2 * a)
        t2 = (-b + sqrt_discriminant) / (2 * a)

        # We want the closest positive intersection
        if t1 > 0:
            return t1
        elif t2 > 0:
            return t2
        else:
            return None  # Intersection behind ray origin

    def _ray_rectangle_intersection(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        rect_center: Tuple[float, float],
        rect_heading: float,
        length: float,
        width: float
    ) -> Optional[float]:
        """
        Calculate ray-rectangle intersection.

        Simplification: Test against 4 line segments forming the rectangle.

        Returns:
            Distance to closest intersection, or None if no intersection
        """
        # Calculate rectangle corners
        heading_rad = math.radians(rect_heading)
        cos_h = math.cos(heading_rad)
        sin_h = math.sin(heading_rad)

        # Half dimensions
        half_length = length / 2
        half_width = width / 2

        # Corner offsets in local coordinates
        corners_local = [
            (half_length, half_width),
            (half_length, -half_width),
            (-half_length, -half_width),
            (-half_length, half_width)
        ]

        # Transform to world coordinates
        corners = []
        for local_x, local_y in corners_local:
            world_x = rect_center[0] + local_x * cos_h - local_y * sin_h
            world_y = rect_center[1] + local_x * sin_h + local_y * cos_h
            corners.append((world_x, world_y))

        # Test intersection with each edge
        closest_distance = None
        for i in range(4):
            start = corners[i]
            end = corners[(i + 1) % 4]

            distance = self._ray_line_intersection(origin, direction, start, end)
            if distance is not None:
                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance

        return closest_distance

    def _ray_line_intersection(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        line_start: Tuple[float, float],
        line_end: Tuple[float, float]
    ) -> Optional[float]:
        """
        Calculate ray-line segment intersection.

        Returns:
            Distance to intersection, or None if no intersection
        """
        # Ray: P = origin + t * direction
        # Line: Q = line_start + s * (line_end - line_start)

        dx = line_end[0] - line_start[0]
        dy = line_end[1] - line_start[1]

        # Check if ray and line are parallel
        denominator = direction[0] * dy - direction[1] * dx
        if abs(denominator) < 1e-10:
            return None  # Parallel or coincident

        # Calculate intersection parameters
        ox = origin[0] - line_start[0]
        oy = origin[1] - line_start[1]

        t = (ox * dy - oy * dx) / denominator
        s = (ox * direction[1] - oy * direction[0]) / denominator

        # Check if intersection is valid
        if t > 0 and 0 <= s <= 1:
            return t
        else:
            return None

    def _add_distance_noise(self, distance: float) -> float:
        """
        Add realistic measurement noise to distance.

        Args:
            distance: True distance

        Returns:
            Distance with added noise
        """
        noise = np.random.normal(0, self.distance_noise)
        return max(0, distance + noise)

    def _calculate_intensity(self, base_intensity: float) -> float:
        """
        Calculate return intensity with variation.

        Args:
            base_intensity: Base intensity for object material (0-1)

        Returns:
            Intensity with variation
        """
        variation = np.random.uniform(-self.intensity_variation, self.intensity_variation)
        intensity = base_intensity + variation
        return max(0.0, min(1.0, intensity))

    def get_sensor_info(self) -> Dict[str, Any]:
        """Get information about the sensor configuration."""
        return {
            "type": "lidar",
            "max_range": self.max_range,
            "angle_resolution": self.angle_resolution,
            "angle_coverage": (self.start_angle, self.end_angle),
            "num_rays": self.num_rays,
            "distance_noise": self.distance_noise,
            "position_offset": self.position_offset
        }
