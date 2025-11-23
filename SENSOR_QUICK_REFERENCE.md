# Sensor System Quick Reference

**For Agent 5 (RL Agent) - START HERE!**

## Simplest Usage (Recommended)

```python
from sensors import SensorFusion

# 1. Initialize once
fusion = SensorFusion()

# 2. In your RL loop:
# Get observation
sensor_data = fusion.sense_all(
    car_position=(x, y),
    car_heading=degrees,
    car_state={"position": (x,y), "velocity": (vx, vy), "heading": deg},
    environment_state=env_state,  # from Agent 2
    map_data=map_data,            # from Agent 1
    destination=(dest_x, dest_y),
    delta_time=0.1
)

# Convert to state vector for your RL model
state = fusion.get_processed_state(sensor_data, "feature_vector")
# state is now a 23D numpy array ready for your neural network

# 3. Get action from your RL agent
action = your_rl_agent.select_action(state)

# 4. Apply control
fusion.apply_control(
    throttle=action[0],  # 0.0 to 1.0
    steering=action[1]   # -1.0 to 1.0
)

# 5. Update physics
fusion.update_control(delta_time=0.1, current_speed=current_speed_ms)
new_car_state = fusion.apply_control_to_physics(car_state, delta_time=0.1)
```

## What You Get (Observation)

**23-dimensional feature vector:**
- GPS position (x, y)
- Heading
- Speed limit
- Distance to destination
- Speed, acceleration
- Steering angle, fuel level
- 8 sonar distances
- Counts of nearby vehicles, pedestrians, obstacles
- Lidar statistics (closest, average, density)

All values are normalized to [0, 1] range.

## What You Control (Action)

**3 continuous actions:**
```python
action = [throttle, steering, brake]  # optional brake
# throttle: 0.0 (no gas) to 1.0 (full throttle)
# steering: -1.0 (full left) to 1.0 (full right)
# brake: 0.0 (no brake) to 1.0 (full brake)
```

Or simplified:
```python
action = [throttle, steering]  # just 2 actions
# Gear is automatic by default
```

## Gym Environment Integration

```python
import gymnasium as gym
from sensors import SensorFusion

class TaxiEnv(gym.Env):
    def __init__(self):
        self.fusion = SensorFusion()

        # Observation space: 23D vector
        self.observation_space = gym.spaces.Box(
            low=0.0, high=1.0, shape=(23,), dtype=np.float32
        )

        # Action space: 2D continuous (throttle, steering)
        self.action_space = gym.spaces.Box(
            low=np.array([0.0, -1.0]),
            high=np.array([1.0, 1.0]),
            dtype=np.float32
        )

    def step(self, action):
        # Apply control
        self.fusion.apply_control(throttle=action[0], steering=action[1])

        # Update physics
        self.fusion.update_control(self.dt, self.current_speed)
        self.car_state = self.fusion.apply_control_to_physics(self.car_state, self.dt)

        # Get new observation
        sensor_data = self.fusion.sense_all(...)
        obs = self.fusion.get_processed_state(sensor_data, "feature_vector")

        # Calculate reward
        reward = self.calculate_reward(...)

        # Check termination
        done = self.check_done(...)

        return obs, reward, done, False, {}

    def reset(self):
        self.fusion.reset()
        # ... reset environment ...
        sensor_data = self.fusion.sense_all(...)
        obs = self.fusion.get_processed_state(sensor_data, "feature_vector")
        return obs, {}
```

## Data Formats for Other Agents

### Agent 2 (Traffic Simulation) - Environment State

```python
environment_state = {
    "vehicles": [
        {
            "position": (x, y),      # required
            "heading": degrees,      # required
            "vehicle_type": "car",   # "car" or "truck"
            "length": 4.5,          # meters
            "width": 2.0            # meters
        },
        ...
    ],
    "pedestrians": [
        {
            "position": (x, y),  # required
            "radius": 0.3        # meters
        },
        ...
    ],
    "obstacles": [
        {
            "position": (x, y),
            "radius": 0.5,
            "geometry": "circle"  # or "rectangle"
        },
        ...
    ]
}
```

### Agent 1 (Map Parser) - Map Data

```python
map_data = {
    "zones": {
        "main_zones": [
            {
                "type": "urban",  # or "countryside", "highway"
                "speed_limit": 60,
                "id": 1,
                "bounds": {"min_x": 0, "max_x": 200, "min_y": 0, "max_y": 200}
                # OR "polygon": [(x1,y1), (x2,y2), ...]
            },
            ...
        ]
    },
    "roads": {
        "lanes": [
            {
                "id": 1,
                "type": "main_road",
                "direction": "bidirectional",
                "center_line": [(x1, y1), (x2, y2), ...]
            },
            ...
        ]
    },
    "boundaries": [  # optional
        {"start": (x1, y1), "end": (x2, y2)},
        ...
    ]
}
```

## Sensor Capabilities Summary

| Sensor | Range | Accuracy | What it detects |
|--------|-------|----------|-----------------|
| **Camera** | 75m | ±2-5m | Vehicles, pedestrians, obstacles, lanes |
| **Lidar** | 40m | ±2cm | Accurate distances (point cloud) |
| **Sonar** | 8m | ±1cm | Very accurate close-range distances |
| **GPS** | N/A | ±3.5m | Position, roads, zones, route |
| **Telemetry** | N/A | High | Speed, RPM, fuel, gear, steering |

## Common Pitfalls

1. **Don't access environment state directly!** Use only sensor data.
2. **Remember sensors have limitations:** Camera is noisy, Lidar has limited range.
3. **Update control before physics:** Call `update_control()` before `apply_to_physics()`.
4. **Use feature_vector for RL:** It's already normalized and ready for neural networks.
5. **Check GPS signal:** GPS can lose signal (1% chance), check `has_signal` field.

## Testing Your Integration

```bash
# Test sensors work
python test_sensors.py

# Run example
python examples/sensor_usage_example.py
```

## Need More Details?

See `src/sensors/README.md` for complete API documentation.

## Files You Need

Just import from `sensors`:
```python
from sensors import SensorFusion  # That's it!
```

All sensors are included and configured with good defaults.

## Questions?

- Check `src/sensors/README.md` for detailed docs
- See `examples/sensor_usage_example.py` for complete examples
- Read `AGENT4_IMPLEMENTATION_SUMMARY.md` for technical details
