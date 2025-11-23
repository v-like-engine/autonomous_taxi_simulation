# Traffic Simulation Documentation

Documentation for the Traffic Simulation module (Agent 2).

## Overview

The Traffic Simulation module simulates realistic traffic with vehicles (cars, trucks) and pedestrians. It provides physics-based movement, collision detection, and temperature-based random behavior.

## Components

### Vehicle

Represents individual vehicles in the simulation.

**Vehicle Types:**
- **Car**: Standard size, normal acceleration
- **Truck**: Larger, slower acceleration

**Behavior:**
- Follow roads and stay in lanes
- Respect speed limits
- Avoid collisions
- Yield to pedestrians at crosswalks
- Temperature-based random behavior

**Usage:**
```python
from src.traffic_simulation.vehicle import Vehicle

car = Vehicle(
    position=(100, 200),
    vehicle_type="car",
    temperature=0.5
)
car.update(delta_time=0.016, world_state=world)
```

### Pedestrian

Represents individual pedestrians.

**Behavior:**
- Walk on sidewalks
- Cross at crosswalks
- Wait for safe gaps in traffic
- Vary walking speed
- React to approaching vehicles

**Usage:**
```python
from src.traffic_simulation.pedestrian import Pedestrian

ped = Pedestrian(position=(150, 250))
ped.update(delta_time=0.016, world_state=world)
```

### TrafficManager

Manages all traffic entities, spawning, and updates.

**Responsibilities:**
- Spawn vehicles at appropriate locations
- Despawn vehicles when they exit
- Update all entities
- Manage traffic density
- Handle intersections
- Detect collisions

**Usage:**
```python
from src.traffic_simulation.traffic_manager import TrafficManager

manager = TrafficManager(map_data)
manager.set_density(vehicle_density=50, pedestrian_density=30)
manager.update(delta_time=0.016)
state = manager.get_state()
```

### Behavior

Temperature-based random behavior models.

**Temperature Levels:**
- **Low (0.0-0.3)**: Careful driver
  - Follows rules strictly
  - No violations
  - Safe distances

- **Medium (0.3-0.7)**: Normal driver
  - Occasional minor violations
  - Some speeding (<10 km/h over)
  - Normal lane changes

- **High (0.7-1.0)**: Aggressive driver
  - Frequent violations
  - Significant speeding (up to +20 km/h)
  - Sudden lane changes
  - May run yellow/red lights

**Random Events:**
- Lane changes
- Sudden braking
- Aggressive acceleration
- Cutting off other cars
- Speed variations

## Physics Model

**Vehicle Dynamics:**
- Position update: `p(t+dt) = p(t) + v(t) * dt`
- Velocity update: `v(t+dt) = v(t) + a(t) * dt`
- Acceleration limits: Car: -8 to 4 m/s², Truck: -6 to 2 m/s²
- Turning radius: Speed-dependent
- Friction and drag applied

**Collision Detection:**
- Bounding box collision
- Spatial partitioning for efficiency
- Collision response (bounce, stop)

## Configuration

```yaml
# config/traffic_simulation.yaml
vehicles:
  car:
    max_acceleration: 4.0  # m/s²
    max_braking: 8.0
    max_speed: 180  # km/h
    turning_radius: 5.0  # meters

  truck:
    max_acceleration: 2.0
    max_braking: 6.0
    max_speed: 120
    turning_radius: 8.0

pedestrians:
  walking_speed: 1.5  # m/s
  running_speed: 3.0
  crossing_wait_time: 2.0  # seconds

traffic:
  spawn_rate: 0.1  # entities per second
  despawn_distance: 100  # pixels from map edge

behavior:
  temperature_distribution:
    low: 0.3  # 30% careful drivers
    medium: 0.5  # 50% normal drivers
    high: 0.2  # 20% aggressive drivers
```

## API Reference

See [API Documentation](api.md#traffic-simulation-api).
