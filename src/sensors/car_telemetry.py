"""
Car telemetry sensor simulation for autonomous taxi.

Internal sensors that monitor the car's state:
- Speed, acceleration
- Engine RPM, fuel level, temperature
- Gear, steering angle
"""

import numpy as np
import math
from typing import Dict, Any, Optional


class CarTelemetry:
    """
    Simulates internal car sensors that monitor vehicle state.

    Provides accurate readings of speed, acceleration, engine parameters,
    and control positions.
    """

    def __init__(
        self,
        speed_noise: float = 0.5,  # km/h
        acceleration_noise: float = 0.05,  # m/s²
        rpm_noise: float = 50,  # RPM
        fuel_consumption_rate: float = 0.001,  # % per meter at full throttle
        engine_temp_nominal: float = 90.0,  # °C
        max_rpm: int = 6000,
        idle_rpm: int = 800
    ):
        """
        Initialize car telemetry system.

        Args:
            speed_noise: Noise in speed measurement (km/h)
            acceleration_noise: Noise in acceleration measurement (m/s²)
            rpm_noise: Noise in RPM measurement
            fuel_consumption_rate: Fuel consumption rate (% per meter)
            engine_temp_nominal: Normal engine temperature
            max_rpm: Maximum engine RPM
            idle_rpm: Idle engine RPM
        """
        self.speed_noise = speed_noise
        self.acceleration_noise = acceleration_noise
        self.rpm_noise = rpm_noise
        self.fuel_consumption_rate = fuel_consumption_rate
        self.engine_temp_nominal = engine_temp_nominal
        self.max_rpm = max_rpm
        self.idle_rpm = idle_rpm

        # Internal state
        self.fuel_level = 100.0  # percentage
        self.engine_temperature = 20.0  # starts cold
        self.odometer = 0.0  # total distance traveled
        self.previous_speed = 0.0
        self.previous_time = 0.0

    def sense(
        self,
        car_state: Dict[str, Any],
        control_inputs: Optional[Dict[str, Any]] = None,
        delta_time: float = 0.1
    ) -> Dict[str, Any]:
        """
        Get telemetry data from the car's internal sensors.

        Args:
            car_state: Current state of the car (position, velocity, etc.)
            control_inputs: Current control inputs (throttle, brake, steering, gear)
            delta_time: Time since last update in seconds

        Returns:
            Dictionary with telemetry data
        """
        # Extract car state
        velocity = car_state.get("velocity", (0.0, 0.0))
        speed_ms = math.sqrt(velocity[0]**2 + velocity[1]**2)  # m/s
        speed_kmh = speed_ms * 3.6  # km/h

        heading = car_state.get("heading", 0.0)
        position = car_state.get("position", (0.0, 0.0))

        # Get control inputs
        if control_inputs is None:
            control_inputs = {}

        throttle = control_inputs.get("throttle", 0.0)
        brake = control_inputs.get("brake", 0.0)
        steering = control_inputs.get("steering", 0.0)
        gear = control_inputs.get("gear", 1)

        # Calculate acceleration
        if delta_time > 0:
            acceleration_ms2 = (speed_ms - self.previous_speed) / delta_time
        else:
            acceleration_ms2 = 0.0

        self.previous_speed = speed_ms

        # Calculate RPM based on speed and gear
        rpm = self._calculate_rpm(speed_kmh, gear, throttle)

        # Update fuel level
        distance_traveled = speed_ms * delta_time
        self._update_fuel(throttle, distance_traveled)

        # Update engine temperature
        self._update_temperature(throttle, delta_time)

        # Update odometer
        self.odometer += distance_traveled

        # Calculate steering angle (convert from -1 to 1 to degrees)
        max_steering_angle = 35.0  # degrees
        steering_angle = steering * max_steering_angle

        # Add noise to measurements
        noisy_speed = speed_kmh + np.random.normal(0, self.speed_noise)
        noisy_acceleration = acceleration_ms2 + np.random.normal(0, self.acceleration_noise)
        noisy_rpm = rpm + np.random.normal(0, self.rpm_noise)

        # Ensure values are within reasonable bounds
        noisy_speed = max(0, noisy_speed)
        noisy_rpm = max(0, min(self.max_rpm, noisy_rpm))

        return {
            "speed": noisy_speed,  # km/h
            "acceleration": noisy_acceleration,  # m/s²
            "rpm": int(noisy_rpm),
            "fuel": round(self.fuel_level, 1),  # %
            "temperature": round(self.engine_temperature, 1),  # °C
            "gear": gear,
            "steering_angle": round(steering_angle, 1),  # degrees
            "odometer": round(self.odometer, 2),  # meters
            "throttle_position": round(throttle * 100, 1),  # %
            "brake_position": round(brake * 100, 1),  # %
            "sensor_type": "telemetry"
        }

    def _calculate_rpm(self, speed_kmh: float, gear: int, throttle: float) -> float:
        """
        Calculate engine RPM based on speed, gear, and throttle.

        Args:
            speed_kmh: Current speed in km/h
            gear: Current gear (-1 to 5)
            throttle: Throttle position (0-1)

        Returns:
            Engine RPM
        """
        if gear == 0:  # Neutral
            # RPM depends only on throttle
            return self.idle_rpm + throttle * (self.max_rpm - self.idle_rpm) * 0.5

        if gear == -1:  # Reverse
            # Similar to first gear but for reverse
            gear_ratio = 15.0
        else:
            # Forward gears (1-5)
            # Higher gear = lower RPM at same speed
            gear_ratios = {1: 15.0, 2: 10.0, 3: 7.0, 4: 5.0, 5: 3.5}
            gear_ratio = gear_ratios.get(gear, 10.0)

        # Base RPM from speed and gear ratio
        speed_ms = speed_kmh / 3.6
        base_rpm = self.idle_rpm + abs(speed_ms) * gear_ratio * 30

        # Add throttle influence (throttle can increase RPM)
        throttle_rpm = throttle * 1500

        rpm = base_rpm + throttle_rpm

        # Clamp to valid range
        return max(self.idle_rpm, min(self.max_rpm, rpm))

    def _update_fuel(self, throttle: float, distance: float) -> None:
        """
        Update fuel level based on consumption.

        Args:
            throttle: Current throttle position (0-1)
            distance: Distance traveled in this timestep (meters)
        """
        # Fuel consumption depends on throttle and distance
        consumption = self.fuel_consumption_rate * distance * (0.3 + 0.7 * throttle)
        self.fuel_level = max(0.0, self.fuel_level - consumption)

    def _update_temperature(self, throttle: float, delta_time: float) -> None:
        """
        Update engine temperature based on load.

        Args:
            throttle: Current throttle position (0-1)
            delta_time: Time elapsed in seconds
        """
        # Target temperature increases with throttle
        target_temp = self.engine_temp_nominal + throttle * 15.0

        # Temperature gradually approaches target
        temp_change_rate = 0.5  # degrees per second
        temp_diff = target_temp - self.engine_temperature

        if abs(temp_diff) > 0.1:
            # Move towards target temperature
            change = np.sign(temp_diff) * temp_change_rate * delta_time
            if abs(change) > abs(temp_diff):
                change = temp_diff
            self.engine_temperature += change

        # Clamp temperature to reasonable range
        self.engine_temperature = max(20.0, min(130.0, self.engine_temperature))

    def reset(
        self,
        fuel_level: float = 100.0,
        engine_temperature: float = 90.0,
        odometer: float = 0.0
    ) -> None:
        """
        Reset telemetry state (useful for starting new episodes).

        Args:
            fuel_level: Initial fuel level (%)
            engine_temperature: Initial engine temperature (°C)
            odometer: Initial odometer reading (meters)
        """
        self.fuel_level = fuel_level
        self.engine_temperature = engine_temperature
        self.odometer = odometer
        self.previous_speed = 0.0

    def refuel(self, amount: float = 100.0) -> None:
        """
        Refuel the car.

        Args:
            amount: Amount to add (% or liters)
        """
        self.fuel_level = min(100.0, self.fuel_level + amount)

    def get_warning_flags(self) -> Dict[str, bool]:
        """
        Get warning flags for various conditions.

        Returns:
            Dictionary of warning flags
        """
        return {
            "low_fuel": self.fuel_level < 10.0,
            "engine_overheat": self.engine_temperature > 110.0,
            "engine_cold": self.engine_temperature < 60.0,
            "high_rpm": self.previous_speed > 0 and self.fuel_level < 5.0
        }

    def get_sensor_info(self) -> Dict[str, Any]:
        """Get information about the telemetry system."""
        return {
            "type": "telemetry",
            "speed_noise": self.speed_noise,
            "acceleration_noise": self.acceleration_noise,
            "rpm_range": (self.idle_rpm, self.max_rpm),
            "fuel_capacity": 100.0,  # percentage
            "temperature_range": (20.0, 130.0)
        }
