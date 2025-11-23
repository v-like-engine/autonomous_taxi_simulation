"""
Temperature-based random behavior system for traffic simulation.

This module implements realistic driver and pedestrian behavior using a temperature parameter:
- Low temperature (0.0-0.3): Careful, rule-following behavior
- Medium temperature (0.3-0.7): Normal behavior with occasional violations
- High temperature (0.7-1.0): Aggressive behavior with frequent violations
"""

import random
import math
from typing import Dict, Any, Optional
from enum import Enum


class BehaviorType(Enum):
    """Types of behavior that can be triggered."""
    NORMAL = "normal"
    SPEEDING = "speeding"
    AGGRESSIVE_ACCELERATION = "aggressive_acceleration"
    SUDDEN_BRAKING = "sudden_braking"
    LANE_CHANGE = "lane_change"
    CUTTING_OFF = "cutting_off"
    RUNNING_LIGHT = "running_light"
    TAILGATING = "tailgating"


class DriverBehavior:
    """
    Manages driver behavior based on temperature parameter.

    Temperature ranges:
    - 0.0-0.3: Careful driver (follows rules strictly, safe distances, no violations)
    - 0.3-0.7: Normal driver (mostly follows rules, occasional minor violations)
    - 0.7-1.0: Aggressive driver (frequent violations, risky maneuvers)
    """

    def __init__(self, temperature: float = 0.5):
        """
        Initialize driver behavior.

        Args:
            temperature: Behavior temperature (0.0-1.0)
        """
        self.temperature = max(0.0, min(1.0, temperature))
        self._last_behavior_time = 0.0
        self._current_behavior = BehaviorType.NORMAL
        self._behavior_duration = 0.0

    def update(self, dt: float) -> None:
        """Update behavior state."""
        self._last_behavior_time += dt
        if self._last_behavior_time >= self._behavior_duration:
            self._current_behavior = BehaviorType.NORMAL

    def get_speed_multiplier(self, base_speed_limit: float) -> float:
        """
        Get speed multiplier based on temperature.

        Args:
            base_speed_limit: Base speed limit in km/h

        Returns:
            Speed multiplier (1.0 = speed limit, >1.0 = speeding)
        """
        if self.temperature < 0.3:
            # Careful driver: stays at or below speed limit
            return random.uniform(0.8, 1.0)
        elif self.temperature < 0.7:
            # Normal driver: occasional slight speeding
            if random.random() < 0.3:  # 30% chance of speeding
                return random.uniform(1.0, 1.15)
            return random.uniform(0.9, 1.05)
        else:
            # Aggressive driver: frequent speeding
            if random.random() < 0.7:  # 70% chance of speeding
                # Can go up to +20 km/h over limit
                overspeed = random.uniform(5, 20)
                return 1.0 + (overspeed / base_speed_limit)
            return random.uniform(1.0, 1.1)

    def should_change_lane(self, current_time: float) -> bool:
        """
        Determine if vehicle should attempt a lane change.

        Args:
            current_time: Current simulation time

        Returns:
            True if should attempt lane change
        """
        # Cooldown between lane changes
        min_time_between_changes = 5.0 - (self.temperature * 3.0)  # 5s to 2s
        if current_time - self._last_behavior_time < min_time_between_changes:
            return False

        # Probability based on temperature
        if self.temperature < 0.3:
            probability = 0.05  # Rare lane changes
        elif self.temperature < 0.7:
            probability = 0.15  # Occasional lane changes
        else:
            probability = 0.35  # Frequent lane changes

        if random.random() < probability:
            self._last_behavior_time = current_time
            return True
        return False

    def can_cut_off(self, gap_size: float, safe_gap: float) -> bool:
        """
        Determine if driver will cut off another vehicle.

        Args:
            gap_size: Available gap in meters
            safe_gap: Recommended safe gap in meters

        Returns:
            True if driver will attempt to cut off
        """
        if self.temperature < 0.3:
            # Careful: never cut off, needs extra space
            return gap_size >= safe_gap * 1.5
        elif self.temperature < 0.7:
            # Normal: occasionally accepts smaller gaps
            if random.random() < 0.2:
                return gap_size >= safe_gap * 0.8
            return gap_size >= safe_gap
        else:
            # Aggressive: frequently accepts small gaps
            if random.random() < 0.6:
                return gap_size >= safe_gap * 0.5
            return gap_size >= safe_gap * 0.7

    def should_run_yellow_light(self, distance_to_light: float, current_speed: float) -> bool:
        """
        Determine if driver will run a yellow light.

        Args:
            distance_to_light: Distance to traffic light in meters
            current_speed: Current speed in km/h

        Returns:
            True if driver will run the yellow light
        """
        # Convert speed to m/s
        speed_ms = current_speed / 3.6

        # Time to reach light
        if speed_ms > 0:
            time_to_light = distance_to_light / speed_ms
        else:
            return False

        if self.temperature < 0.3:
            # Careful: stops if more than 1 second away
            return time_to_light < 1.0
        elif self.temperature < 0.7:
            # Normal: stops if more than 2 seconds away
            return time_to_light < 2.0
        else:
            # Aggressive: often runs yellow, sometimes red
            if random.random() < 0.3:
                return time_to_light < 4.0  # Run even from far away
            return time_to_light < 3.0

    def should_run_red_light(self) -> bool:
        """
        Determine if driver will run a red light (very rare).

        Returns:
            True if driver will run red light
        """
        if self.temperature < 0.7:
            return False  # Only aggressive drivers run red lights
        return random.random() < (self.temperature - 0.7) * 0.2  # Max 6% chance at temp=1.0

    def get_acceleration_multiplier(self) -> float:
        """
        Get acceleration multiplier based on temperature.

        Returns:
            Acceleration multiplier (1.0 = normal, >1.0 = aggressive)
        """
        if self.temperature < 0.3:
            # Gentle acceleration
            return random.uniform(0.6, 0.8)
        elif self.temperature < 0.7:
            # Normal acceleration
            return random.uniform(0.8, 1.1)
        else:
            # Aggressive acceleration
            return random.uniform(1.1, 1.5)

    def get_braking_multiplier(self) -> float:
        """
        Get braking multiplier based on temperature.

        Returns:
            Braking multiplier (1.0 = normal, >1.0 = harder braking)
        """
        if self.temperature < 0.3:
            # Gentle braking, starts early
            return random.uniform(0.5, 0.7)
        elif self.temperature < 0.7:
            # Normal braking
            return random.uniform(0.7, 1.0)
        else:
            # Late, hard braking
            return random.uniform(0.8, 1.2)

    def should_sudden_brake(self, current_time: float) -> bool:
        """
        Determine if driver should suddenly brake (distracted/mistake).

        Args:
            current_time: Current simulation time

        Returns:
            True if should suddenly brake
        """
        # Only medium and high temperature drivers make mistakes
        if self.temperature < 0.3:
            return False

        # Cooldown
        if current_time - self._last_behavior_time < 10.0:
            return False

        # Low probability event
        probability = self.temperature * 0.02  # Max 2% at temp=1.0
        if random.random() < probability:
            self._last_behavior_time = current_time
            self._current_behavior = BehaviorType.SUDDEN_BRAKING
            self._behavior_duration = random.uniform(1.0, 2.0)
            return True
        return False

    def get_following_distance_multiplier(self) -> float:
        """
        Get following distance multiplier.

        Returns:
            Distance multiplier (1.0 = safe, <1.0 = tailgating)
        """
        if self.temperature < 0.3:
            # Careful: maintains extra distance
            return random.uniform(1.5, 2.0)
        elif self.temperature < 0.7:
            # Normal: safe following distance
            return random.uniform(1.0, 1.3)
        else:
            # Aggressive: tailgating
            if random.random() < 0.5:
                return random.uniform(0.5, 0.8)  # Unsafe distance
            return random.uniform(0.8, 1.0)


class PedestrianBehavior:
    """
    Manages pedestrian behavior with slight randomness.

    Pedestrians are generally more predictable than drivers but still have
    some variation in behavior.
    """

    def __init__(self, caution_level: float = 0.5):
        """
        Initialize pedestrian behavior.

        Args:
            caution_level: How cautious the pedestrian is (0.0-1.0)
        """
        self.caution_level = max(0.0, min(1.0, caution_level))
        self.base_speed = random.uniform(1.2, 1.8)  # m/s (4.3-6.5 km/h)

    def get_walking_speed(self) -> float:
        """
        Get current walking speed.

        Returns:
            Speed in m/s
        """
        # Add some variation
        variation = random.uniform(-0.2, 0.2)
        return max(0.5, self.base_speed + variation)

    def should_cross_road(self, traffic_nearby: bool, distance_to_nearest_car: float) -> bool:
        """
        Determine if pedestrian should cross the road.

        Args:
            traffic_nearby: True if traffic is nearby
            distance_to_nearest_car: Distance to nearest car in meters

        Returns:
            True if should cross
        """
        if not traffic_nearby:
            return True

        # Safe distance based on caution level
        if self.caution_level < 0.3:
            # Less cautious: crosses with smaller gaps
            safe_distance = 20.0
        elif self.caution_level < 0.7:
            # Normal caution
            safe_distance = 30.0
        else:
            # Very cautious: waits for large gaps
            safe_distance = 40.0

        return distance_to_nearest_car >= safe_distance

    def should_jaywalk(self) -> bool:
        """
        Determine if pedestrian will jaywalk (rare).

        Returns:
            True if will jaywalk
        """
        # Less cautious pedestrians are more likely to jaywalk
        if self.caution_level > 0.5:
            return False
        return random.random() < (0.5 - self.caution_level) * 0.1  # Max 5% chance

    def get_reaction_distance(self) -> float:
        """
        Get distance at which pedestrian reacts to approaching vehicle.

        Returns:
            Reaction distance in meters
        """
        if self.caution_level < 0.3:
            return random.uniform(5.0, 10.0)
        elif self.caution_level < 0.7:
            return random.uniform(10.0, 15.0)
        else:
            return random.uniform(15.0, 25.0)

    def should_stop_for_vehicle(self, vehicle_distance: float, vehicle_speed: float) -> bool:
        """
        Determine if pedestrian should stop for an approaching vehicle.

        Args:
            vehicle_distance: Distance to vehicle in meters
            vehicle_speed: Vehicle speed in km/h

        Returns:
            True if should stop
        """
        # Calculate time to collision
        if vehicle_speed > 0:
            speed_ms = vehicle_speed / 3.6
            time_to_collision = vehicle_distance / speed_ms
        else:
            return False

        # Reaction time based on caution
        if self.caution_level < 0.3:
            reaction_time = 2.0  # Reacts late
        elif self.caution_level < 0.7:
            reaction_time = 3.0  # Normal reaction
        else:
            reaction_time = 5.0  # Reacts early

        return time_to_collision <= reaction_time


def generate_temperature_distribution(count: int, mean: float = 0.5, std: float = 0.2) -> list:
    """
    Generate a distribution of temperature values for a population.

    Creates a realistic distribution where most drivers are normal,
    with fewer careful and aggressive drivers.

    Args:
        count: Number of temperature values to generate
        mean: Mean temperature (default 0.5 for normal distribution)
        std: Standard deviation (default 0.2)

    Returns:
        List of temperature values
    """
    temperatures = []
    for _ in range(count):
        # Use normal distribution and clamp to [0, 1]
        temp = random.gauss(mean, std)
        temp = max(0.0, min(1.0, temp))
        temperatures.append(temp)
    return temperatures


def get_behavior_description(temperature: float) -> str:
    """
    Get a human-readable description of behavior for a given temperature.

    Args:
        temperature: Temperature value (0.0-1.0)

    Returns:
        Description string
    """
    if temperature < 0.3:
        return "Careful driver - follows rules strictly, maintains safe distances"
    elif temperature < 0.7:
        return "Normal driver - mostly follows rules, occasional minor violations"
    else:
        return "Aggressive driver - frequent violations, risky maneuvers"
