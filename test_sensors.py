#!/usr/bin/env python3
"""
Test script for sensor implementations.

Tests all sensors individually and the sensor fusion module.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sensors import (
    CameraSensor,
    LidarSensor,
    SonarSensor,
    GPSSensor,
    CarTelemetry,
    CarControl,
    SensorFusion
)


def test_camera_sensor():
    """Test camera sensor."""
    print("\n=== Testing Camera Sensor ===")

    camera = CameraSensor(max_range=75.0)
    print(f"Camera info: {camera.get_sensor_info()}")

    # Create mock environment
    environment_state = {
        "vehicles": [
            {"position": (10, 5), "vehicle_type": "car", "heading": 0, "length": 4.5, "width": 2.0},
            {"position": (50, 20), "vehicle_type": "truck", "heading": 90, "length": 8.0, "width": 2.5}
        ],
        "pedestrians": [
            {"position": (15, 10), "radius": 0.3},
            {"position": (25, 15), "radius": 0.3}
        ],
        "obstacles": [
            {"position": (30, 5), "radius": 0.5}
        ]
    }

    car_position = (0, 0)
    car_heading = 0

    # Test sensing
    camera_data = camera.sense(car_position, car_heading, environment_state)

    print(f"Detected {len(camera_data['vehicles'])} vehicles")
    print(f"Detected {len(camera_data['pedestrians'])} pedestrians")
    print(f"Detected {len(camera_data['obstacles'])} obstacles")

    if len(camera_data['vehicles']) > 0:
        print(f"First vehicle: {camera_data['vehicles'][0]}")

    print("✓ Camera sensor test passed")


def test_lidar_sensor():
    """Test lidar sensor."""
    print("\n=== Testing Lidar Sensor ===")

    lidar = LidarSensor(max_range=40.0, angle_resolution=5.0)  # 5 degrees for faster test
    print(f"Lidar info: {lidar.get_sensor_info()}")

    # Create mock environment
    environment_state = {
        "vehicles": [
            {"position": (10, 0), "vehicle_type": "car", "heading": 0, "length": 4.5, "width": 2.0}
        ],
        "pedestrians": [
            {"position": (5, 5), "radius": 0.3}
        ]
    }

    car_position = (0, 0)
    car_heading = 0

    # Test sensing
    lidar_data = lidar.sense(car_position, car_heading, environment_state)

    print(f"Point cloud has {len(lidar_data['points'])} points")
    if len(lidar_data['points']) > 0:
        print(f"First point: {lidar_data['points'][0]}")
        print(f"Sample points: {lidar_data['points'][:5]}")

    print("✓ Lidar sensor test passed")


def test_sonar_sensor():
    """Test sonar sensor."""
    print("\n=== Testing Sonar Sensor ===")

    sonar = SonarSensor(max_range=8.0)
    print(f"Sonar info: {sonar.get_sensor_info()}")

    # Create mock environment
    environment_state = {
        "vehicles": [
            {"position": (5, 0), "vehicle_type": "car", "heading": 0, "length": 4.5, "width": 2.0}
        ],
        "pedestrians": [
            {"position": (2, 1), "radius": 0.3}
        ]
    }

    car_position = (0, 0)
    car_heading = 0

    # Test sensing
    sonar_data = sonar.sense(car_position, car_heading, environment_state)

    print(f"Sonar readings: {sonar_data['sensors']}")

    print("✓ Sonar sensor test passed")


def test_gps_sensor():
    """Test GPS sensor."""
    print("\n=== Testing GPS Sensor ===")

    gps = GPSSensor(position_noise=3.5)
    print(f"GPS info: {gps.get_sensor_info()}")

    # Create mock map data
    map_data = {
        "zones": {
            "main_zones": [
                {
                    "type": "urban",
                    "speed_limit": 60,
                    "id": 1,
                    "bounds": {"min_x": -100, "max_x": 100, "min_y": -100, "max_y": 100}
                }
            ]
        },
        "roads": {
            "lanes": [
                {
                    "id": 1,
                    "type": "main_road",
                    "direction": "bidirectional",
                    "center_line": [(0, 0), (100, 0), (100, 100)]
                }
            ]
        }
    }

    car_position = (10, 5)
    car_heading = 45
    destination = (100, 100)

    # Test sensing
    gps_data = gps.sense(car_position, car_heading, map_data, destination)

    print(f"GPS position (noisy): {gps_data['position']}")
    print(f"GPS heading (noisy): {gps_data['heading']}")
    print(f"Has signal: {gps_data['has_signal']}")
    print(f"Current road: {gps_data.get('current_road')}")
    print(f"Speed limit: {gps_data.get('speed_limit')}")

    print("✓ GPS sensor test passed")


def test_car_telemetry():
    """Test car telemetry."""
    print("\n=== Testing Car Telemetry ===")

    telemetry = CarTelemetry()
    print(f"Telemetry info: {telemetry.get_sensor_info()}")

    # Create mock car state
    car_state = {
        "velocity": (10, 5),  # m/s
        "heading": 30,
        "position": (50, 50)
    }

    control_inputs = {
        "throttle": 0.5,
        "brake": 0.0,
        "steering": 0.2,
        "gear": 3
    }

    # Test sensing
    telemetry_data = telemetry.sense(car_state, control_inputs, delta_time=0.1)

    print(f"Speed: {telemetry_data['speed']} km/h")
    print(f"RPM: {telemetry_data['rpm']}")
    print(f"Fuel: {telemetry_data['fuel']}%")
    print(f"Temperature: {telemetry_data['temperature']}°C")
    print(f"Gear: {telemetry_data['gear']}")
    print(f"Steering angle: {telemetry_data['steering_angle']}°")

    print("✓ Car telemetry test passed")


def test_car_control():
    """Test car control interface."""
    print("\n=== Testing Car Control ===")

    control = CarControl()
    print(f"Control info: {control.get_info()}")
    print(f"Action space: {control.get_action_space_info()}")

    # Test setting controls
    control.set_control(throttle=0.7, brake=0.0, steering=0.3)

    # Test update with smooth transitions
    control.update(delta_time=0.1, current_speed=10.0)

    state = control.get_control_state()
    print(f"Control state: {state}")

    # Test physics application
    car_state = {
        "position": (0, 0),
        "velocity": (10, 0),
        "heading": 0,
        "angular_velocity": 0
    }

    new_state = control.apply_to_physics(car_state, delta_time=0.1)
    print(f"New position: {new_state['position']}")
    print(f"New velocity: {new_state['velocity']}")
    print(f"New heading: {new_state['heading']}")

    print("✓ Car control test passed")


def test_sensor_fusion():
    """Test sensor fusion module."""
    print("\n=== Testing Sensor Fusion ===")

    fusion = SensorFusion()
    print(f"Sensor fusion info: {fusion.get_all_sensor_info()}")
    print(f"Observation space: {fusion.get_observation_space_info()}")

    # Create mock data
    car_position = (50, 50)
    car_heading = 45
    car_state = {
        "position": car_position,
        "velocity": (10, 5),
        "heading": car_heading,
        "angular_velocity": 0
    }

    environment_state = {
        "vehicles": [
            {"position": (60, 55), "vehicle_type": "car", "heading": 45, "length": 4.5, "width": 2.0}
        ],
        "pedestrians": [
            {"position": (55, 52), "radius": 0.3}
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
                    "center_line": [(0, 0), (100, 100)]
                }
            ]
        }
    }

    destination = (100, 100)

    # Test full sensor fusion
    fused_data = fusion.sense_all(
        car_position,
        car_heading,
        car_state,
        environment_state,
        map_data,
        destination,
        delta_time=0.1
    )

    print(f"Fused data keys: {fused_data.keys()}")
    print(f"Camera detections: {len(fused_data['camera']['vehicles'])} vehicles")
    print(f"Lidar points: {len(fused_data['lidar']['points'])} points")
    print(f"GPS position: {fused_data['gps']['position']}")
    print(f"Telemetry speed: {fused_data['telemetry']['speed']} km/h")

    # Test feature vector creation
    feature_vector = fusion.get_processed_state(fused_data, "feature_vector")
    print(f"Feature vector shape: {feature_vector.shape}")
    print(f"Feature vector (first 10): {feature_vector[:10]}")

    # Test control application
    fusion.apply_control(throttle=0.5, steering=0.2)
    fusion.update_control(delta_time=0.1, current_speed=15.0)

    print("✓ Sensor fusion test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("SENSOR IMPLEMENTATION TESTS")
    print("=" * 60)

    try:
        test_camera_sensor()
        test_lidar_sensor()
        test_sonar_sensor()
        test_gps_sensor()
        test_car_telemetry()
        test_car_control()
        test_sensor_fusion()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
