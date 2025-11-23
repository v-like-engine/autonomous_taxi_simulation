# Agent 4: Sensor Simulation Agent

## Responsibility
You are responsible for simulating realistic sensors (lidar, camera, sonar, GPS) and the car control interface for the self-driving car.

## Your Files (DO NOT modify files outside this list)
- `src/sensors/lidar.py` - Lidar sensor simulation
- `src/sensors/camera.py` - Camera sensor simulation
- `src/sensors/sonar.py` - Sonar sensor simulation
- `src/sensors/gps.py` - GPS sensor simulation
- `src/sensors/car_telemetry.py` - Car internal sensors (speed, RPM, fuel, temp)
- `src/sensors/sensor_fusion.py` - Combine sensor data
- `src/sensors/car_control.py` - Car control interface
- `src/sensors/__init__.py` - Module exports

## Requirements

### Sensor Philosophy
**IMPORTANT**: The RL agent (Agent 5) should NOT have access to the complete map state. It must rely on sensors with realistic limitations:
- **Camera**: Wide field of view but ambiguous/inaccurate
- **Lidar**: Accurate but limited range and angle
- **Sonar**: Very accurate for close objects but very short range
- **GPS**: Knows road network and zones but not other vehicles/pedestrians

### Camera Sensor
**Characteristics:**
- **Field of View**: Large circular area around car (e.g., 50-100 meters radius)
- **Output**: Ambiguous/inaccurate information about environment
- **What it detects**:
  - Approximate positions of other vehicles (with noise)
  - Approximate positions of pedestrians (with noise)
  - Road boundaries and lane markings (more accurate)
  - Traffic signs and signals
  - Obstacles

**Limitations:**
- Position noise: ±2-5 meters
- Cannot determine exact speed of other vehicles
- May miss small objects
- May confuse pedestrians with objects
- Accuracy degrades with distance
- Weather/lighting not simulated but could add noise

**Output Format:**
```python
{
    "vehicles": [{"type": "car/truck", "position": [x, y], "confidence": 0.0-1.0}, ...],
    "pedestrians": [{"position": [x, y], "confidence": 0.0-1.0}, ...],
    "lane_markers": [...],
    "obstacles": [...]
}
```

### Lidar Sensor
**Characteristics:**
- **Range**: 30-50 meters
- **Angle**: 360 degrees (or configurable, e.g., 270 degrees front)
- **Resolution**: Ray-casting at regular angle intervals (e.g., every 1 degree)
- **Output**: Accurate distance measurements to obstacles
- **What it detects**:
  - Precise distance to vehicles
  - Precise distance to pedestrians
  - Precise distance to walls/boundaries
  - Road edges

**Limitations:**
- Limited range (objects beyond range are invisible)
- Point cloud data (requires processing to identify objects)
- Cannot see through objects (occlusion)

**Output Format:**
```python
{
    "points": [
        {"angle": 0, "distance": 15.3, "intensity": 0.8},
        {"angle": 1, "distance": 15.5, "intensity": 0.7},
        ...
    ]
}
```

### Sonar Sensor
**Characteristics:**
- **Range**: Very short (5-10 meters)
- **Angle**: Narrow cones (e.g., 30 degrees per sensor)
- **Sensors**: Multiple sensors around car (front, rear, sides)
- **Output**: Very accurate distance to nearest obstacle in each direction
- **What it detects**:
  - Precise distance to nearby vehicles (for parking, collision avoidance)
  - Precise distance to curbs and walls
  - Nearby pedestrians

**Limitations:**
- Very limited range
- Only nearest object in each cone
- Cannot identify what the object is (just distance)

**Output Format:**
```python
{
    "front_left": 3.2,    # meters
    "front_center": 5.8,
    "front_right": 4.1,
    "rear_left": 2.5,
    "rear_center": 7.2,
    "rear_right": 3.0,
    "side_left": 1.8,
    "side_right": 2.3
}
```

### GPS Sensor
**Characteristics:**
- **Accuracy**: ±2-5 meters (realistic GPS error)
- **Output**: Current position, heading, and map information
- **What it provides**:
  - Current position (with noise)
  - Current heading/orientation
  - Road network information (from Agent 1)
  - Current zone information
  - Speed limit information
  - Route to destination

**Limitations:**
- Position noise
- No information about other vehicles or pedestrians
- May lose signal in some areas (can simulate)

**Output Format:**
```python
{
    "position": [x, y],  # with ±2-5m noise
    "heading": 45.0,     # degrees
    "current_road": {...},
    "current_zone": "urban",
    "speed_limit": 60,
    "route": [...]       # path to destination
}
```

### Car Telemetry
**Internal Sensors:**
- **Speed**: Current speed (km/h)
- **Acceleration**: Current acceleration (m/s²)
- **RPM**: Engine RPM (if simulating engine)
- **Fuel**: Fuel level (% or liters)
- **Temperature**: Engine temperature
- **Gear**: Current gear (if simulating transmission)
- **Steering Angle**: Current wheel angle

**Output Format:**
```python
{
    "speed": 45.5,         # km/h
    "acceleration": 1.2,   # m/s²
    "rpm": 2500,
    "fuel": 65.0,          # %
    "temperature": 90.0,   # °C
    "gear": 3,
    "steering_angle": -15.0  # degrees, negative = left
}
```

### Car Control Interface
Provide interface for Agent 5 (RL agent) to control the car:

**Control Actions:**
```python
{
    "throttle": 0.0-1.0,      # 0 = no gas, 1 = full throttle
    "brake": 0.0-1.0,         # 0 = no brake, 1 = full brake
    "steering": -1.0-1.0,     # -1 = full left, 0 = straight, 1 = full right
    "gear": -1, 0, 1, 2, 3, 4, 5  # -1 = reverse, 0 = neutral, 1-5 = gears
}
```

**Control Characteristics:**
- Smooth actuation (no instant changes)
- Physical limits (max steering angle, max acceleration)
- Realistic response times
- Cannot control other vehicles (only the main car)

### Sensor Fusion
Combine all sensor data into a unified representation for the RL agent:
```python
{
    "camera": {...},
    "lidar": {...},
    "sonar": {...},
    "gps": {...},
    "telemetry": {...},
    "timestamp": ...
}
```

## Technical Approach
- Use ray-casting for lidar simulation
- Use circular area query for camera with added noise
- Use cone queries for sonar
- Add realistic noise models to all sensors
- Efficient spatial queries (use Agent 2's spatial structures)

## Communication
- Receive environment state from Agent 2 (but add noise/limitations)
- Receive map data from Agent 1 (for GPS)
- Provide sensor data to Agent 5 (RL agent)
- Provide visualization data to Agent 3 (Frontend)
- Monitor `.claude/agents/sensors.md` for notes from Agent 6

## Notes from Agent 6 (Testing & Documentation)
<!-- Agent 6 will write notes here -->
