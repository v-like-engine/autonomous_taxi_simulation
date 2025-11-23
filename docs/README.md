# Documentation Index

Complete documentation for the Autonomous Taxi Simulation system.

## Quick Links

- [Installation Guide](installation.md) - Get started with installation
- [Usage Guide](usage.md) - Learn how to use the application
- [System Architecture](architecture.md) - Understand the system design
- [API Reference](api.md) - Complete API documentation

## Component Documentation

### Core Modules

1. **[Map Parsing](map_parsing.md)** (Agent 1)
   - Automatic zone and road detection from map images
   - Support for light and dark theme maps
   - Road network graph construction

2. **[Traffic Simulation](traffic_simulation.md)** (Agent 2)
   - Realistic vehicle and pedestrian behavior
   - Physics-based movement
   - Temperature-based random behavior

3. **[Frontend Design](frontend.md)** (Agent 3)
   - Blueprint-style research interface
   - Interactive map viewer and editor
   - Real-time visualization

4. **[Sensor Simulation](sensors.md)** (Agent 4)
   - Lidar, camera, sonar, GPS sensors
   - Realistic noise and limitations
   - Sensor fusion

5. **[RL Agent](rl_agent.md)** (Agent 5)
   - Reinforcement learning for autonomous driving
   - Training and inference
   - Reward function design

## Getting Started

### New Users

1. Start with [Installation Guide](installation.md)
2. Follow [Usage Guide](usage.md) for basic operations
3. Read [Architecture](architecture.md) to understand the system

### Developers

1. Review [System Architecture](architecture.md)
2. Check [API Reference](api.md) for integration
3. Read component-specific documentation
4. Run tests: `pytest`

### Advanced Users

1. Customize reward functions in [RL Agent](rl_agent.md)
2. Tune hyperparameters for training
3. Create custom maps and scenarios
4. Extend the system with new features

## Documentation Structure

```
docs/
├── README.md                  # This file
├── installation.md            # Installation instructions
├── usage.md                   # How to use the application
├── architecture.md            # System architecture
├── api.md                     # API reference
├── map_parsing.md             # Map parsing module
├── traffic_simulation.md      # Traffic simulation module
├── frontend.md                # Frontend module
├── sensors.md                 # Sensor simulation module
└── rl_agent.md                # RL agent module
```

## Common Tasks

### Load a Map
See [Usage Guide - Loading a Map](usage.md#loading-a-map)

### Edit a Map
See [Usage Guide - Map Editor](usage.md#map-editor)

### Run Simulation
See [Usage Guide - Running Simulation](usage.md#running-simulation)

### Train RL Agent
See [Usage Guide - Training the RL Agent](usage.md#training-the-rl-agent)

### Use Trained Model
See [Usage Guide - Using Trained Models](usage.md#using-trained-models)

## Troubleshooting

### Installation Issues
See [Installation Guide - Troubleshooting](installation.md#troubleshooting)

### Runtime Issues
See [Usage Guide - Troubleshooting](usage.md#troubleshooting)

### Performance Issues
See [Architecture - Performance Considerations](architecture.md#performance-considerations)

## API Quick Reference

### REST API
- Base URL: `http://localhost:5000/api`
- [Full API Reference](api.md#frontend-rest-api)

### WebSocket
- URL: `ws://localhost:5000/ws`
- [WebSocket API Reference](api.md#websocket-api)

### Python API
- [Map Parsing API](api.md#map-parsing-api)
- [Traffic Simulation API](api.md#traffic-simulation-api)
- [Sensor API](api.md#sensor-api)
- [RL Agent API](api.md#rl-agent-api)

## Configuration

Configuration files are located in `config/` directory:
- `simulation.yaml` - Simulation parameters
- `rl_agent.yaml` - RL agent hyperparameters
- `sensors.yaml` - Sensor configurations
- `map_parsing.yaml` - Map parsing settings

## Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_map_parsing.py

# Run with coverage
pytest --cov=src --cov-report=html
```

See test files in `tests/` directory.

## Contributing

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Document all public functions

### Testing
- Write tests for new features
- Ensure all tests pass before committing
- Aim for >80% code coverage

### Documentation
- Update relevant documentation when making changes
- Add examples for new features
- Keep API documentation in sync with code

## Support

### Resources
- Main [README](../README.md)
- [Issue Tracker](https://github.com/your-repo/issues)
- [Discussions](https://github.com/your-repo/discussions)

### Getting Help
1. Check documentation
2. Search existing issues
3. Open a new issue with:
   - Clear description of problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information

## Version History

- **v1.0.0** (2025-11-23)
  - Initial release
  - All core features implemented
  - Complete documentation

## License

[Add license information here]

---

**Last Updated**: 2025-11-23

For the most up-to-date information, always refer to the latest version of this documentation.
