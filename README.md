# Autonomous Taxi Simulation

A comprehensive simulation environment for training and testing autonomous vehicles using reinforcement learning, featuring realistic traffic, sensor simulation, and an intuitive blueprint-style interface.

## Features

- **Advanced Map Parsing**: Automatic detection of roads, zones, and traffic rules from map images
- **Realistic Traffic Simulation**: Dynamic traffic with cars, trucks, and pedestrians exhibiting realistic behavior
- **Sensor Suite**: Lidar, camera, sonar, and GPS sensors with realistic limitations and noise
- **Reinforcement Learning**: Train autonomous agents using state-of-the-art RL algorithms
- **Blueprint-Style UI**: Professional research interface with map editor and real-time visualization
- **Docker Support**: Easy deployment with Docker containers

## Quick Start

### Prerequisites

- Python 3.9+
- pip or Docker

### Installation

#### Option 1: Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd autonomous_taxi_simulation

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/frontend/app.py
```

#### Option 2: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t autonomous-taxi .
docker run -p 5000:5000 autonomous-taxi
```

Access the application at `http://localhost:5000`

## Project Structure

```
autonomous_taxi_simulation/
├── src/
│   ├── map_parsing/       # Map loading and zone detection (Agent 1)
│   ├── traffic_simulation/# Traffic and pedestrian simulation (Agent 2)
│   ├── frontend/          # Web UI and API (Agent 3)
│   ├── sensors/           # Sensor simulation (Agent 4)
│   └── rl_agent/          # Reinforcement learning (Agent 5)
├── tests/                 # Unit and integration tests
├── docs/                  # Detailed documentation
├── static/                # Frontend assets (CSS, JS, images)
├── templates/             # HTML templates
├── maps/                  # Map images and data
├── models/                # Trained RL models
└── requirements.txt       # Python dependencies
```

## Components

### 1. Map Parsing
- Load schematic maps from Yandex/Google Maps images
- Automatic zone detection (prohibited, yard, urban, countryside, highway)
- Road network extraction with lanes and directions
- Intersection and crosswalk detection

### 2. Traffic Simulation
- Realistic vehicle behavior with temperature-based randomness
- Pedestrian simulation with sidewalk walking and crosswalk crossing
- Traffic density control
- Collision avoidance and traffic rules

### 3. Frontend Design
- Blueprint-style research interface
- Interactive map viewer with zoom and pan
- Map editor for manual zone/road editing
- Real-time simulation controls
- Sensor data visualization

### 4. Sensor Simulation
- **Lidar**: 360° point cloud with 30-50m range
- **Camera**: Wide field of view with realistic noise
- **Sonar**: Short-range (5-10m) proximity sensors
- **GPS**: Position and route with realistic accuracy
- **Telemetry**: Speed, acceleration, and vehicle state

### 5. Reinforcement Learning
- DQN/PPO/SAC algorithms for autonomous driving
- Comprehensive reward function for safe, legal driving
- Training and inference pipelines
- Model checkpoints and metrics

## Usage

### Loading a Map

1. Open the application in your browser
2. Click "Load Map" and select a map image
3. Wait for automatic zone and road detection
4. Optionally edit zones/roads using the map editor

### Running Simulation

1. Set traffic density and behavior temperature
2. Click "Start Simulation" to begin traffic
3. Click on the map to place the autonomous car
4. Set destination by clicking target location
5. Watch the RL agent navigate the environment

### Training the RL Agent

```bash
# Run training script
python src/rl_agent/training.py --episodes 1000 --save-interval 100

# Use trained model for inference
python src/rl_agent/agent.py --model models/best_model.pth
```

## Documentation

- [Installation Guide](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [System Architecture](docs/architecture.md)
- [API Documentation](docs/api.md)
- Component-specific docs:
  - [Map Parsing](docs/map_parsing.md)
  - [Traffic Simulation](docs/traffic_simulation.md)
  - [Frontend Design](docs/frontend.md)
  - [Sensor Simulation](docs/sensors.md)
  - [RL Agent](docs/rl_agent.md)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test modules
pytest tests/test_map_parsing.py
pytest tests/test_traffic_simulation.py
pytest tests/test_sensors.py
pytest tests/test_rl_agent.py
pytest tests/test_integration.py
```

## Development

This project was developed using a multi-agent approach with specialized agents for each component:
- Agent 1: Map Parsing
- Agent 2: Traffic Simulation
- Agent 3: Frontend Design
- Agent 4: Sensor Simulation
- Agent 5: Reinforcement Learning
- Agent 6: Testing & Documentation

## Performance

- Target: 60 FPS smooth animation
- Supports hundreds of traffic entities
- Real-time sensor processing
- Optimized spatial partitioning for collision detection

## Safety & Rules

The autonomous car must:
- Not collide with vehicles or pedestrians
- Respect speed limits (zone-based)
- Stay on roads and in correct lanes
- Follow traffic directions
- Avoid prohibited zones

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Acknowledgments

Built with modern technologies:
- Python 3.9+
- PyTorch for deep learning
- OpenCV for image processing
- Flask for web framework
- HTML5 Canvas for rendering

## Support

For issues, questions, or contributions, please see the documentation or open an issue on GitHub.
