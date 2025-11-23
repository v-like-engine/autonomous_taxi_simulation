# Sensor Simulation Module

**Agent 4 - Sensor Simulation Agent**

This module provides realistic sensor simulation for the autonomous taxi, ensuring the RL agent (Agent 5) only receives sensor data with realistic limitations and NOT the ground truth environment state.

## Overview

The sensor system implements seven key components:

1. **Camera Sensor** - Wide field of view with noisy/ambiguous data
2. **Lidar Sensor** - Accurate point cloud with limited range
3. **Sonar Sensor** - Very accurate short-range distance sensors
4. **GPS Sensor** - Position with realistic error and map integration
5. **Car Telemetry** - Internal vehicle sensors (speed, RPM, fuel, etc.)
6. **Car Control** - Control interface for the RL agent
7. **Sensor Fusion** - Unified sensor data representation

## Quick Start

```python
from sensors import SensorFusion

# Initialize sensor fusion system
fusion = SensorFusion()

# Get sensor data
fused_data = fusion.sense_all(
    car_position=(50, 50),
    car_heading=45.0,
    car_state=car_state,
    environment_state=environment_state,
    map_data=map_data,
    destination=(100, 100),
    delta_time=0.1
)

# Apply control
fusion.apply_control(throttle=0.5, steering=0.2)
fusion.update_control(delta_time=0.1, current_speed=15.0)

# Get processed state for RL agent
state_vector = fusion.get_processed_state(fused_data, "feature_vector")
```

## Individual Sensors

### Camera Sensor

**Characteristics:**
- Wide field of view (75m radius by default)
- Detects vehicles, pedestrians, obstacles, lane markers
- Position noise: ±2-5 meters
- Confidence scores that degrade with distance
- May miss small objects or confuse object types

**Usage:**
```python
from sensors import CameraSensor

camera = CameraSensor(max_range=75.0)
camera_data = camera.sense(
    car_position=(0, 0),
    car_heading=0,
    environment_state=env_state
)

print(f"Detected {len(camera_data['vehicles'])} vehicles")
```

**Output Format:**
```python
{
    "vehicles": [
        {
            "type": "vehicle",
            "position": (x, y),  # noisy
            "confidence": 0.85,
            "distance": 25.3,
            "vehicle_type": "car"
        },
        ...
    ],
    "pedestrians": [...],
    "lane_markers": [...],
    "obstacles": [...]
}
```

### Lidar Sensor

**Characteristics:**
- 40m range by default
- 360-degree scanning
- 1-degree angular resolution (361 rays)
- Accurate distance measurements (±2cm noise)
- Point cloud output

**Usage:**
```python
from sensors import LidarSensor

lidar = LidarSensor(max_range=40.0, angle_resolution=1.0)
lidar_data = lidar.sense(
    car_position=(0, 0),
    car_heading=0,
    environment_state=env_state
)

print(f"Point cloud has {len(lidar_data['points'])} points")
```

**Output Format:**
```python
{
    "points": [
        {
            "angle": 0,  # relative to car
            "absolute_angle": 45,  # absolute angle
            "distance": 15.3,
            "intensity": 0.8,
            "object_type": "vehicle"
        },
        ...
    ]
}
```

### Sonar Sensor

**Characteristics:**
- Very short range (8m default)
- 8 sensors around the car
- 30-degree cone per sensor
- Very accurate (±1cm noise)
- Only returns distance, not object type

**Usage:**
```python
from sensors import SonarSensor

sonar = SonarSensor(max_range=8.0)
sonar_data = sonar.sense(
    car_position=(0, 0),
    car_heading=0,
    environment_state=env_state
)

print(f"Front center distance: {sonar_data['sensors']['front_center']}m")
```

**Output Format:**
```python
{
    "sensors": {
        "front_left": 3.2,    # meters (None if no detection)
        "front_center": 5.8,
        "front_right": 4.1,
        "rear_left": 2.5,
        "rear_center": 7.2,
        "rear_right": 3.0,
        "side_left": 1.8,
        "side_right": 2.3
    }
}
```

### GPS Sensor

**Characteristics:**
- Position noise: ±3.5m standard deviation
- Heading noise: ±2 degrees
- Integrates with map data (roads, zones, speed limits)
- Route planning capability
- Can simulate signal loss (1% probability)

**Usage:**
```python
from sensors import GPSSensor

gps = GPSSensor(position_noise=3.5)
gps_data = gps.sense(
    car_position=(50, 50),
    car_heading=45,
    map_data=map_data,
    destination=(100, 100)
)

print(f"GPS position: {gps_data['position']}")
print(f"Speed limit: {gps_data['speed_limit']} km/h")
```

**Output Format:**
```python
{
    "position": (x, y),  # with noise
    "heading": 45.0,     # with noise
    "has_signal": True,
    "current_road": {...},
    "current_zone": {"type": "urban", "speed_limit": 60},
    "speed_limit": 60,
    "route": [(x1, y1), (x2, y2), ...],
    "destination": (100, 100),
    "distance_to_destination": 75.3
}
```

### Car Telemetry

**Characteristics:**
- Accurate internal sensors
- Tracks speed, acceleration, RPM, fuel, temperature
- Simulates fuel consumption and engine temperature
- Small measurement noise for realism

**Usage:**
```python
from sensors import CarTelemetry

telemetry = CarTelemetry()
telemetry_data = telemetry.sense(
    car_state=car_state,
    control_inputs=control_inputs,
    delta_time=0.1
)

print(f"Speed: {telemetry_data['speed']} km/h")
print(f"Fuel: {telemetry_data['fuel']}%")
```

**Output Format:**
```python
{
    "speed": 45.5,         # km/h
    "acceleration": 1.2,   # m/s²
    "rpm": 2500,
    "fuel": 65.0,          # %
    "temperature": 90.0,   # °C
    "gear": 3,
    "steering_angle": -15.0,  # degrees
    "odometer": 12345.67,      # meters
    "throttle_position": 50.0, # %
    "brake_position": 0.0      # %
}
```

### Car Control

**Characteristics:**
- Accepts control commands from RL agent
- Smooth actuation with rate limits
- Physical constraints (max steering, acceleration)
- Automatic gear selection (optional)
- Realistic response delays

**Usage:**
```python
from sensors import CarControl

control = CarControl()

# Set desired control
control.set_control(throttle=0.7, steering=0.3)

# Update with smooth transitions
control.update(delta_time=0.1, current_speed=15.0)

# Apply to physics
new_car_state = control.apply_to_physics(car_state, delta_time=0.1)
```

**Action Space:**
```python
{
    "throttle": 0.0-1.0,   # continuous
    "brake": 0.0-1.0,      # continuous
    "steering": -1.0-1.0,  # continuous (-1=left, 1=right)
    "gear": -1,0,1,2,3,4,5 # discrete (auto by default)
}
```

### Sensor Fusion

**Purpose:**
Combines all sensors into a unified interface for the RL agent.

**Key Features:**
- Single interface for all sensors
- Processes raw sensor data into state representations
- Manages control interface
- Ensures RL agent only sees sensor data (not ground truth)

**State Representations:**

1. **Feature Vector** (recommended for simple RL):
   - 23-dimensional normalized vector
   - Includes GPS, telemetry, sonar, camera counts, lidar stats
   - Ready for neural network input

2. **Dictionary** (human-readable):
   - Structured dictionary with all sensor data
   - Good for debugging and visualization

3. **Image** (for CNN-based RL):
   - Multi-channel image representation
   - Placeholder implementation (can be customized)

**Integration with RL Agent:**

```python
# Initialize
fusion = SensorFusion()

# In RL training loop
for step in range(max_steps):
    # Get observation
    sensor_data = fusion.sense_all(
        car_position, car_heading, car_state,
        environment_state, map_data, destination
    )

    # Convert to state vector
    state = fusion.get_processed_state(sensor_data, "feature_vector")

    # RL agent selects action
    action = agent.select_action(state)

    # Apply control
    fusion.apply_control(
        throttle=action[0],
        steering=action[1]
    )

    # Update physics
    fusion.update_control(delta_time, current_speed)
    new_state = fusion.apply_control_to_physics(car_state, delta_time)
```

## Design Philosophy

### Why Realistic Sensor Limitations?

The sensor system ensures the RL agent learns to work with realistic sensor data:

1. **Camera**: Wide view but noisy - forces agent to handle uncertainty
2. **Lidar**: Accurate but limited range - agent must plan ahead
3. **Sonar**: Very accurate but very short range - useful for parking/collision avoidance
4. **GPS**: Good for navigation but has positioning errors

This prevents the agent from "cheating" by accessing perfect environment state.

### Sensor Complementarity

Different sensors complement each other:
- **Camera**: Good for detecting objects and their types
- **Lidar**: Good for accurate distance measurements
- **Sonar**: Best for close-range precision
- **GPS**: Essential for navigation and route following

The RL agent must learn to fuse these different sensor modalities.

## Configuration

All sensors accept configuration parameters:

```python
fusion = SensorFusion(
    camera_config={
        "max_range": 75.0,
        "position_noise_max": 5.0
    },
    lidar_config={
        "max_range": 40.0,
        "angle_resolution": 1.0
    },
    sonar_config={
        "max_range": 8.0,
        "cone_angle": 30.0
    },
    gps_config={
        "position_noise": 3.5,
        "heading_noise": 2.0
    },
    control_config={
        "max_acceleration": 4.0,
        "max_steering_angle": 35.0
    }
)
```

## Testing

Run the test suite:

```bash
python test_sensors.py
```

This tests all sensors individually and the fusion module.

## Integration Notes

### For Agent 5 (RL Agent)

Use the `SensorFusion` class as your primary interface:
- Call `sense_all()` to get observations
- Use `get_processed_state()` to convert to feature vectors
- Call `apply_control()` to send actions
- Use `get_observation_space_info()` and `get_action_space_info()` for gym environment setup

### For Agent 2 (Traffic Simulation)

Provide environment state in this format:
```python
environment_state = {
    "vehicles": [
        {
            "position": (x, y),
            "heading": degrees,
            "vehicle_type": "car/truck",
            "length": 4.5,
            "width": 2.0
        },
        ...
    ],
    "pedestrians": [
        {
            "position": (x, y),
            "radius": 0.3
        },
        ...
    ],
    "obstacles": [...]
}
```

### For Agent 1 (Map Parser)

Provide map data in this format:
```python
map_data = {
    "zones": {
        "main_zones": [
            {
                "type": "urban/countryside/highway",
                "speed_limit": 60,
                "bounds": {...} or "polygon": [...]
            },
            ...
        ]
    },
    "roads": {
        "lanes": [
            {
                "id": 1,
                "type": "main_road/highway",
                "direction": "bidirectional/oneway",
                "center_line": [(x1, y1), (x2, y2), ...]
            },
            ...
        ]
    },
    "boundaries": [
        {"start": (x1, y1), "end": (x2, y2)},
        ...
    ]
}
```

## Implementation Status

✅ **Completed**
- Camera sensor with realistic noise
- Lidar sensor with ray-casting
- Sonar sensor with multiple sensors
- GPS sensor with map integration
- Car telemetry with physics simulation
- Car control with realistic actuation
- Sensor fusion module
- Comprehensive test suite
- Documentation

## Future Enhancements (Optional)

- Weather effects (rain, fog affecting camera/lidar)
- Time of day effects (lighting)
- Sensor failure simulation
- More advanced route planning (A* on road network)
- Kalman filtering for sensor fusion
- Object tracking across frames

## Files

- `camera.py` - Camera sensor implementation
- `lidar.py` - Lidar sensor with ray-casting
- `sonar.py` - Sonar sensor array
- `gps.py` - GPS with map integration
- `car_telemetry.py` - Internal vehicle sensors
- `car_control.py` - Control interface
- `sensor_fusion.py` - Unified sensor system
- `__init__.py` - Module exports
- `README.md` - This file

## Contact

This module was implemented by **Agent 4 (Sensor Simulation Agent)**.

For questions or issues, check the main project documentation or contact the system coordinator (Agent 6).
