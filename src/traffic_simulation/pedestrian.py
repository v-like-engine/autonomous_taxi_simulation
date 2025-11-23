"""
Pedestrian simulation for traffic system.

This module implements realistic pedestrian behavior including walking on sidewalks,
crossing at crosswalks, and reacting to traffic.
"""

import math
import random
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from dataclasses import dataclass

from .behavior import PedestrianBehavior


class PedestrianState(Enum):
    """Current state of the pedestrian."""
    WALKING = "walking"
    WAITING = "waiting"
    CROSSING = "crossing"
    IDLE = "idle"


@dataclass
class PedestrianTarget:
    """Represents a target location for pedestrian."""
    x: float
    y: float
    is_crossing: bool = False  # True if this is a crossing waypoint


class Pedestrian:
    """
    Represents a pedestrian in the traffic simulation.

    Pedestrians walk on sidewalks, cross at crosswalks, and react to traffic.
    """

    _id_counter = 0

    def __init__(
        self,
        position: Tuple[float, float],
        caution_level: float = 0.5,
        color: Optional[str] = None
    ):
        """
        Initialize a pedestrian.

        Args:
            position: Initial (x, y) position in meters
            caution_level: Caution level (0.0-1.0), affects crossing behavior
            color: Pedestrian color (hex string), randomly assigned if None
        """
        # Unique ID
        Pedestrian._id_counter += 1
        self.id = Pedestrian._id_counter

        # Position and movement
        self.x, self.y = position
        self.heading = random.uniform(0.0, 360.0)  # Initial random heading
        self.speed = 0.0  # m/s

        # Physical properties
        self.radius = 0.3  # meters (pedestrian represented as a circle)

        # State
        self.state = PedestrianState.WALKING

        # Color (for visualization)
        if color is None:
            self.color = self._random_color()
        else:
            self.color = color

        # Behavior
        self.behavior = PedestrianBehavior(caution_level)

        # Navigation
        self.waypoints = []  # List of PedestrianTarget
        self.current_waypoint_index = 0
        self.current_target = None

        # Environment awareness
        self.on_sidewalk = True
        self.at_crosswalk = False
        self.nearest_vehicle = None
        self.nearest_vehicle_distance = float('inf')

        # Timing
        self.wait_timer = 0.0
        self.total_time = 0.0
        self.time_in_state = 0.0

        # Group behavior (optional)
        self.group_id = None  # If part of a group
        self.group_leader = None

    @staticmethod
    def _random_color() -> str:
        """Generate a random pedestrian color."""
        colors = [
            "#FF6B6B",  # Light Red
            "#4ECDC4",  # Turquoise
            "#45B7D1",  # Sky Blue
            "#FFA07A",  # Light Salmon
            "#98D8C8",  # Light Green
            "#F7DC6F",  # Light Yellow
            "#BB8FCE",  # Light Purple
            "#85C1E2",  # Light Blue
            "#F8B739",  # Orange
            "#52B788",  # Green
            "#E63946",  # Red
            "#1D3557",  # Navy
            "#F77F00",  # Dark Orange
            "#06FFA5",  # Mint
        ]
        return random.choice(colors)

    def update(self, dt: float, map_data: Optional[Dict] = None, vehicles: Optional[List] = None) -> None:
        """
        Update pedestrian state for one time step.

        Args:
            dt: Time step in seconds
            map_data: Map data from Agent 1 (sidewalks, crosswalks, etc.)
            vehicles: List of nearby vehicles for awareness
        """
        self.total_time += dt
        self.time_in_state += dt

        # Update vehicle awareness
        if vehicles:
            self._update_vehicle_awareness(vehicles)

        # Update based on state
        if self.state == PedestrianState.WALKING:
            self._update_walking(dt, map_data)
        elif self.state == PedestrianState.WAITING:
            self._update_waiting(dt)
        elif self.state == PedestrianState.CROSSING:
            self._update_crossing(dt, vehicles)
        elif self.state == PedestrianState.IDLE:
            self._update_idle(dt)

        # Apply movement
        self._update_movement(dt)

        # Safety check
        self._check_safety(vehicles)

    def _update_walking(self, dt: float, map_data: Optional[Dict]) -> None:
        """Update pedestrian while walking on sidewalk."""
        # Get target speed
        self.speed = self.behavior.get_walking_speed()

        # Follow waypoints
        if self.waypoints and self.current_waypoint_index < len(self.waypoints):
            target = self.waypoints[self.current_waypoint_index]
            self.current_target = target

            # Head towards target
            self.heading = self._heading_to((target.x, target.y))

            # Check if reached target
            if self._distance_to((target.x, target.y)) < 1.0:
                # Reached waypoint
                if target.is_crossing:
                    # Approaching a crossing
                    self.at_crosswalk = True
                    self.state = PedestrianState.WAITING
                    self.time_in_state = 0.0
                    self.speed = 0.0
                else:
                    # Normal waypoint, continue to next
                    self.current_waypoint_index += 1
                    if self.current_waypoint_index >= len(self.waypoints):
                        # Reached end of path
                        self._generate_new_path(map_data)
        else:
            # No waypoints, generate new path
            self._generate_new_path(map_data)

    def _update_waiting(self, dt: float) -> None:
        """Update pedestrian while waiting to cross."""
        self.speed = 0.0
        self.wait_timer += dt

        # Check if it's safe to cross
        if self.behavior.should_cross_road(
            self.nearest_vehicle is not None,
            self.nearest_vehicle_distance
        ):
            self.state = PedestrianState.CROSSING
            self.time_in_state = 0.0
            self.at_crosswalk = False
            self.on_sidewalk = False
            self.current_waypoint_index += 1  # Move to next waypoint (across street)
        elif self.wait_timer > 30.0:
            # Been waiting too long, maybe give up and find another path
            if random.random() < 0.1:  # 10% chance
                self.state = PedestrianState.WALKING
                self.wait_timer = 0.0
                self.current_waypoint_index += 1

    def _update_crossing(self, dt: float, vehicles: Optional[List]) -> None:
        """Update pedestrian while crossing the road."""
        # Move at normal walking speed (or faster if vehicle approaching)
        base_speed = self.behavior.get_walking_speed()

        # Check for approaching vehicles
        if self.nearest_vehicle and self.nearest_vehicle_distance < 20.0:
            # Speed up if vehicle is close
            if self.behavior.should_stop_for_vehicle(
                self.nearest_vehicle_distance,
                self.nearest_vehicle.speed if hasattr(self.nearest_vehicle, 'speed') else 0
            ):
                # Stop and yield
                self.speed = 0.0
                self.state = PedestrianState.WAITING
                return
            else:
                # Hurry across
                base_speed *= 1.5

        self.speed = base_speed

        # Continue to next waypoint
        if self.waypoints and self.current_waypoint_index < len(self.waypoints):
            target = self.waypoints[self.current_waypoint_index]
            self.heading = self._heading_to((target.x, target.y))

            # Check if reached other side
            if self._distance_to((target.x, target.y)) < 1.0:
                # Reached other side
                self.on_sidewalk = True
                self.state = PedestrianState.WALKING
                self.time_in_state = 0.0
                self.current_waypoint_index += 1
        else:
            # No target while crossing? Go back to walking
            self.state = PedestrianState.WALKING
            self.on_sidewalk = True

    def _update_idle(self, dt: float) -> None:
        """Update pedestrian while idle."""
        self.speed = 0.0

        # After some time, start walking again
        if self.time_in_state > random.uniform(3.0, 10.0):
            self.state = PedestrianState.WALKING
            self.time_in_state = 0.0

    def _update_movement(self, dt: float) -> None:
        """Apply movement based on speed and heading."""
        if self.speed > 0:
            heading_rad = math.radians(self.heading)
            self.x += self.speed * math.sin(heading_rad) * dt
            self.y -= self.speed * math.cos(heading_rad) * dt

    def _update_vehicle_awareness(self, vehicles: List) -> None:
        """Update awareness of nearby vehicles."""
        self.nearest_vehicle = None
        self.nearest_vehicle_distance = float('inf')

        for vehicle in vehicles:
            if hasattr(vehicle, 'x') and hasattr(vehicle, 'y'):
                dist = self._distance_to((vehicle.x, vehicle.y))
                if dist < self.nearest_vehicle_distance:
                    self.nearest_vehicle = vehicle
                    self.nearest_vehicle_distance = dist

    def _check_safety(self, vehicles: Optional[List]) -> None:
        """Check for dangerous situations and react."""
        if not vehicles:
            return

        # Check for very close vehicles
        for vehicle in vehicles:
            if hasattr(vehicle, 'x') and hasattr(vehicle, 'y'):
                dist = self._distance_to((vehicle.x, vehicle.y))
                if dist < 5.0 and hasattr(vehicle, 'speed') and vehicle.speed > 10.0:
                    # Vehicle very close and moving!
                    if self.state == PedestrianState.CROSSING:
                        # Emergency stop
                        self.speed = 0.0
                        self.state = PedestrianState.WAITING
                    elif self.state == PedestrianState.WALKING and not self.on_sidewalk:
                        # Jump back to safety
                        self.speed = self.behavior.get_walking_speed() * 2.0

    def _generate_new_path(self, map_data: Optional[Dict]) -> None:
        """
        Generate a new random walking path.

        Args:
            map_data: Map data with sidewalks and crosswalks
        """
        # Simplified path generation
        # In reality, this would use map_data to find sidewalk paths
        num_waypoints = random.randint(3, 8)
        self.waypoints = []

        # Generate random waypoints in a general direction
        base_distance = random.uniform(20.0, 50.0)
        general_direction = random.uniform(0.0, 360.0)

        for i in range(num_waypoints):
            # Random walk with some variation
            angle = general_direction + random.uniform(-45.0, 45.0)
            distance = base_distance + random.uniform(-10.0, 10.0)

            angle_rad = math.radians(angle)
            target_x = self.x + distance * math.sin(angle_rad)
            target_y = self.y - distance * math.cos(angle_rad)

            # Occasional crossing waypoint
            is_crossing = random.random() < 0.2  # 20% chance

            self.waypoints.append(PedestrianTarget(target_x, target_y, is_crossing))

        self.current_waypoint_index = 0

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

    def set_waypoints(self, waypoints: List[Tuple[float, float, bool]]) -> None:
        """
        Set waypoints for the pedestrian.

        Args:
            waypoints: List of (x, y, is_crossing) tuples
        """
        self.waypoints = [PedestrianTarget(x, y, is_crossing) for x, y, is_crossing in waypoints]
        self.current_waypoint_index = 0

    def stop(self) -> None:
        """Stop the pedestrian."""
        self.state = PedestrianState.IDLE
        self.speed = 0.0
        self.time_in_state = 0.0

    def resume(self) -> None:
        """Resume walking."""
        if self.state == PedestrianState.IDLE:
            self.state = PedestrianState.WALKING
            self.time_in_state = 0.0

    def check_collision(self, other: 'Pedestrian') -> bool:
        """
        Check if this pedestrian collides with another pedestrian.

        Args:
            other: Other pedestrian

        Returns:
            True if collision detected
        """
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx * dx + dy * dy)
        return distance < (self.radius + other.radius)

    def check_vehicle_collision(self, vehicle) -> bool:
        """
        Check if this pedestrian is hit by a vehicle.

        Args:
            vehicle: Vehicle to check

        Returns:
            True if collision detected
        """
        if not hasattr(vehicle, 'x') or not hasattr(vehicle, 'y'):
            return False

        dx = self.x - vehicle.x
        dy = self.y - vehicle.y
        distance = math.sqrt(dx * dx + dy * dy)

        # Use vehicle's collision radius if available
        vehicle_radius = getattr(vehicle, 'collision_radius', 3.0)
        return distance < (self.radius + vehicle_radius)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert pedestrian to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'heading': self.heading,
            'speed': self.speed,
            'state': self.state.value,
            'color': self.color,
            'radius': self.radius,
            'on_sidewalk': self.on_sidewalk,
            'caution_level': self.behavior.caution_level
        }

    def __repr__(self) -> str:
        return (f"Pedestrian(id={self.id}, "
                f"pos=({self.x:.1f}, {self.y:.1f}), "
                f"state={self.state.value})")


def create_pedestrian_group(
    center_position: Tuple[float, float],
    count: int,
    spread: float = 3.0
) -> List[Pedestrian]:
    """
    Create a group of pedestrians near each other.

    Args:
        center_position: Center (x, y) position for the group
        count: Number of pedestrians in the group
        spread: How spread out the group is (in meters)

    Returns:
        List of Pedestrian objects
    """
    group_id = Pedestrian._id_counter + 1
    pedestrians = []

    for i in range(count):
        # Random position around center
        angle = random.uniform(0.0, 360.0)
        distance = random.uniform(0.0, spread)
        angle_rad = math.radians(angle)

        x = center_position[0] + distance * math.cos(angle_rad)
        y = center_position[1] + distance * math.sin(angle_rad)

        # Similar caution levels for group members
        base_caution = random.uniform(0.3, 0.7)
        caution = base_caution + random.uniform(-0.1, 0.1)

        ped = Pedestrian((x, y), caution)
        ped.group_id = group_id

        # First pedestrian is the leader
        if i == 0:
            ped.group_leader = ped
        else:
            ped.group_leader = pedestrians[0]

        pedestrians.append(ped)

    return pedestrians
