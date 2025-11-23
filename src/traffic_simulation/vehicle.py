"""
Vehicle simulation for traffic system.

This module implements realistic vehicle physics and behavior for cars and trucks,
including lane following, collision avoidance, and temperature-based random behavior.
"""

import math
import random
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass

from .behavior import DriverBehavior, BehaviorType


class VehicleType(Enum):
    """Types of vehicles in the simulation."""
    CAR = "car"
    TRUCK = "truck"
    TAXI = "taxi"  # For the main self-driving taxi


@dataclass
class VehicleSpecs:
    """Physical specifications for a vehicle type."""
    length: float  # meters
    width: float  # meters
    max_speed: float  # km/h
    max_acceleration: float  # m/s²
    max_deceleration: float  # m/s²
    max_steering_angle: float  # degrees
    turning_radius: float  # meters
    mass: float  # kg


# Default specifications for each vehicle type
VEHICLE_SPECS = {
    VehicleType.CAR: VehicleSpecs(
        length=4.5,
        width=2.0,
        max_speed=180.0,
        max_acceleration=3.5,
        max_deceleration=8.0,
        max_steering_angle=35.0,
        turning_radius=5.0,
        mass=1500.0
    ),
    VehicleType.TRUCK: VehicleSpecs(
        length=8.0,
        width=2.5,
        max_speed=120.0,
        max_acceleration=2.0,
        max_deceleration=6.0,
        max_steering_angle=25.0,
        turning_radius=8.0,
        mass=8000.0
    ),
    VehicleType.TAXI: VehicleSpecs(
        length=4.5,
        width=2.0,
        max_speed=160.0,
        max_acceleration=3.0,
        max_deceleration=8.0,
        max_steering_angle=35.0,
        turning_radius=5.0,
        mass=1600.0
    )
}


class VehicleState(Enum):
    """Current state of the vehicle."""
    DRIVING = "driving"
    STOPPING = "stopping"
    STOPPED = "stopped"
    TURNING = "turning"
    LANE_CHANGING = "lane_changing"
    YIELDING = "yielding"


class Vehicle:
    """
    Represents a vehicle in the traffic simulation.

    Handles physics, behavior, navigation, and collision detection for
    realistic vehicle simulation.
    """

    _id_counter = 0

    def __init__(
        self,
        vehicle_type: VehicleType,
        position: Tuple[float, float],
        heading: float = 0.0,
        temperature: float = 0.5,
        color: Optional[str] = None
    ):
        """
        Initialize a vehicle.

        Args:
            vehicle_type: Type of vehicle (CAR, TRUCK, or TAXI)
            position: Initial (x, y) position in meters
            heading: Initial heading in degrees (0 = north, 90 = east)
            temperature: Driver behavior temperature (0.0-1.0)
            color: Vehicle color (hex string), randomly assigned if None
        """
        # Unique ID
        Vehicle._id_counter += 1
        self.id = Vehicle._id_counter

        # Type and specifications
        self.type = vehicle_type
        self.specs = VEHICLE_SPECS[vehicle_type]

        # Position and orientation
        self.x, self.y = position
        self.heading = heading  # degrees
        self.speed = 0.0  # km/h
        self.acceleration = 0.0  # m/s²

        # Steering
        self.steering_angle = 0.0  # degrees

        # State
        self.state = VehicleState.DRIVING

        # Color
        if color is None:
            self.color = self._random_color()
        else:
            self.color = color

        # Behavior
        self.behavior = DriverBehavior(temperature)

        # Navigation
        self.path = []  # List of waypoints [(x, y), ...]
        self.current_waypoint_index = 0
        self.current_lane = None
        self.target_lane = None

        # Target values for control
        self.target_speed = 0.0  # km/h
        self.target_position = None

        # Collision detection
        self.collision_radius = math.sqrt(
            (self.specs.length / 2) ** 2 + (self.specs.width / 2) ** 2
        )

        # Traffic awareness
        self.vehicle_ahead = None
        self.distance_to_ahead = float('inf')

        # Simulation time tracking
        self.time_in_state = 0.0
        self.total_time = 0.0

    @staticmethod
    def _random_color() -> str:
        """Generate a random vehicle color."""
        colors = [
            "#FF0000",  # Red
            "#0000FF",  # Blue
            "#00FF00",  # Green
            "#FFFF00",  # Yellow
            "#FF00FF",  # Magenta
            "#00FFFF",  # Cyan
            "#FFA500",  # Orange
            "#800080",  # Purple
            "#FFC0CB",  # Pink
            "#A52A2A",  # Brown
            "#808080",  # Gray
            "#000000",  # Black
            "#FFFFFF",  # White
            "#C0C0C0",  # Silver
        ]
        return random.choice(colors)

    def update(self, dt: float, map_data: Optional[Dict] = None) -> None:
        """
        Update vehicle state for one time step.

        Args:
            dt: Time step in seconds
            map_data: Map data from Agent 1 (zones, roads, etc.)
        """
        self.total_time += dt
        self.time_in_state += dt
        self.behavior.update(dt)

        # Update control based on current state
        if self.state == VehicleState.DRIVING:
            self._update_driving(dt, map_data)
        elif self.state == VehicleState.STOPPING:
            self._update_stopping(dt)
        elif self.state == VehicleState.STOPPED:
            self._update_stopped(dt)
        elif self.state == VehicleState.TURNING:
            self._update_turning(dt)
        elif self.state == VehicleState.LANE_CHANGING:
            self._update_lane_changing(dt)
        elif self.state == VehicleState.YIELDING:
            self._update_yielding(dt)

        # Apply physics
        self._update_physics(dt)

        # Update behavior triggers
        self._check_behavior_triggers(dt)

    def _update_driving(self, dt: float, map_data: Optional[Dict]) -> None:
        """Update vehicle while in driving state."""
        # Follow path if we have one
        if self.path and self.current_waypoint_index < len(self.path):
            target = self.path[self.current_waypoint_index]
            self._steer_towards(target)

            # Check if we reached waypoint
            dist = self._distance_to(target)
            if dist < 3.0:  # Within 3 meters
                self.current_waypoint_index += 1

        # Speed control
        if map_data and 'zones' in map_data:
            speed_limit = self._get_speed_limit(map_data)
            self.target_speed = speed_limit * self.behavior.get_speed_multiplier(speed_limit)
        else:
            self.target_speed = 50.0  # Default if no map data

        # Adjust for vehicle ahead
        if self.vehicle_ahead and self.distance_to_ahead < 50.0:
            # Calculate safe following distance
            safe_distance = (self.speed / 3.6) * 2.0  # 2 second rule
            safe_distance *= self.behavior.get_following_distance_multiplier()

            if self.distance_to_ahead < safe_distance:
                # Slow down
                self.target_speed = min(self.target_speed, self.vehicle_ahead.speed * 0.9)

                if self.distance_to_ahead < safe_distance * 0.5:
                    # Emergency braking
                    self.acceleration = -self.specs.max_deceleration

    def _update_stopping(self, dt: float) -> None:
        """Update vehicle while stopping."""
        self.target_speed = 0.0
        if self.speed < 1.0:
            self.speed = 0.0
            self.state = VehicleState.STOPPED
            self.time_in_state = 0.0

    def _update_stopped(self, dt: float) -> None:
        """Update vehicle while stopped."""
        self.speed = 0.0
        self.acceleration = 0.0

        # After some time, resume driving
        if self.time_in_state > random.uniform(2.0, 5.0):
            self.state = VehicleState.DRIVING
            self.time_in_state = 0.0

    def _update_turning(self, dt: float) -> None:
        """Update vehicle while turning."""
        # Reduce speed for turning
        turn_speed = min(self.target_speed, 30.0)
        self.target_speed = turn_speed

        # Check if turn is complete
        if self.path and self.current_waypoint_index < len(self.path):
            target = self.path[self.current_waypoint_index]
            heading_diff = self._angle_difference(self.heading, self._heading_to(target))
            if abs(heading_diff) < 10.0:
                self.state = VehicleState.DRIVING
                self.time_in_state = 0.0

    def _update_lane_changing(self, dt: float) -> None:
        """Update vehicle while changing lanes."""
        if self.target_lane is not None:
            # Steer towards target lane
            # This is simplified - in reality we'd need the lane center line
            if self.time_in_state > 3.0:  # Lane change takes ~3 seconds
                self.current_lane = self.target_lane
                self.target_lane = None
                self.state = VehicleState.DRIVING
                self.time_in_state = 0.0

    def _update_yielding(self, dt: float) -> None:
        """Update vehicle while yielding."""
        self.target_speed = min(self.speed * 0.5, 10.0)

        # After yielding for a while, resume
        if self.time_in_state > 2.0:
            self.state = VehicleState.DRIVING
            self.time_in_state = 0.0

    def _update_physics(self, dt: float) -> None:
        """Apply physics to update position and velocity."""
        # Speed control
        speed_error = self.target_speed - self.speed
        if abs(speed_error) > 0.1:
            if speed_error > 0:
                # Accelerate
                accel = self.specs.max_acceleration * self.behavior.get_acceleration_multiplier()
                self.acceleration = min(accel, speed_error / dt)
            else:
                # Decelerate
                decel = self.specs.max_deceleration * self.behavior.get_braking_multiplier()
                self.acceleration = max(-decel, speed_error / dt)
        else:
            self.acceleration = 0.0

        # Update speed (km/h)
        speed_ms = self.speed / 3.6  # Convert to m/s
        speed_ms += self.acceleration * dt
        speed_ms = max(0.0, min(speed_ms, self.specs.max_speed / 3.6))
        self.speed = speed_ms * 3.6  # Convert back to km/h

        # Update steering (simplified)
        max_steering_rate = 30.0  # degrees per second
        self.steering_angle = max(
            -self.specs.max_steering_angle,
            min(self.specs.max_steering_angle, self.steering_angle)
        )

        # Update heading based on steering and speed
        if speed_ms > 0.1 and abs(self.steering_angle) > 0.1:
            # Simplified steering model
            turn_rate = (speed_ms / self.specs.turning_radius) * (self.steering_angle / self.specs.max_steering_angle)
            self.heading += math.degrees(turn_rate * dt)
            self.heading = self.heading % 360.0

        # Update position
        heading_rad = math.radians(self.heading)
        self.x += speed_ms * math.sin(heading_rad) * dt
        self.y -= speed_ms * math.cos(heading_rad) * dt

    def _check_behavior_triggers(self, dt: float) -> None:
        """Check for behavior-based random events."""
        # Sudden braking
        if self.behavior.should_sudden_brake(self.total_time):
            self.target_speed = 0.0
            self.acceleration = -self.specs.max_deceleration * 0.8

        # Lane changes
        if self.state == VehicleState.DRIVING and self.behavior.should_change_lane(self.total_time):
            if self.current_lane is not None:
                self.state = VehicleState.LANE_CHANGING
                self.time_in_state = 0.0
                # In reality, we'd pick an adjacent lane
                self.target_lane = self.current_lane + random.choice([-1, 1])

    def _steer_towards(self, target: Tuple[float, float]) -> None:
        """
        Steer vehicle towards a target position.

        Args:
            target: Target (x, y) position
        """
        target_heading = self._heading_to(target)
        heading_error = self._angle_difference(self.heading, target_heading)

        # Simple proportional control for steering
        k_steer = 2.0
        self.steering_angle = max(
            -self.specs.max_steering_angle,
            min(self.specs.max_steering_angle, heading_error * k_steer)
        )

    def _heading_to(self, target: Tuple[float, float]) -> float:
        """
        Calculate heading to a target position.

        Args:
            target: Target (x, y) position

        Returns:
            Heading in degrees
        """
        dx = target[0] - self.x
        dy = target[1] - self.y
        heading = math.degrees(math.atan2(dx, -dy))
        return heading % 360.0

    def _distance_to(self, target: Tuple[float, float]) -> float:
        """
        Calculate distance to a target position.

        Args:
            target: Target (x, y) position

        Returns:
            Distance in meters
        """
        dx = target[0] - self.x
        dy = target[1] - self.y
        return math.sqrt(dx * dx + dy * dy)

    @staticmethod
    def _angle_difference(a: float, b: float) -> float:
        """
        Calculate the smallest difference between two angles.

        Args:
            a: First angle in degrees
            b: Second angle in degrees

        Returns:
            Difference in degrees (-180 to 180)
        """
        diff = (b - a + 180.0) % 360.0 - 180.0
        return diff

    def _get_speed_limit(self, map_data: Dict) -> float:
        """
        Get speed limit at current position.

        Args:
            map_data: Map data from Agent 1

        Returns:
            Speed limit in km/h
        """
        # Default speed limits by zone type
        # This is a simplified version - in reality we'd check the actual zone
        return 50.0  # Default urban speed

    def set_path(self, waypoints: List[Tuple[float, float]]) -> None:
        """
        Set navigation path for the vehicle.

        Args:
            waypoints: List of (x, y) waypoints
        """
        self.path = waypoints
        self.current_waypoint_index = 0

    def stop(self) -> None:
        """Command the vehicle to stop."""
        self.state = VehicleState.STOPPING

    def resume(self) -> None:
        """Command the vehicle to resume driving."""
        if self.state == VehicleState.STOPPED:
            self.state = VehicleState.DRIVING
            self.time_in_state = 0.0

    def set_vehicle_ahead(self, vehicle: Optional['Vehicle'], distance: float) -> None:
        """
        Set the vehicle ahead for following behavior.

        Args:
            vehicle: Vehicle ahead (or None if no vehicle)
            distance: Distance to vehicle in meters
        """
        self.vehicle_ahead = vehicle
        self.distance_to_ahead = distance

    def get_bounds(self) -> Tuple[float, float, float, float]:
        """
        Get axis-aligned bounding box for collision detection.

        Returns:
            (min_x, min_y, max_x, max_y) in meters
        """
        # Simplified bounding box (doesn't account for rotation)
        half_length = self.specs.length / 2
        half_width = self.specs.width / 2

        return (
            self.x - half_width,
            self.y - half_length,
            self.x + half_width,
            self.y + half_length
        )

    def get_corners(self) -> List[Tuple[float, float]]:
        """
        Get the four corner positions of the vehicle (accounting for rotation).

        Returns:
            List of (x, y) corner positions
        """
        half_length = self.specs.length / 2
        half_width = self.specs.width / 2
        heading_rad = math.radians(self.heading)

        cos_h = math.cos(heading_rad)
        sin_h = math.sin(heading_rad)

        # Four corners relative to center
        corners_rel = [
            (-half_width, -half_length),
            (half_width, -half_length),
            (half_width, half_length),
            (-half_width, half_length)
        ]

        # Rotate and translate
        corners = []
        for cx, cy in corners_rel:
            x = self.x + cx * cos_h - cy * sin_h
            y = self.y + cx * sin_h + cy * cos_h
            corners.append((x, y))

        return corners

    def check_collision(self, other: 'Vehicle') -> bool:
        """
        Check if this vehicle collides with another vehicle.

        Args:
            other: Other vehicle to check

        Returns:
            True if collision detected
        """
        # Quick circle-based check first
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance > self.collision_radius + other.collision_radius:
            return False

        # More detailed check could use separating axis theorem
        # For now, the circle check is sufficient
        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert vehicle to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'type': self.type.value,
            'x': self.x,
            'y': self.y,
            'heading': self.heading,
            'speed': self.speed,
            'acceleration': self.acceleration,
            'steering_angle': self.steering_angle,
            'state': self.state.value,
            'color': self.color,
            'length': self.specs.length,
            'width': self.specs.width,
            'temperature': self.behavior.temperature
        }

    def __repr__(self) -> str:
        return (f"Vehicle(id={self.id}, type={self.type.value}, "
                f"pos=({self.x:.1f}, {self.y:.1f}), "
                f"heading={self.heading:.1f}°, speed={self.speed:.1f} km/h)")
