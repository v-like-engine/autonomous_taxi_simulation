"""
Sonar sensor simulation for autonomous taxi.

Characteristics:
- Very short range (5-10 meters)
- Multiple sensors around the car
- Narrow detection cones
- Very accurate distance measurements
- Cannot identify object type (just distance)
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Any, Optional


class SonarSensor:
    """
    Simulates multiple sonar sensors around the car for close-range detection.

    Sonar sensors are very accurate but have limited range and field of view.
    Typically used for parking assistance and collision avoidance.
    """

    # Standard sonar positions and angles relative to car
    SENSOR_CONFIGS = {
        "front_left": {"angle": 45, "position_offset": (1.8, 0.8)},
        "front_center": {"angle": 0, "position_offset": (2.0, 0.0)},
        "front_right": {"angle": -45, "position_offset": (1.8, -0.8)},
        "rear_left": {"angle": 135, "position_offset": (-1.8, 0.8)},
        "rear_center": {"angle": 180, "position_offset": (-2.0, 0.0)},
        "rear_right": {"angle": -135, "position_offset": (-1.8, -0.8)},
        "side_left": {"angle": 90, "position_offset": (0.0, 1.0)},
        "side_right": {"angle": -90, "position_offset": (0.0, -1.0)}
    }

    def __init__(
        self,
        max_range: float = 8.0,  # meters
        cone_angle: float = 30.0,  # degrees (total cone width)
        distance_noise: float = 0.01,  # 1cm standard deviation
        num_rays_per_sensor: int = 5,  # rays to cast per sensor for cone coverage
        enabled_sensors: Optional[List[str]] = None  # which sensors to enable
    ):
        """
        Initialize the sonar sensor array.

        Args:
            max_range: Maximum detection range in meters
            cone_angle: Width of detection cone in degrees
            distance_noise: Standard deviation of distance noise in meters
            num_rays_per_sensor: Number of rays to cast per sensor
            enabled_sensors: List of sensor names to enable (None = all)
        """
        self.max_range = max_range
        self.cone_angle = cone_angle
        self.distance_noise = distance_noise
        self.num_rays_per_sensor = num_rays_per_sensor

        # Determine which sensors are enabled
        if enabled_sensors is None:
            self.enabled_sensors = list(self.SENSOR_CONFIGS.keys())
        else:
            self.enabled_sensors = [s for s in enabled_sensors if s in self.SENSOR_CONFIGS]

    def sense(
        self,
        car_position: Tuple[float, float],
        car_heading: float,
        environment_state: Dict[str, Any],
        map_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform sonar sensing from all enabled sensors.

        Args:
            car_position: Current position of the car (x, y)
            car_heading: Current heading in degrees (0 = East, 90 = North)
            environment_state: Current state of the environment
            map_data: Optional map data for detecting boundaries

        Returns:
            Dictionary with distance measurements from each sensor
        """
        # Collect all detectable objects
        objects = self._collect_objects(environment_state, map_data, car_position)

        # Perform sensing from each enabled sensor
        measurements = {}
        for sensor_name in self.enabled_sensors:
            distance = self._sense_single_sensor(
                sensor_name,
                car_position,
                car_heading,
                objects
            )
            measurements[sensor_name] = distance

        return {
            "sensors": measurements,
            "sensor_type": "sonar",
            "max_range": self.max_range,
            "cone_angle": self.cone_angle
        }

    def _sense_single_sensor(
        self,
        sensor_name: str,
        car_position: Tuple[float, float],
        car_heading: float,
        objects: List[Dict[str, Any]]
    ) -> Optional[float]:
        """
        Perform sensing from a single sonar sensor.

        Args:
            sensor_name: Name of the sensor
            car_position: Position of the car
            car_heading: Heading of the car
            objects: List of objects to detect

        Returns:
            Distance to nearest object in meters, or None if nothing detected
        """
        config = self.SENSOR_CONFIGS[sensor_name]

        # Calculate sensor position and direction
        sensor_position = self._calculate_sensor_position(
            car_position,
            car_heading,
            config["position_offset"]
        )
        sensor_angle = (config["angle"] + car_heading) % 360

        # Cast multiple rays within the cone
        min_distance = None

        for i in range(self.num_rays_per_sensor):
            # Calculate ray angle within cone
            if self.num_rays_per_sensor == 1:
                ray_offset = 0
            else:
                # Distribute rays evenly across cone
                ray_offset = (i / (self.num_rays_per_sensor - 1) - 0.5) * self.cone_angle

            ray_angle = sensor_angle + ray_offset

            # Cast ray and find nearest object
            distance = self._cast_sonar_ray(sensor_position, ray_angle, objects)

            if distance is not None:
                if min_distance is None or distance < min_distance:
                    min_distance = distance

        # Add measurement noise if we detected something
        if min_distance is not None:
            min_distance = self._add_distance_noise(min_distance)

        return min_distance

    def _calculate_sensor_position(
        self,
        car_position: Tuple[float, float],
        car_heading: float,
        offset: Tuple[float, float]
    ) -> Tuple[float, float]:
        """
        Calculate sensor position considering offset from car center.

        Args:
            car_position: Position of car center
            car_heading: Heading of car in degrees
            offset: Offset in car's local coordinates (forward, left)

        Returns:
            Actual sensor position in world coordinates
        """
        # Convert heading to radians
        heading_rad = math.radians(car_heading)

        # Rotate offset by car heading
        cos_h = math.cos(heading_rad)
        sin_h = math.sin(heading_rad)

        offset_x = offset[0] * cos_h - offset[1] * sin_h
        offset_y = offset[0] * sin_h + offset[1] * cos_h

        return (car_position[0] + offset_x, car_position[1] + offset_y)

    def _collect_objects(
        self,
        environment_state: Dict[str, Any],
        map_data: Optional[Dict[str, Any]],
        car_position: Tuple[float, float]
    ) -> List[Dict[str, Any]]:
        """
        Collect nearby objects that sonar can detect.

        Args:
            environment_state: Current environment state
            map_data: Map data with boundaries
            car_position: Position of the car (to filter distant objects)

        Returns:
            List of nearby objects with their geometries
        """
        objects = []

        # Add vehicles (only if close enough)
        if "vehicles" in environment_state:
            for vehicle in environment_state["vehicles"]:
                position = vehicle.get("position", (0, 0))
                # Pre-filter vehicles that are too far away
                distance = self._calculate_distance(car_position, position)
                if distance <= self.max_range + 5:  # Add buffer for vehicle size
                    heading = vehicle.get("heading", 0)
                    length = vehicle.get("length", 4.5)
                    width = vehicle.get("width", 2.0)

                    objects.append({
                        "type": "vehicle",
                        "geometry": "rectangle",
                        "position": position,
                        "heading": heading,
                        "length": length,
                        "width": width
                    })

        # Add pedestrians
        if "pedestrians" in environment_state:
            for pedestrian in environment_state["pedestrians"]:
                position = pedestrian.get("position", (0, 0))
                distance = self._calculate_distance(car_position, position)
                if distance <= self.max_range + 1:
                    radius = pedestrian.get("radius", 0.3)

                    objects.append({
                        "type": "pedestrian",
                        "geometry": "circle",
                        "position": position,
                        "radius": radius
                    })

        # Add obstacles
        if "obstacles" in environment_state:
            for obstacle in environment_state["obstacles"]:
                position = obstacle.get("position", (0, 0))
                distance = self._calculate_distance(car_position, position)
                if distance <= self.max_range + 2:
                    objects.append({
                        "type": "obstacle",
                        "geometry": obstacle.get("geometry", "circle"),
                        "position": position,
                        "radius": obstacle.get("radius", 0.5)
                    })

        # Add curbs and walls from map data
        if map_data and "boundaries" in map_data:
            for boundary in map_data["boundaries"]:
                # Check if boundary is close enough
                start = boundary.get("start", (0, 0))
                end = boundary.get("end", (0, 0))
                # Approximate check using segment midpoint
                midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
                distance = self._calculate_distance(car_position, midpoint)
                if distance <= self.max_range + 5:
                    objects.append({
                        "type": "boundary",
                        "geometry": "line",
                        "start": start,
                        "end": end
                    })

        return objects

    def _cast_sonar_ray(
        self,
        origin: Tuple[float, float],
        angle: float,
        objects: List[Dict[str, Any]]
    ) -> Optional[float]:
        """
        Cast a single sonar ray and find nearest intersection.

        Args:
            origin: Starting position of the ray
            angle: Angle of the ray in degrees (absolute)
            objects: List of objects to test

        Returns:
            Distance to nearest object, or None if nothing within range
        """
        # Convert angle to radians and get direction vector
        angle_rad = math.radians(angle)
        ray_dir = (math.cos(angle_rad), math.sin(angle_rad))

        closest_distance = None

        for obj in objects:
            distance = None

            if obj["geometry"] == "circle":
                distance = self._ray_circle_intersection(
                    origin, ray_dir, obj["position"], obj["radius"]
                )
            elif obj["geometry"] == "rectangle":
                distance = self._ray_rectangle_intersection(
                    origin, ray_dir, obj["position"], obj["heading"],
                    obj["length"], obj["width"]
                )
            elif obj["geometry"] == "line":
                distance = self._ray_line_intersection(
                    origin, ray_dir, obj["start"], obj["end"]
                )

            if distance is not None and distance <= self.max_range:
                if closest_distance is None or distance < closest_distance:
                    closest_distance = distance

        return closest_distance

    def _ray_circle_intersection(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        center: Tuple[float, float],
        radius: float
    ) -> Optional[float]:
        """Ray-circle intersection (same as Lidar)."""
        oc_x = origin[0] - center[0]
        oc_y = origin[1] - center[1]

        a = direction[0] ** 2 + direction[1] ** 2
        b = 2 * (oc_x * direction[0] + oc_y * direction[1])
        c = oc_x ** 2 + oc_y ** 2 - radius ** 2

        discriminant = b ** 2 - 4 * a * c

        if discriminant < 0:
            return None

        sqrt_discriminant = math.sqrt(discriminant)
        t1 = (-b - sqrt_discriminant) / (2 * a)
        t2 = (-b + sqrt_discriminant) / (2 * a)

        if t1 > 0:
            return t1
        elif t2 > 0:
            return t2
        else:
            return None

    def _ray_rectangle_intersection(
        self,
        origin: Tuple[float, float],
        direction: Tuple[float, float],
        rect_center: Tuple[float, float],
        rect_heading: float,
        length: float,
        width: float
    ) -> Optional[float]:
        """Ray-rectangle intersection (same as Lidar)."""
        heading_rad = math.radians(rect_heading)
        cos_h = math.cos(heading_rad)
        sin_h = math.sin(heading_rad)

        half_length = length / 2
        half_width = width / 2

        corners_local = [
            (half_length, half_width),
            (half_length, -half_width),
            (-half_length, -half_width),
            (-half_length, half_width)
        ]

        corners = []
        for local_x, local_y in corners_local:
            world_x = rect_center[0] + local_x * cos_h - local_y * sin_h
            world_y = rect_center[1] + local_x * sin_h + local_y * cos_h
            corners.append((world_x, world_y))

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
        """Ray-line segment intersection (same as Lidar)."""
        dx = line_end[0] - line_start[0]
        dy = line_end[1] - line_start[1]

        denominator = direction[0] * dy - direction[1] * dx
        if abs(denominator) < 1e-10:
            return None

        ox = origin[0] - line_start[0]
        oy = origin[1] - line_start[1]

        t = (ox * dy - oy * dx) / denominator
        s = (ox * direction[1] - oy * direction[0]) / denominator

        if t > 0 and 0 <= s <= 1:
            return t
        else:
            return None

    def _calculate_distance(
        self,
        pos1: Tuple[float, float],
        pos2: Tuple[float, float]
    ) -> float:
        """Calculate Euclidean distance between two positions."""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)

    def _add_distance_noise(self, distance: float) -> float:
        """
        Add very small measurement noise to distance.

        Sonar is very accurate, so noise is minimal.

        Args:
            distance: True distance

        Returns:
            Distance with added noise
        """
        noise = np.random.normal(0, self.distance_noise)
        return max(0, distance + noise)

    def get_sensor_info(self) -> Dict[str, Any]:
        """Get information about the sensor configuration."""
        return {
            "type": "sonar",
            "max_range": self.max_range,
            "cone_angle": self.cone_angle,
            "enabled_sensors": self.enabled_sensors,
            "num_sensors": len(self.enabled_sensors),
            "distance_noise": self.distance_noise,
            "sensor_positions": self.SENSOR_CONFIGS
        }
