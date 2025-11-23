# Sensor Simulation Documentation

Documentation for the Sensor Simulation module (Agent 4).

## Overview

The Sensor Simulation module provides realistic sensors with appropriate limitations and noise. The RL agent must rely on these sensors and cannot access the complete world state.

## Design Philosophy

**Key Principle**: Realistic Limitations

The RL agent should NOT have perfect information. Sensors provide:
- **Camera**: Wide FOV but ambiguous/inaccurate
- **Lidar**: Accurate but limited range/angle
- **Sonar**: Very accurate but very short range
- **GPS**: Knows map/route but not other entities

## Sensors

### Lidar Sensor

**Characteristics:**
- Range: 30-50 meters
- Angle: 360 degrees (configurable)
- Resolution: 1-degree intervals
- Accuracy: ±0.1 meter

**Implementation:**
- Ray-casting algorithm
- Returns point cloud data
- Detects vehicles, pedestrians, boundaries
- Cannot see through objects (occlusion)

**Output Format:**
```python
{
    "points": [
        {
            "angle": 0,      # degrees
            "distance": 15.3,  # meters
            "intensity": 0.8   # reflection intensity
        },
        ...  # 360 points for full scan
    ]
}
```

**Usage:**
```python
from src.sensors.lidar import Lidar

lidar = Lidar(range=40, resolution=1)
data = lidar.scan(car_position, world_state)
```

### Camera Sensor

**Characteristics:**
- Field of View: 50-100 meter radius
- Output: Detected objects with noise
- Position noise: ±2-5 meters
- May miss objects or false positives

**Detected Objects:**
- Vehicles (type, approximate position)
- Pedestrians (approximate position)
- Lane markers
- Road boundaries

**Output Format:**
```python
{
    "vehicles": [
        {
            "type": "car",
            "position": [x, y],  # with noise
            "confidence": 0.85
        }
    ],
    "pedestrians": [
        {
            "position": [x, y],  # with noise
            "confidence": 0.72
        }
    ],
    "lane_markers": [...],
    "obstacles": [...]
}
```

**Usage:**
```python
from src.sensors.camera import Camera

camera = Camera(fov_radius=75)
data = camera.capture(car_position, world_state)
```

### Sonar Sensor

**Characteristics:**
- Range: 5-10 meters
- Accuracy: ±0.05 meters
- Multiple sensors: Front, rear, sides
- Cone angle: ~30 degrees each
- Returns nearest object only

**Sensor Positions:**
- front_left, front_center, front_right
- rear_left, rear_center, rear_right
- side_left, side_right

**Output Format:**
```python
{
    "front_left": 3.2,    # meters to nearest obstacle
    "front_center": 5.8,
    "front_right": 4.1,
    "rear_left": 2.5,
    "rear_center": 7.2,
    "rear_right": 3.0,
    "side_left": 1.8,
    "side_right": 2.3
}
```

**Usage:**
```python
from src.sensors.sonar import Sonar

sonar = Sonar(range=8)
data = sonar.measure(car_position, car_heading, world_state)
```

### GPS Sensor

**Characteristics:**
- Position accuracy: ±2-5 meters
- Provides map information
- Provides route to destination
- NO information about other vehicles/pedestrians

**Output Format:**
```python
{
    "position": [x, y],  # with noise
    "heading": 45.0,     # degrees
    "current_road": {
        "id": "road_12",
        "lane": 2,
        "direction": "forward"
    },
    "current_zone": "urban",
    "speed_limit": 60,  # km/h
    "route": [
        [x1, y1],
        [x2, y2],
        ...
    ]
}
```

**Usage:**
```python
from src.sensors.gps import GPS

gps = GPS(map_data, noise_std=3.0)
data = gps.locate(car_position, destination)
```

### Car Telemetry

**Internal Sensors:**
- Speed (km/h)
- Acceleration (m/s²)
- RPM (engine)
- Fuel level (%)
- Temperature (°C)
- Steering angle (degrees)

**Output Format:**
```python
{
    "speed": 45.5,
    "acceleration": 1.2,
    "rpm": 2500,
    "fuel": 65.0,
    "temperature": 90.0,
    "gear": 3,
    "steering_angle": -15.0
}
```

**Usage:**
```python
from src.sensors.car_telemetry import CarTelemetry

telemetry = CarTelemetry()
data = telemetry.read(car_state)
```

## Sensor Fusion

Combines all sensor data into unified representation.

**Purpose:**
- Provide single data structure to RL agent
- Timestamp synchronization
- Handle missing/failed sensors

**Output Format:**
```python
{
    "lidar": {...},
    "camera": {...},
    "sonar": {...},
    "gps": {...},
    "telemetry": {...},
    "timestamp": 1234567890.123
}
```

**Usage:**
```python
from src.sensors.sensor_fusion import SensorFusion

fusion = SensorFusion()
lidar_data = lidar.scan(...)
camera_data = camera.capture(...)
# ... other sensors

fused = fusion.fuse(
    lidar=lidar_data,
    camera=camera_data,
    sonar=sonar_data,
    gps=gps_data,
    telemetry=telemetry_data
)
```

## Car Control Interface

Provides interface for RL agent to control the car.

**Control Actions:**
```python
{
    "throttle": 0.7,      # 0.0-1.0
    "brake": 0.0,         # 0.0-1.0
    "steering": -0.15,    # -1.0 to 1.0
    "gear": 3             # -1=reverse, 0=neutral, 1-5=gears
}
```

**Constraints:**
- Smooth actuation (no instant changes)
- Physical limits enforced
- Realistic response times
- Only controls main car

**Usage:**
```python
from src.sensors.car_control import CarControl

control = CarControl()
control.execute({
    "throttle": 0.7,
    "brake": 0.0,
    "steering": -0.15,
    "gear": 3
})
```

## Noise Models

### Position Noise (GPS, Camera)

Gaussian noise with configurable standard deviation:
```python
noisy_position = true_position + N(0, σ²)
# σ = 3.0 for GPS, 4.0 for camera
```

### Detection Confidence (Camera)

Distance-based confidence:
```python
confidence = max(0, 1 - distance / max_distance)
confidence *= random(0.8, 1.0)  # Add randomness
```

### Occlusion (Lidar)

Ray-casting stops at first obstacle:
```python
for each ray:
    cast ray from car position
    find first intersection with any object
    return distance to intersection
```

## Configuration

```yaml
# config/sensors.yaml
lidar:
  range: 40.0  # meters
  resolution: 1.0  # degrees
  noise_std: 0.1

camera:
  fov_radius: 75.0
  position_noise_std: 4.0
  min_confidence: 0.5

sonar:
  range: 8.0
  cone_angle: 30.0
  noise_std: 0.05

gps:
  position_noise_std: 3.0
  update_rate: 10  # Hz

telemetry:
  update_rate: 60  # Hz
  speed_noise_std: 0.5
```

## Visualization

Sensors can provide visualization data for the frontend:

```python
def get_visualization_data(self):
    return {
        "lidar_rays": [...],
        "camera_fov": circle,
        "camera_detections": boxes,
        "sonar_cones": arcs,
        "gps_route": line
    }
```

## API Reference

See [API Documentation](api.md#sensor-api).
