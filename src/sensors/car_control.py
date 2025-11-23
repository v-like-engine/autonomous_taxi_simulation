"""
Car control interface for autonomous taxi.

Provides a realistic control interface between the RL agent and the car,
with physical limits, smooth actuation, and response delays.
"""

import numpy as np
import math
from typing import Dict, Any, Tuple, Optional


class CarControl:
    """
    Interface for controlling the autonomous car.

    Accepts control commands from the RL agent and applies them with
    realistic physical limitations and response characteristics.
    """

    def __init__(
        self,
        max_throttle_rate: float = 2.0,  # per second (0 to 1)
        max_brake_rate: float = 3.0,  # per second (0 to 1)
        max_steering_rate: float = 90.0,  # degrees per second
        max_steering_angle: float = 35.0,  # degrees
        max_acceleration: float = 4.0,  # m/s²
        max_deceleration: float = 8.0,  # m/s²
        throttle_response_delay: float = 0.1,  # seconds
        brake_response_delay: float = 0.05,  # seconds
        steering_response_delay: float = 0.05,  # seconds
        wheelbase: float = 2.7,  # meters (distance between front and rear axles)
        mass: float = 1500.0,  # kg
        auto_gear: bool = True  # automatic gear selection
    ):
        """
        Initialize car control system.

        Args:
            max_throttle_rate: Maximum rate of throttle change per second
            max_brake_rate: Maximum rate of brake change per second
            max_steering_rate: Maximum steering angle change rate (degrees/sec)
            max_steering_angle: Maximum steering angle (degrees)
            max_acceleration: Maximum forward acceleration (m/s²)
            max_deceleration: Maximum braking deceleration (m/s²)
            throttle_response_delay: Throttle response time (seconds)
            brake_response_delay: Brake response time (seconds)
            steering_response_delay: Steering response time (seconds)
            wheelbase: Distance between front and rear axles (meters)
            mass: Vehicle mass (kg)
            auto_gear: Whether to automatically select gears
        """
        self.max_throttle_rate = max_throttle_rate
        self.max_brake_rate = max_brake_rate
        self.max_steering_rate = max_steering_rate
        self.max_steering_angle = max_steering_angle
        self.max_acceleration = max_acceleration
        self.max_deceleration = max_deceleration
        self.throttle_response_delay = throttle_response_delay
        self.brake_response_delay = brake_response_delay
        self.steering_response_delay = steering_response_delay
        self.wheelbase = wheelbase
        self.mass = mass
        self.auto_gear = auto_gear

        # Current control state
        self.current_throttle = 0.0
        self.current_brake = 0.0
        self.current_steering = 0.0  # -1 to 1
        self.current_gear = 1

        # Target control state (what RL agent wants)
        self.target_throttle = 0.0
        self.target_brake = 0.0
        self.target_steering = 0.0
        self.target_gear = 1

        # Response delay buffers
        self.throttle_buffer = []
        self.brake_buffer = []
        self.steering_buffer = []

    def set_control(
        self,
        throttle: Optional[float] = None,
        brake: Optional[float] = None,
        steering: Optional[float] = None,
        gear: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Set control inputs from the RL agent.

        Args:
            throttle: Throttle position 0.0-1.0 (None = no change)
            brake: Brake position 0.0-1.0 (None = no change)
            steering: Steering -1.0 (full left) to 1.0 (full right) (None = no change)
            gear: Gear selection -1 (reverse), 0 (neutral), 1-5 (forward) (None = no change)

        Returns:
            Dictionary with validated control values
        """
        # Validate and set targets
        if throttle is not None:
            self.target_throttle = self._clamp(throttle, 0.0, 1.0)

        if brake is not None:
            self.target_brake = self._clamp(brake, 0.0, 1.0)

        if steering is not None:
            self.target_steering = self._clamp(steering, -1.0, 1.0)

        if gear is not None and not self.auto_gear:
            self.target_gear = self._clamp(gear, -1, 5)

        return {
            "target_throttle": self.target_throttle,
            "target_brake": self.target_brake,
            "target_steering": self.target_steering,
            "target_gear": self.target_gear,
            "current_throttle": self.current_throttle,
            "current_brake": self.current_brake,
            "current_steering": self.current_steering,
            "current_gear": self.current_gear
        }

    def update(
        self,
        delta_time: float,
        current_speed: float
    ) -> Dict[str, Any]:
        """
        Update control state with smooth transitions and delays.

        Args:
            delta_time: Time since last update (seconds)
            current_speed: Current vehicle speed (m/s)

        Returns:
            Dictionary with current control state
        """
        # Update throttle with rate limiting
        throttle_change = self.target_throttle - self.current_throttle
        max_change = self.max_throttle_rate * delta_time
        if abs(throttle_change) > max_change:
            throttle_change = np.sign(throttle_change) * max_change
        self.current_throttle += throttle_change
        self.current_throttle = self._clamp(self.current_throttle, 0.0, 1.0)

        # Update brake with rate limiting
        brake_change = self.target_brake - self.current_brake
        max_change = self.max_brake_rate * delta_time
        if abs(brake_change) > max_change:
            brake_change = np.sign(brake_change) * max_change
        self.current_brake += brake_change
        self.current_brake = self._clamp(self.current_brake, 0.0, 1.0)

        # Throttle and brake are mutually exclusive
        if self.current_brake > 0.1:
            self.current_throttle = 0.0

        # Update steering with rate limiting
        steering_change = self.target_steering - self.current_steering
        max_change = (self.max_steering_rate / self.max_steering_angle) * delta_time
        if abs(steering_change) > max_change:
            steering_change = np.sign(steering_change) * max_change
        self.current_steering += steering_change
        self.current_steering = self._clamp(self.current_steering, -1.0, 1.0)

        # Update gear (automatic or manual)
        if self.auto_gear:
            self.current_gear = self._select_automatic_gear(current_speed)
        else:
            # Manual gear change (instant for now, could add delay)
            self.current_gear = self.target_gear

        return self.get_control_state()

    def apply_to_physics(
        self,
        car_state: Dict[str, Any],
        delta_time: float
    ) -> Dict[str, Any]:
        """
        Apply control inputs to update car physics state.

        Args:
            car_state: Current state of the car
            delta_time: Time step (seconds)

        Returns:
            Updated car state
        """
        # Extract current state
        position = car_state.get("position", (0.0, 0.0))
        velocity = car_state.get("velocity", (0.0, 0.0))
        heading = car_state.get("heading", 0.0)
        angular_velocity = car_state.get("angular_velocity", 0.0)

        # Calculate current speed
        speed = math.sqrt(velocity[0]**2 + velocity[1]**2)

        # Calculate acceleration based on throttle and brake
        acceleration = self._calculate_acceleration(speed)

        # Update velocity magnitude
        new_speed = speed + acceleration * delta_time
        new_speed = max(0.0, new_speed)  # Can't go negative

        # Calculate steering-induced angular velocity
        if abs(new_speed) > 0.1:  # Only turn if moving
            # Bicycle model for turning
            steering_angle_rad = math.radians(self.current_steering * self.max_steering_angle)
            turn_radius = self.wheelbase / (math.tan(steering_angle_rad) + 1e-6)
            angular_velocity = new_speed / turn_radius
        else:
            angular_velocity = 0.0

        # Update heading
        new_heading = (heading + math.degrees(angular_velocity * delta_time)) % 360

        # Calculate new velocity components
        heading_rad = math.radians(new_heading)
        new_velocity = (
            new_speed * math.cos(heading_rad),
            new_speed * math.sin(heading_rad)
        )

        # Update position
        new_position = (
            position[0] + new_velocity[0] * delta_time,
            position[1] + new_velocity[1] * delta_time
        )

        # Return updated state
        return {
            "position": new_position,
            "velocity": new_velocity,
            "heading": new_heading,
            "angular_velocity": angular_velocity,
            "acceleration": acceleration,
            "speed": new_speed
        }

    def _calculate_acceleration(self, current_speed: float) -> float:
        """
        Calculate acceleration based on throttle and brake inputs.

        Args:
            current_speed: Current speed in m/s

        Returns:
            Acceleration in m/s²
        """
        if self.current_brake > 0.1:
            # Braking
            deceleration = -self.current_brake * self.max_deceleration
            return deceleration
        elif self.current_throttle > 0.0:
            # Accelerating
            # Reduce max acceleration at higher speeds
            speed_factor = max(0.2, 1.0 - current_speed / 50.0)
            acceleration = self.current_throttle * self.max_acceleration * speed_factor
            return acceleration
        else:
            # Coasting - natural deceleration due to friction/drag
            if current_speed > 0.1:
                # Deceleration proportional to speed (drag)
                drag_deceleration = -0.3 - 0.02 * current_speed
                return drag_deceleration
            else:
                return 0.0

    def _select_automatic_gear(self, speed: float) -> int:
        """
        Automatically select appropriate gear based on speed.

        Args:
            speed: Current speed in m/s

        Returns:
            Selected gear (1-5)
        """
        # Convert speed to km/h
        speed_kmh = speed * 3.6

        # Simple automatic transmission logic
        if speed_kmh < 0.1:
            return 1
        elif speed_kmh < 20:
            return 1
        elif speed_kmh < 40:
            return 2
        elif speed_kmh < 60:
            return 3
        elif speed_kmh < 80:
            return 4
        else:
            return 5

    def get_control_state(self) -> Dict[str, Any]:
        """
        Get current control state.

        Returns:
            Dictionary with current control values
        """
        return {
            "throttle": self.current_throttle,
            "brake": self.current_brake,
            "steering": self.current_steering,
            "gear": self.current_gear,
            "steering_angle": self.current_steering * self.max_steering_angle
        }

    def reset(self) -> None:
        """Reset control state to defaults."""
        self.current_throttle = 0.0
        self.current_brake = 0.0
        self.current_steering = 0.0
        self.current_gear = 1
        self.target_throttle = 0.0
        self.target_brake = 0.0
        self.target_steering = 0.0
        self.target_gear = 1
        self.throttle_buffer = []
        self.brake_buffer = []
        self.steering_buffer = []

    def emergency_stop(self) -> None:
        """Initiate emergency stop (full brake)."""
        self.target_throttle = 0.0
        self.target_brake = 1.0
        self.current_throttle = 0.0
        self.current_brake = 1.0

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp value to range [min_val, max_val]."""
        return max(min_val, min(max_val, value))

    def get_info(self) -> Dict[str, Any]:
        """Get control system information."""
        return {
            "max_steering_angle": self.max_steering_angle,
            "max_acceleration": self.max_acceleration,
            "max_deceleration": self.max_deceleration,
            "max_throttle_rate": self.max_throttle_rate,
            "max_brake_rate": self.max_brake_rate,
            "max_steering_rate": self.max_steering_rate,
            "wheelbase": self.wheelbase,
            "mass": self.mass,
            "auto_gear": self.auto_gear
        }

    def get_action_space_info(self) -> Dict[str, Any]:
        """
        Get information about the action space for the RL agent.

        Returns:
            Dictionary describing valid action ranges
        """
        action_space = {
            "throttle": {
                "type": "continuous",
                "range": [0.0, 1.0],
                "description": "Throttle pedal position"
            },
            "brake": {
                "type": "continuous",
                "range": [0.0, 1.0],
                "description": "Brake pedal position"
            },
            "steering": {
                "type": "continuous",
                "range": [-1.0, 1.0],
                "description": "Steering wheel position (-1=left, 1=right)"
            }
        }

        if not self.auto_gear:
            action_space["gear"] = {
                "type": "discrete",
                "range": [-1, 0, 1, 2, 3, 4, 5],
                "description": "Gear selection (-1=reverse, 0=neutral, 1-5=forward)"
            }

        return action_space
