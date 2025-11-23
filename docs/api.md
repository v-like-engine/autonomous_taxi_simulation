# API Documentation

Complete API reference for the Autonomous Taxi Simulation system.

## Table of Contents

1. [Map Parsing API](#map-parsing-api)
2. [Traffic Simulation API](#traffic-simulation-api)
3. [Sensor API](#sensor-api)
4. [RL Agent API](#rl-agent-api)
5. [Frontend REST API](#frontend-rest-api)
6. [WebSocket API](#websocket-api)

## Map Parsing API

### MapLoader

#### `load(image_path: str) -> np.ndarray`

Load a map image from file.

**Parameters:**
- `image_path` (str): Path to the map image file

**Returns:**
- `np.ndarray`: Loaded image as numpy array

**Raises:**
- `FileNotFoundError`: If image file doesn't exist
- `ValueError`: If image format is unsupported

**Example:**
```python
from src.map_parsing.map_loader import MapLoader

loader = MapLoader()
image = loader.load("maps/city_map.png")
```

### ZoneDetector

#### `detect_zones(image: np.ndarray) -> dict`

Detect zones from map image.

**Parameters:**
- `image` (np.ndarray): Map image

**Returns:**
- `dict`: Zone data with structure:
```python
{
    "main_zones": [
        {
            "type": "urban|yard|countryside|highway|prohibited",
            "polygon": [[x1, y1], [x2, y2], ...],
            "speed_limit": int
        },
        ...
    ],
    "subzones": {
        "sidewalks": [...],
        "parking": [...],
        "roads": [...]
    }
}
```

### RoadDetector

#### `detect_roads(image: np.ndarray, zones: dict) -> dict`

Detect roads and build road network.

**Parameters:**
- `image` (np.ndarray): Map image
- `zones` (dict): Previously detected zones

**Returns:**
- `dict`: Road network data

## Traffic Simulation API

### Vehicle

#### `__init__(position, vehicle_type, temperature=0.5)`

Create a vehicle instance.

**Parameters:**
- `position` (tuple): Initial (x, y) position
- `vehicle_type` (str): "car" or "truck"
- `temperature` (float): Behavior aggressiveness (0.0-1.0)

#### `update(delta_time: float, world_state: dict)`

Update vehicle state.

**Parameters:**
- `delta_time` (float): Time elapsed since last update (seconds)
- `world_state` (dict): Current world state

### TrafficManager

#### `spawn_vehicle(position, vehicle_type) -> str`

Spawn a new vehicle.

**Returns:**
- `str`: Vehicle ID

#### `update(delta_time: float)`

Update all traffic entities.

#### `get_state() -> dict`

Get current traffic state.

**Returns:**
```python
{
    "vehicles": [...],
    "pedestrians": [...],
    "main_car": {...}
}
```

## Sensor API

### Lidar

#### `scan(car_position, world_state) -> dict`

Perform lidar scan.

**Returns:**
```python
{
    "points": [
        {"angle": float, "distance": float, "intensity": float},
        ...
    ]
}
```

### Camera

#### `capture(car_position, world_state) -> dict`

Capture camera view.

**Returns:**
```python
{
    "vehicles": [{"position": [x, y], "confidence": float}, ...],
    "pedestrians": [{"position": [x, y], "confidence": float}, ...],
    "lane_markers": [...],
    "obstacles": [...]
}
```

### SensorFusion

#### `fuse(lidar_data, camera_data, sonar_data, gps_data, telemetry) -> dict`

Combine all sensor data.

**Returns:**
```python
{
    "lidar": {...},
    "camera": {...},
    "sonar": {...},
    "gps": {...},
    "telemetry": {...},
    "timestamp": float
}
```

### CarControl

#### `execute(command: dict)`

Execute control command.

**Parameters:**
```python
{
    "throttle": 0.0-1.0,
    "brake": 0.0-1.0,
    "steering": -1.0-1.0,
    "gear": int
}
```

## RL Agent API

### Agent

#### `__init__(state_dim, action_dim, config=None)`

Initialize RL agent.

#### `select_action(state, explore=True) -> np.ndarray`

Select action from state.

**Parameters:**
- `state`: Current state (sensor data)
- `explore` (bool): Whether to explore (training) or exploit (inference)

**Returns:**
- Action array

#### `train(num_episodes, env) -> dict`

Train the agent.

**Returns:**
- Training metrics

#### `save(path: str)`

Save model to file.

#### `load(path: str)`

Load model from file.

## Frontend REST API

Base URL: `http://localhost:5000/api`

### Map Endpoints

#### `POST /map/upload`

Upload a new map image.

**Request:**
- Content-Type: multipart/form-data
- Body: Form data with "file" field

**Response:**
```json
{
    "success": true,
    "map_id": "uuid",
    "map_data": {...}
}
```

#### `GET /map/<map_id>`

Get map data.

**Response:**
```json
{
    "map_id": "uuid",
    "zones": {...},
    "roads": {...},
    "bounds": {...}
}
```

#### `PUT /map/<map_id>`

Update map data (after editing).

**Request:**
```json
{
    "zones": {...},
    "roads": {...}
}
```

### Simulation Endpoints

#### `POST /simulation/start`

Start simulation.

**Request:**
```json
{
    "map_id": "uuid",
    "traffic_density": 50,
    "traffic_temperature": 0.5,
    "pedestrian_density": 30
}
```

**Response:**
```json
{
    "success": true,
    "simulation_id": "uuid"
}
```

#### `POST /simulation/stop`

Stop simulation.

#### `GET /simulation/state`

Get current simulation state.

**Response:**
```json
{
    "vehicles": [...],
    "pedestrians": [...],
    "main_car": {...},
    "timestamp": float
}
```

### Car Endpoints

#### `POST /car/place`

Place the main car.

**Request:**
```json
{
    "position": [x, y],
    "heading": angle
}
```

#### `POST /car/destination`

Set destination.

**Request:**
```json
{
    "position": [x, y]
}
```

### Training Endpoints

#### `POST /train/start`

Start training.

**Request:**
```json
{
    "episodes": 1000,
    "batch_size": 128,
    "learning_rate": 0.0001
}
```

#### `GET /train/status`

Get training status.

**Response:**
```json
{
    "episode": 523,
    "total_episodes": 1000,
    "avg_reward": 145.2,
    "success_rate": 0.78,
    "collision_rate": 0.05
}
```

#### `GET /train/metrics`

Get training metrics history.

### Model Endpoints

#### `GET /models`

List available models.

**Response:**
```json
{
    "models": [
        {
            "name": "best_model.pth",
            "timestamp": "2025-11-23T10:30:00",
            "metrics": {...}
        },
        ...
    ]
}
```

#### `POST /models/<model_name>/load`

Load a trained model for inference.

## WebSocket API

WebSocket URL: `ws://localhost:5000/ws`

### Events

#### Client → Server

**`subscribe`**: Subscribe to updates
```json
{
    "event": "subscribe",
    "channels": ["simulation", "sensors", "training"]
}
```

**`control`**: Send control command
```json
{
    "event": "control",
    "command": {
        "throttle": 0.7,
        "brake": 0.0,
        "steering": -0.15
    }
}
```

#### Server → Client

**`simulation_update`**: Simulation state update
```json
{
    "event": "simulation_update",
    "data": {
        "vehicles": [...],
        "pedestrians": [...],
        "main_car": {...}
    }
}
```

**`sensor_update`**: Sensor data update
```json
{
    "event": "sensor_update",
    "data": {
        "lidar": {...},
        "camera": {...},
        "sonar": {...},
        "gps": {...}
    }
}
```

**`training_update`**: Training progress update
```json
{
    "event": "training_update",
    "data": {
        "episode": 523,
        "reward": 145.2,
        "loss": 0.032
    }
}
```

## Error Responses

All API endpoints return errors in this format:

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {...}
    }
}
```

Common error codes:
- `INVALID_INPUT`: Invalid request parameters
- `NOT_FOUND`: Resource not found
- `SIMULATION_ERROR`: Simulation error occurred
- `MODEL_ERROR`: RL model error
- `INTERNAL_ERROR`: Internal server error

## Rate Limiting

API endpoints are rate-limited:
- Map upload: 10 requests/minute
- Simulation control: 60 requests/minute
- State queries: 120 requests/minute

## Authentication

Currently, the API does not require authentication. In production, implement:
- API keys for external access
- Session tokens for web interface
- OAuth for third-party integrations

---

For more details, see component-specific documentation:
- [Map Parsing](map_parsing.md)
- [Traffic Simulation](traffic_simulation.md)
- [Sensors](sensors.md)
- [RL Agent](rl_agent.md)
