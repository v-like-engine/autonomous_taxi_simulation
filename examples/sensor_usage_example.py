#!/usr/bin/env python3
"""
Example usage of the sensor system for the autonomous taxi.

This demonstrates how to use sensors in your own code.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sensors import SensorFusion


def example_basic_usage():
    """Basic sensor usage example."""
    print("=== Basic Sensor Usage ===\n")

    # Initialize sensor fusion system
    fusion = SensorFusion()

    # Print sensor information
    print("Sensor Configuration:")
    sensor_info = fusion.get_all_sensor_info()
    print(f"- Camera range: {sensor_info['camera']['max_range']}m")
    print(f"- Lidar range: {sensor_info['lidar']['max_range']}m")
    print(f"- Sonar range: {sensor_info['sonar']['max_range']}m")
    print(f"- GPS noise: ±{sensor_info['gps']['position_noise']}m")

    # Mock data
    car_position = (50, 50)
    car_heading = 45  # degrees
    car_state = {
        "position": car_position,
        "velocity": (10, 5),
        "heading": car_heading,
        "angular_velocity": 0
    }

    environment_state = {
        "vehicles": [
            {"position": (60, 55), "vehicle_type": "car", "heading": 45, "length": 4.5, "width": 2.0},
            {"position": (70, 60), "vehicle_type": "truck", "heading": 30, "length": 8.0, "width": 2.5}
        ],
        "pedestrians": [
            {"position": (55, 52), "radius": 0.3},
            {"position": (58, 48), "radius": 0.3}
        ],
        "obstacles": []
    }

    map_data = {
        "zones": {
            "main_zones": [
                {
                    "type": "urban",
                    "speed_limit": 60,
                    "id": 1,
                    "bounds": {"min_x": 0, "max_x": 200, "min_y": 0, "max_y": 200}
                }
            ]
        },
        "roads": {
            "lanes": [
                {
                    "id": 1,
                    "type": "main_road",
                    "direction": "bidirectional",
                    "center_line": [(0, 0), (100, 100), (200, 200)]
                }
            ]
        }
    }

    destination = (150, 150)

    # Get sensor data
    print("\nGetting sensor data...")
    sensor_data = fusion.sense_all(
        car_position,
        car_heading,
        car_state,
        environment_state,
        map_data,
        destination,
        delta_time=0.1
    )

    # Print sensor readings
    print(f"\nCamera detected:")
    print(f"  - {len(sensor_data['camera']['vehicles'])} vehicles")
    print(f"  - {len(sensor_data['camera']['pedestrians'])} pedestrians")

    print(f"\nLidar point cloud:")
    print(f"  - {len(sensor_data['lidar']['points'])} points")

    print(f"\nSonar readings:")
    for sensor_name, distance in sensor_data['sonar']['sensors'].items():
        if distance is not None:
            print(f"  - {sensor_name}: {distance:.2f}m")

    print(f"\nGPS data:")
    print(f"  - Position: ({sensor_data['gps']['position'][0]:.1f}, {sensor_data['gps']['position'][1]:.1f})")
    print(f"  - Heading: {sensor_data['gps']['heading']:.1f}°")
    print(f"  - Speed limit: {sensor_data['gps']['speed_limit']} km/h")
    print(f"  - Distance to destination: {sensor_data['gps']['distance_to_destination']:.1f}m")

    print(f"\nTelemetry:")
    print(f"  - Speed: {sensor_data['telemetry']['speed']:.1f} km/h")
    print(f"  - RPM: {sensor_data['telemetry']['rpm']}")
    print(f"  - Fuel: {sensor_data['telemetry']['fuel']}%")
    print(f"  - Gear: {sensor_data['telemetry']['gear']}")


def example_rl_integration():
    """Example of how to integrate with RL agent."""
    print("\n\n=== RL Integration Example ===\n")

    # Initialize
    fusion = SensorFusion()

    # Get observation and action space info
    obs_space = fusion.get_observation_space_info()
    action_space = fusion.control.get_action_space_info()

    print(f"Observation space: {obs_space['dimension']}-dimensional vector")
    print(f"Action space: {list(action_space.keys())}")

    # Simulate one step of RL interaction
    print("\nSimulating one RL step...")

    # Mock data (same as above)
    car_state = {
        "position": (50, 50),
        "velocity": (10, 5),
        "heading": 45,
        "angular_velocity": 0
    }

    environment_state = {
        "vehicles": [{"position": (60, 55), "vehicle_type": "car", "heading": 45, "length": 4.5, "width": 2.0}],
        "pedestrians": [{"position": (55, 52), "radius": 0.3}],
        "obstacles": []
    }

    map_data = {
        "zones": {"main_zones": [{"type": "urban", "speed_limit": 60, "id": 1, "bounds": {"min_x": 0, "max_x": 200, "min_y": 0, "max_y": 200}}]},
        "roads": {"lanes": [{"id": 1, "type": "main_road", "direction": "bidirectional", "center_line": [(0, 0), (100, 100)]}]}
    }

    # 1. Get observation
    sensor_data = fusion.sense_all(
        (50, 50), 45, car_state, environment_state, map_data, (100, 100), delta_time=0.1
    )

    # 2. Convert to state vector
    state_vector = fusion.get_processed_state(sensor_data, "feature_vector")
    print(f"State vector shape: {state_vector.shape}")
    print(f"State vector (sample): {state_vector[:5]}")

    # 3. RL agent would select action here
    # For demo, we'll use a simple action
    action = {
        "throttle": 0.6,
        "brake": 0.0,
        "steering": 0.1
    }
    print(f"\nRL agent selected action: {action}")

    # 4. Apply control
    fusion.apply_control(
        throttle=action["throttle"],
        brake=action["brake"],
        steering=action["steering"]
    )

    # 5. Update control system
    current_speed = 15.0  # m/s
    control_state = fusion.update_control(delta_time=0.1, current_speed=current_speed)
    print(f"Control state after update: {control_state}")

    # 6. Apply to physics
    new_car_state = fusion.apply_control_to_physics(car_state, delta_time=0.1)
    print(f"\nNew car state:")
    print(f"  - Position: ({new_car_state['position'][0]:.2f}, {new_car_state['position'][1]:.2f})")
    print(f"  - Velocity: ({new_car_state['velocity'][0]:.2f}, {new_car_state['velocity'][1]:.2f})")
    print(f"  - Heading: {new_car_state['heading']:.2f}°")


def example_custom_configuration():
    """Example of custom sensor configuration."""
    print("\n\n=== Custom Sensor Configuration ===\n")

    # Create fusion with custom configuration
    fusion = SensorFusion(
        camera_config={
            "max_range": 100.0,  # Longer range camera
            "position_noise_max": 3.0  # Less noise
        },
        lidar_config={
            "max_range": 50.0,  # Longer range lidar
            "angle_resolution": 2.0  # Lower resolution for performance
        },
        sonar_config={
            "max_range": 10.0,  # Longer range sonar
            "cone_angle": 40.0  # Wider cone
        },
        gps_config={
            "position_noise": 2.0,  # More accurate GPS
            "heading_noise": 1.0
        },
        control_config={
            "max_acceleration": 5.0,  # More powerful car
            "max_steering_angle": 40.0,  # Can turn tighter
            "auto_gear": True  # Automatic transmission
        }
    )

    print("Custom sensor configuration created:")
    info = fusion.get_all_sensor_info()
    print(f"  - Camera range: {info['camera']['max_range']}m")
    print(f"  - Lidar range: {info['lidar']['max_range']}m")
    print(f"  - Sonar range: {info['sonar']['max_range']}m")
    print(f"  - GPS noise: ±{info['gps']['position_noise']}m")
    print(f"  - Max acceleration: {info['control']['max_acceleration']} m/s²")
    print(f"  - Max steering: {info['control']['max_steering_angle']}°")


def example_sensor_data_processing():
    """Example of different state representations."""
    print("\n\n=== Sensor Data Processing ===\n")

    fusion = SensorFusion()

    # Get mock sensor data
    car_state = {
        "position": (50, 50),
        "velocity": (10, 5),
        "heading": 45,
        "angular_velocity": 0
    }

    environment_state = {
        "vehicles": [{"position": (60, 55), "vehicle_type": "car", "heading": 45, "length": 4.5, "width": 2.0}],
        "pedestrians": [{"position": (55, 52), "radius": 0.3}],
        "obstacles": []
    }

    map_data = {
        "zones": {"main_zones": [{"type": "urban", "speed_limit": 60, "id": 1, "bounds": {"min_x": 0, "max_x": 200, "min_y": 0, "max_y": 200}}]},
        "roads": {"lanes": [{"id": 1, "type": "main_road", "direction": "bidirectional", "center_line": [(0, 0), (100, 100)]}]}
    }

    sensor_data = fusion.sense_all(
        (50, 50), 45, car_state, environment_state, map_data, (100, 100), delta_time=0.1
    )

    # 1. Feature vector representation (for simple neural networks)
    feature_vector = fusion.get_processed_state(sensor_data, "feature_vector")
    print("Feature Vector Representation:")
    print(f"  Shape: {feature_vector.shape}")
    print(f"  Data type: {feature_vector.dtype}")
    print(f"  Values: {feature_vector}")

    # 2. Dictionary representation (for debugging/visualization)
    feature_dict = fusion.get_processed_state(sensor_data, "dict")
    print("\nDictionary Representation:")
    for key, value in feature_dict.items():
        print(f"  {key}: {value}")

    # 3. Image representation (for CNNs) - placeholder
    # image_rep = fusion.get_processed_state(sensor_data, "image")
    # print(f"\nImage Representation: {image_rep.shape}")


def main():
    """Run all examples."""
    print("=" * 70)
    print("SENSOR SYSTEM USAGE EXAMPLES")
    print("=" * 70)

    example_basic_usage()
    example_rl_integration()
    example_custom_configuration()
    example_sensor_data_processing()

    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
