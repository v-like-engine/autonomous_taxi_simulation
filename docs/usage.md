# Usage Guide

This guide explains how to use the Autonomous Taxi Simulation system.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Loading a Map](#loading-a-map)
3. [Map Editor](#map-editor)
4. [Running Simulation](#running-simulation)
5. [Placing the Autonomous Car](#placing-the-autonomous-car)
6. [Training the RL Agent](#training-the-rl-agent)
7. [Using Trained Models](#using-trained-models)
8. [Advanced Features](#advanced-features)

## Getting Started

### Starting the Application

```bash
# Local installation
python src/frontend/app.py

# Docker installation
docker-compose up
```

Open your browser and navigate to `http://localhost:5000`

### Interface Overview

The interface features a blueprint-style design with the following components:

- **Top Toolbar**: Main actions (Load Map, Start/Stop, Settings)
- **Left Sidebar**: Simulation controls and settings
- **Main Canvas**: Map display and simulation view
- **Right Panel**: Information displays and metrics
- **Bottom Status Bar**: FPS, entity count, simulation time

## Loading a Map

### Supported Map Formats

- Image formats: PNG, JPG, JPEG, BMP
- Map sources: Yandex Maps, Google Maps screenshots
- Themes: Both light and dark themes supported

### Step-by-Step Map Loading

1. **Click "Load Map"** button in the top toolbar
2. **Select a map image** from your local file system
3. **Wait for automatic processing**:
   - Zone detection (prohibited, yard, urban, countryside, highway)
   - Road detection (lanes, directions, intersections)
   - Crosswalk detection
   - Sidewalk detection

4. **Review detected features**:
   - Zones are highlighted with different colors
   - Roads are marked with lane divisions
   - Intersections are marked with special indicators

### Map Quality Tips

For best results:
- Use high-resolution images (at least 1024x768)
- Ensure roads are clearly visible
- Use maps with good color contrast
- Avoid heavily cluttered maps

## Map Editor

After automatic detection, you can manually refine the map:

### Accessing the Editor

1. Click **"Edit Map"** button
2. The editor panel will appear on the left

### Zone Editing

#### Adding Zones

1. Select **"Zone Tool"** from the tool palette
2. Choose zone type:
   - Prohibited (forests, water, parks)
   - Yard (residential areas, 10 km/h limit)
   - Urban (city areas, 60 km/h limit)
   - Countryside (90 km/h limit)
   - Highway (110 km/h limit)

3. Click on the map to define polygon points
4. Double-click or press Enter to complete the zone
5. Adjust speed limits in the properties panel

#### Editing Zones

1. Select **"Select Tool"**
2. Click on a zone to select it
3. Drag points to reshape
4. Modify properties in the properties panel
5. Click **"Delete"** to remove

### Road Editing

#### Drawing Roads

1. Select **"Road Tool"**
2. Click to place road waypoints
3. Set road properties:
   - Width (affects number of lanes)
   - Direction (one-way or two-way)
   - Speed limit

4. Double-click to finish the road

#### Editing Roads

1. Use **"Select Tool"** to click on a road
2. Modify width, direction, or other properties
3. Add or remove waypoints by dragging

### Marking Special Features

#### Crosswalks

1. Select **"Crosswalk Tool"**
2. Click start and end points across a road
3. Crosswalk will be created

#### Sidewalks

1. Select **"Sidewalk Tool"**
2. Draw along roads where pedestrians should walk
3. Set width in properties panel

#### Parking Areas

1. Select **"Parking Tool"**
2. Draw polygon for parking area
3. Set capacity and availability

### Saving Edited Maps

1. Click **"Save Map"** to save your changes
2. Choose format:
   - `.json` - Map data only (recommended)
   - `.png` - Visual representation
   - Both

## Running Simulation

### Starting the Simulation

1. Ensure a map is loaded
2. Configure simulation parameters (see below)
3. Click **"Start Simulation"**
4. Traffic and pedestrians will begin appearing

### Simulation Controls

#### Traffic Density

- **Slider range**: 0-100%
- **Low (0-30%)**: Sparse traffic, easy navigation
- **Medium (30-70%)**: Normal traffic conditions
- **High (70-100%)**: Heavy traffic, congestion possible

#### Traffic Temperature

Controls driver behavior aggressiveness:
- **Low (0.0-0.3)**: Careful drivers, strict rule following
- **Medium (0.3-0.7)**: Normal drivers, occasional violations
- **High (0.7-1.0)**: Aggressive drivers, frequent violations

#### Pedestrian Density

- **Slider range**: 0-100%
- Controls number of pedestrians on sidewalks

#### Simulation Speed

- **0.5x**: Slow motion (for detailed observation)
- **1x**: Real-time
- **2x**: Fast forward
- **5x**: Very fast (for training)

### Pause and Resume

- Click **"Pause"** to freeze simulation
- Click **"Resume"** to continue
- Click **"Reset"** to clear all entities and restart

### Visualization Toggles

Toggle visibility of various elements:
- ☑ **Show Zones**: Display zone boundaries and colors
- ☑ **Show Roads**: Display road lanes and directions
- ☑ **Show Sensors**: Display sensor data visualization
- ☑ **Show Paths**: Display vehicle planned paths
- ☑ **Show Speed Limits**: Display speed limit indicators

## Placing the Autonomous Car

### Manual Placement

1. Click **"Place Car"** button
2. Click on a road location on the map
3. The autonomous taxi will appear at that location
4. Car orientation will match road direction

### Setting Destination

1. With car placed, click **"Set Destination"**
2. Click target location on the map
3. Route will be calculated and displayed
4. GPS will guide the car along the route

### Adding Waypoints

For complex routes:
1. Click **"Add Waypoint"**
2. Click on intermediate locations
3. Car will navigate through waypoints in sequence
4. Right-click a waypoint to remove it

## Training the RL Agent

### Starting Training

#### Via UI

1. Place the autonomous car
2. Set a destination
3. Open **Training Panel**
4. Configure training parameters:
   - Episodes: 1000+ recommended
   - Learning rate: 1e-4 to 1e-3
   - Batch size: 64-256
5. Click **"Start Training"**

#### Via Command Line

```bash
# Basic training
python src/rl_agent/training.py

# With custom parameters
python src/rl_agent/training.py \
  --episodes 2000 \
  --batch-size 128 \
  --learning-rate 0.0001 \
  --save-interval 100
```

### Monitoring Training

Watch the training metrics:
- **Episode Reward**: Should increase over time
- **Success Rate**: Percentage of successful navigations
- **Collision Rate**: Should decrease to near zero
- **Average Speed**: Should stabilize
- **Training Loss**: Should decrease

### Training Parameters

#### Episodes

- **Recommended**: 1000-5000 episodes
- More episodes = better learning but longer training time

#### Batch Size

- **Small (32-64)**: More stable but slower
- **Medium (128-256)**: Balanced
- **Large (512+)**: Faster but less stable

#### Learning Rate

- **Low (1e-5 to 1e-4)**: Slow but stable learning
- **Medium (1e-4 to 1e-3)**: Recommended
- **High (>1e-3)**: Fast but may be unstable

### Saving Models

Models are automatically saved:
- Every N episodes (configurable)
- When new best performance is achieved
- At training completion

Models saved to: `models/`

## Using Trained Models

### Loading a Trained Model

1. Click **"Load Model"** in the control panel
2. Select a model file from `models/` directory
3. Model will be loaded and ready for inference

### Running Inference

1. Load a trained model
2. Place the car and set destination
3. Click **"Auto Drive"**
4. The RL agent will control the car
5. Watch as it navigates to the destination

### Evaluating Performance

Monitor these metrics:
- **Success Rate**: Did it reach the destination?
- **Collision Events**: Any collisions during navigation?
- **Traffic Violations**: Speeding, wrong direction, etc.
- **Time to Destination**: How efficient was the route?
- **Smoothness**: How smooth was the driving?

### Comparing Models

1. Load different models
2. Run on same map with same destination
3. Compare performance metrics
4. Select best model for deployment

## Advanced Features

### Camera Controls

#### Zooming

- **Mouse wheel**: Zoom in/out
- **Pinch gesture**: On touch screens
- **Buttons**: + and - buttons in toolbar
- All elements scale proportionally

#### Panning

- **Click and drag**: Move around the map
- **Arrow keys**: Pan in directions
- **Double-click**: Center on location

### Sensor Visualization

#### Lidar Visualization

- Green rays: Clear path
- Red rays: Obstacle detected
- Ray length shows detection distance

#### Camera Visualization

- Blue circle: Field of view
- Yellow boxes: Detected vehicles
- Orange boxes: Detected pedestrians
- Confidence shown as box opacity

#### Sonar Visualization

- Colored arcs around car
- Green: Safe distance
- Yellow: Caution
- Red: Very close obstacle

#### GPS Visualization

- Blue line: Planned route
- Purple markers: Waypoints
- Current position with GPS noise shown

### Real-time Metrics

View in the metrics panel:
- **Main Car**:
  - Speed (km/h)
  - Position (x, y)
  - Current zone
  - Distance to destination

- **Simulation**:
  - FPS (frames per second)
  - Entity count
  - Simulation time

- **RL Agent**:
  - Current reward
  - Cumulative reward
  - Actions taken
  - Violations count

### Exporting Data

#### Export Map

1. File → Export Map
2. Choose format (JSON, PNG, or both)
3. Save to local file

#### Export Training Data

1. Training → Export Data
2. Select metrics to export
3. Format: CSV or JSON
4. Useful for analysis in external tools

#### Export Video

1. Simulation → Record
2. Run simulation
3. Stop recording
4. Video saved to `data/recordings/`

### Keyboard Shortcuts

- **Space**: Pause/Resume simulation
- **R**: Reset simulation
- **M**: Toggle map display
- **S**: Toggle sensor visualization
- **+/-**: Zoom in/out
- **Arrow keys**: Pan map
- **Ctrl+S**: Save map
- **Ctrl+O**: Open/Load map
- **Esc**: Cancel current operation

### Configuration Files

Advanced users can edit configuration files:

#### `config/simulation.yaml`

```yaml
traffic:
  density: 50
  temperature: 0.5
  spawn_rate: 0.1

pedestrians:
  density: 30
  walking_speed: 1.5

physics:
  gravity: 9.81
  friction: 0.7
```

#### `config/rl_agent.yaml`

```yaml
training:
  episodes: 1000
  batch_size: 128
  learning_rate: 0.0001
  gamma: 0.99

model:
  hidden_layers: [256, 256, 128]
  activation: relu
```

## Tips and Best Practices

### For Best Performance

1. **Start simple**: Use simple maps first
2. **Low traffic initially**: Begin with low traffic density
3. **Train gradually**: Start with short routes, then longer
4. **Monitor metrics**: Watch for anomalies
5. **Save frequently**: Save good models regularly

### For Best Results

1. **Quality maps**: Use high-quality map images
2. **Verify detection**: Check automatic zone/road detection
3. **Balance parameters**: Don't set extreme values
4. **Adequate training**: Allow sufficient training time
5. **Test thoroughly**: Test in various scenarios

### Common Mistakes to Avoid

1. ❌ Loading low-quality maps
2. ❌ Training with too few episodes
3. ❌ Extreme traffic density (100%) for initial training
4. ❌ Not verifying automatic detection results
5. ❌ Overwriting good models

## Troubleshooting

### Simulation runs slowly

- Reduce traffic/pedestrian density
- Disable sensor visualization
- Lower simulation speed
- Close other applications

### Car won't move

- Check if simulation is paused
- Verify destination is reachable
- Check if car is on a valid road
- Reload the model

### Frequent collisions

- Model needs more training
- Traffic density too high
- Reduce traffic temperature
- Check sensor configurations

### Route not found

- Destination may be in prohibited zone
- No connected road path
- Try different destination
- Check road network connectivity

## Next Steps

- Explore [Architecture Documentation](architecture.md) to understand the system
- Read [API Documentation](api.md) for integration
- Check component-specific documentation for details

---

**Happy Simulating!** Enjoy training your autonomous taxi.
