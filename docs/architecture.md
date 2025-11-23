# System Architecture

This document describes the architecture of the Autonomous Taxi Simulation system, including component interactions, data flow, and design decisions.

## Table of Contents

1. [Overview](#overview)
2. [System Components](#system-components)
3. [Architecture Diagram](#architecture-diagram)
4. [Data Flow](#data-flow)
5. [Component Interactions](#component-interactions)
6. [Design Patterns](#design-patterns)
7. [Technology Stack](#technology-stack)
8. [File Structure](#file-structure)

## Overview

The Autonomous Taxi Simulation is a modular system designed with a multi-agent development approach. The system consists of 5 core functional components plus testing/documentation:

- **Agent 1**: Map Parsing - Processes map images to extract zones and roads
- **Agent 2**: Traffic Simulation - Simulates realistic traffic and pedestrians
- **Agent 3**: Frontend Design - Provides UI and visualization
- **Agent 4**: Sensor Simulation - Simulates realistic car sensors
- **Agent 5**: RL Agent - Controls the autonomous car using reinforcement learning
- **Agent 6**: Testing & Documentation - Ensures quality and provides documentation

### Design Philosophy

1. **Modularity**: Each component is independent and loosely coupled
2. **Realism**: Sensors have realistic limitations; no "perfect" world access
3. **Scalability**: Support hundreds of entities without performance degradation
4. **Extensibility**: Easy to add new features or modify existing ones
5. **Testability**: Comprehensive test coverage for all components

## System Components

### 1. Map Parsing Module

**Purpose**: Extract structured data from map images

**Responsibilities**:
- Load map images (Yandex/Google Maps style)
- Detect zones (prohibited, yard, urban, countryside, highway)
- Detect roads, lanes, and directions
- Identify intersections and crosswalks
- Build road network graph

**Input**: Map image file (PNG, JPG)
**Output**: Structured map data (JSON)

**Key Classes**:
- `MapLoader`: Image loading and preprocessing
- `ZoneDetector`: Zone detection using computer vision
- `RoadDetector`: Road network extraction
- `ImageProcessor`: Image processing utilities

### 2. Traffic Simulation Module

**Purpose**: Simulate realistic traffic environment

**Responsibilities**:
- Spawn and manage vehicles (cars, trucks)
- Spawn and manage pedestrians
- Implement realistic physics and behavior
- Handle collisions and interactions
- Provide temperature-based random behavior

**Input**: Map data, simulation parameters
**Output**: Entity positions and states

**Key Classes**:
- `Vehicle`: Individual vehicle entity
- `Pedestrian`: Individual pedestrian entity
- `TrafficManager`: Manages all traffic entities
- `Behavior`: Random behavior models

### 3. Frontend Module

**Purpose**: User interface and visualization

**Responsibilities**:
- Display map and overlays
- Render vehicles and pedestrians
- Provide simulation controls
- Display sensor visualizations
- Implement map editor
- Handle user interactions

**Input**: All system data
**Output**: Visual display, user commands

**Key Files**:
- `app.py`: Flask application
- `routes.py`: API routes
- `main.js`: Main UI logic
- `map_viewer.js`: Map display and interaction
- `editor.js`: Map editing tools
- `animation.js`: Rendering loop

### 4. Sensor Simulation Module

**Purpose**: Provide realistic sensor data to RL agent

**Responsibilities**:
- Simulate Lidar (360°, 30-50m range)
- Simulate Camera (wide FOV, noisy data)
- Simulate Sonar (short range, accurate)
- Simulate GPS (position, route, zones)
- Provide car telemetry
- Fuse sensor data
- Provide car control interface

**Input**: World state (from traffic simulation)
**Output**: Noisy, limited sensor data

**Key Classes**:
- `Lidar`: Ray-casting based lidar
- `Camera`: Vision sensor with noise
- `Sonar`: Proximity sensors
- `GPS`: Position and navigation
- `CarTelemetry`: Internal car sensors
- `SensorFusion`: Combines all sensor data
- `CarControl`: Control interface

### 5. RL Agent Module

**Purpose**: Train and control autonomous car

**Responsibilities**:
- Process sensor data
- Make driving decisions
- Learn from experience
- Optimize for safety and efficiency
- Follow routes to destinations

**Input**: Sensor data
**Output**: Control commands (throttle, brake, steering)

**Key Classes**:
- `Agent`: Main RL agent (DQN/PPO/SAC)
- `Model`: Neural network
- `Training`: Training loop
- `ReplayBuffer`: Experience replay
- `Reward`: Reward function

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Frontend - Agent 3)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Map View │  │ Controls │  │ Metrics  │  │  Editor  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────┬─────────────┬────────────┬────────────┬───────────────┘
         │             │            │            │
         │             ▼            ▼            │
         │      ┌──────────────────────┐        │
         │      │  Map Parsing         │◄───────┘
         │      │  (Agent 1)           │
         │      └──────────┬───────────┘
         │                 │
         │                 │ Map Data
         │                 ▼
         │      ┌──────────────────────┐
         └─────►│  Traffic Simulation  │
                │  (Agent 2)           │
                └──────────┬───────────┘
                           │
                           │ World State
                           ▼
                ┌──────────────────────┐
                │  Sensor Simulation   │
                │  (Agent 4)           │
                └──────────┬───────────┘
                           │
                           │ Sensor Data
                           ▼
                ┌──────────────────────┐
                │  RL Agent            │
                │  (Agent 5)           │
                └──────────┬───────────┘
                           │
                           │ Control Commands
                           ▼
                      (Back to Traffic Simulation)
```

### Detailed Component Interaction

```
┌─────────────┐
│ Map Image   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐      ┌──────────────┐
│ Map Parsing     │─────►│  Map Data    │
│ - Zone Detection│      │  - Zones     │
│ - Road Detection│      │  - Roads     │
└─────────────────┘      │  - Network   │
                         └──────┬───────┘
                                │
                                ▼
                         ┌──────────────┐      ┌──────────────┐
                         │  Traffic     │─────►│ Entities     │
                         │  Manager     │      │ - Vehicles   │
                         │  - Spawn     │      │ - Pedestrians│
                         │  - Update    │      └──────┬───────┘
                         └──────────────┘             │
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │ Sensor Array │
                                               │ - Lidar      │
                                               │ - Camera     │
                                               │ - Sonar      │
                                               │ - GPS        │
                                               └──────┬───────┘
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │ Sensor Fusion│
                                               └──────┬───────┘
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │  RL Agent    │
                                               │  - Process   │
                                               │  - Decide    │
                                               │  - Learn     │
                                               └──────┬───────┘
                                                      │
                                                      ▼
                                               ┌──────────────┐
                                               │ Car Control  │
                                               │ - Throttle   │
                                               │ - Brake      │
                                               │ - Steering   │
                                               └──────────────┘
```

## Data Flow

### 1. Map Loading Flow

```
User uploads map image
    │
    ▼
MapLoader.load(image_path)
    │
    ▼
ImageProcessor.preprocess(image)
    │
    ├──► ZoneDetector.detect_zones(image) ──► Zone polygons + speed limits
    │
    └──► RoadDetector.detect_roads(image) ──► Road network + lanes
         │
         └──► Build graph structure for routing
              │
              ▼
         Return map_data JSON
              │
              ▼
         Store in TrafficManager
              │
              └──► Store in GPS sensor
```

### 2. Simulation Update Loop

```
While simulation running:
    │
    ├──► TrafficManager.update(delta_time)
    │    │
    │    ├──► Update all vehicles
    │    │    │
    │    │    └──► Apply physics, behavior, collision detection
    │    │
    │    └──► Update all pedestrians
    │         │
    │         └──► Update position, check crosswalks
    │
    ├──► SensorArray.update(world_state)
    │    │
    │    ├──► Lidar.scan() ──► Point cloud
    │    ├──► Camera.capture() ──► Detected objects (noisy)
    │    ├──► Sonar.measure() ──► Distances
    │    └──► GPS.locate() ──► Position + route
    │         │
    │         └──► SensorFusion.fuse() ──► Combined sensor data
    │
    ├──► RLAgent.step(sensor_data)
    │    │
    │    ├──► Process sensor input
    │    ├──► Select action (or get from policy)
    │    └──► Return control command
    │
    ├──► CarControl.execute(command)
    │    │
    │    └──► Update main car state in traffic simulation
    │
    └──► Frontend.render(all_data)
         │
         └──► Display on canvas
```

### 3. Training Flow

```
For each episode:
    │
    ├──► Reset environment
    │    │
    │    └──► Place car, set destination, reset traffic
    │
    ├──► For each step:
    │    │
    │    ├──► Get sensor data
    │    ├──► Agent selects action (with exploration)
    │    ├──► Execute action
    │    ├──► Get new sensor data
    │    ├──► Calculate reward
    │    ├──► Store experience (state, action, reward, next_state)
    │    │
    │    └──► If done: break
    │
    ├──► Sample batch from replay buffer
    │
    ├──► Update model using batch
    │
    ├──► Track metrics (reward, success, collisions)
    │
    └──► Save model checkpoint if improved
```

## Component Interactions

### Critical Interfaces

#### 1. Map Data Interface

Used by Traffic Simulation, Sensors, and Frontend:

```python
{
    "zones": {
        "main_zones": [
            {
                "type": "urban",
                "polygon": [[x1, y1], [x2, y2], ...],
                "speed_limit": 60
            },
            ...
        ],
        "subzones": {
            "sidewalks": [...],
            "parking": [...],
            "roads": [...]
        }
    },
    "roads": {
        "network": graph_structure,
        "lanes": [...],
        "intersections": [...],
        "crosswalks": [...]
    },
    "map_bounds": {"width": 1920, "height": 1080}
}
```

#### 2. Traffic State Interface

Used by Sensors and Frontend:

```python
{
    "vehicles": [
        {
            "id": "v1",
            "type": "car",
            "position": [x, y],
            "velocity": [vx, vy],
            "heading": angle,
            "dimensions": [width, height]
        },
        ...
    ],
    "pedestrians": [
        {
            "id": "p1",
            "position": [x, y],
            "velocity": [vx, vy]
        },
        ...
    ],
    "main_car": {
        "position": [x, y],
        "velocity": [vx, vy],
        "heading": angle,
        ...
    }
}
```

#### 3. Sensor Data Interface

Used by RL Agent:

```python
{
    "lidar": {
        "points": [
            {"angle": 0, "distance": 15.3, "intensity": 0.8},
            ...
        ]
    },
    "camera": {
        "vehicles": [{"position": [x, y], "confidence": 0.9}, ...],
        "pedestrians": [...]
    },
    "sonar": {
        "front_left": 3.2,
        "front_center": 5.8,
        ...
    },
    "gps": {
        "position": [x, y],
        "heading": 45.0,
        "current_zone": "urban",
        "speed_limit": 60,
        "route": [...]
    },
    "telemetry": {
        "speed": 45.5,
        "acceleration": 1.2,
        ...
    }
}
```

#### 4. Control Interface

Used by RL Agent to control car:

```python
{
    "throttle": 0.7,     # 0.0-1.0
    "brake": 0.0,        # 0.0-1.0
    "steering": -0.15,   # -1.0 to 1.0
    "gear": 3            # -1, 0, 1, 2, 3, 4, 5
}
```

## Design Patterns

### 1. Model-View-Controller (MVC)

- **Model**: Map data, traffic state, RL model
- **View**: Frontend rendering
- **Controller**: User input handling, simulation control

### 2. Observer Pattern

- Frontend observes traffic simulation state
- Sensors observe traffic simulation state
- Training observes agent performance

### 3. Strategy Pattern

- Different RL algorithms (DQN, PPO, SAC) implement same interface
- Different behavior models for traffic

### 4. Factory Pattern

- VehicleFactory creates different vehicle types
- SensorFactory creates sensor instances

### 5. Singleton Pattern

- TrafficManager (single instance manages all traffic)
- Configuration manager

## Technology Stack

### Backend

- **Python 3.9+**: Core language
- **Flask**: Web framework
- **OpenCV**: Image processing
- **NumPy**: Numerical operations
- **PyTorch**: Deep learning
- **NetworkX**: Graph structures

### Frontend

- **HTML5**: Structure
- **CSS3**: Styling (blueprint theme)
- **JavaScript (ES6+)**: Interactivity
- **Canvas API**: Rendering

### Testing

- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking

### DevOps

- **Docker**: Containerization
- **Docker Compose**: Orchestration
- **Git**: Version control

## File Structure

```
autonomous_taxi_simulation/
│
├── src/                          # Source code
│   ├── map_parsing/              # Agent 1
│   │   ├── __init__.py
│   │   ├── map_loader.py
│   │   ├── zone_detector.py
│   │   ├── road_detector.py
│   │   └── image_processor.py
│   │
│   ├── traffic_simulation/       # Agent 2
│   │   ├── __init__.py
│   │   ├── vehicle.py
│   │   ├── pedestrian.py
│   │   ├── traffic_manager.py
│   │   └── behavior.py
│   │
│   ├── frontend/                 # Agent 3
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── routes.py
│   │
│   ├── sensors/                  # Agent 4
│   │   ├── __init__.py
│   │   ├── lidar.py
│   │   ├── camera.py
│   │   ├── sonar.py
│   │   ├── gps.py
│   │   ├── car_telemetry.py
│   │   ├── sensor_fusion.py
│   │   └── car_control.py
│   │
│   └── rl_agent/                 # Agent 5
│       ├── __init__.py
│       ├── agent.py
│       ├── model.py
│       ├── training.py
│       ├── replay_buffer.py
│       └── reward.py
│
├── tests/                        # Test suite (Agent 6)
│   ├── __init__.py
│   ├── test_map_parsing.py
│   ├── test_traffic_simulation.py
│   ├── test_sensors.py
│   ├── test_rl_agent.py
│   └── test_integration.py
│
├── docs/                         # Documentation (Agent 6)
│   ├── installation.md
│   ├── usage.md
│   ├── architecture.md
│   ├── api.md
│   ├── map_parsing.md
│   ├── traffic_simulation.md
│   ├── frontend.md
│   ├── sensors.md
│   └── rl_agent.md
│
├── static/                       # Frontend assets
│   ├── css/
│   │   ├── style.css
│   │   └── blueprint.css
│   ├── js/
│   │   ├── main.js
│   │   ├── map_viewer.js
│   │   ├── editor.js
│   │   ├── controls.js
│   │   └── animation.js
│   └── images/
│
├── templates/                    # HTML templates
│   ├── index.html
│   ├── editor.html
│   └── simulation.html
│
├── maps/                         # Map storage
├── models/                       # Trained models
├── data/                         # Runtime data
├── logs/                         # Application logs
│
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker Compose
├── .dockerignore                 # Docker ignore
└── README.md                     # Main documentation
```

## Performance Considerations

### Optimization Strategies

1. **Spatial Partitioning**: Use grid or quad-tree for efficient collision detection
2. **Level of Detail**: Render distant objects with less detail
3. **Batch Processing**: Process multiple entities together
4. **Caching**: Cache frequently accessed data (map data, road network)
5. **Asynchronous Processing**: Use async for I/O operations

### Scalability

- **Entity Management**: Efficient spawning/despawning
- **Rendering**: Canvas optimization, requestAnimationFrame
- **Sensor Processing**: Parallel processing where possible
- **Memory Management**: Cleanup unused objects

### Target Performance

- **FPS**: 60 (frontend rendering)
- **Simulation Rate**: 30-60 updates/second
- **Max Entities**: 200+ vehicles + 100+ pedestrians
- **Response Time**: <100ms for user interactions

## Security Considerations

1. **Input Validation**: Validate all user inputs
2. **File Upload**: Restrict file types and sizes
3. **API Rate Limiting**: Prevent abuse
4. **Data Sanitization**: Clean all data before processing
5. **Error Handling**: Don't expose internal errors

## Future Extensibility

The architecture supports future enhancements:

1. **Multi-car scenarios**: Multiple RL agents
2. **Networked simulation**: Multi-client support
3. **Advanced sensors**: Radar, V2V communication
4. **Weather simulation**: Rain, fog effects on sensors
5. **Day/night cycle**: Lighting effects
6. **Traffic lights**: Signal control
7. **More RL algorithms**: Additional algorithms
8. **Model export**: ONNX, TensorFlow Lite

---

This architecture provides a solid foundation for a scalable, maintainable, and extensible autonomous vehicle simulation system.
