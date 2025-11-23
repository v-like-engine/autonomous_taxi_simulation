# Frontend Documentation

Documentation for the Frontend module (Agent 3).

## Overview

The Frontend module provides a blueprint-style research interface for visualization and interaction with the simulation.

## Design Style

**Blueprint Theme:**
- Blueprint paper texture background
- Technical drawing aesthetic
- Clean color scheme (blues, whites, grays)
- Monospace fonts for data
- Engineering-style grid
- Professional controls

## Components

### Flask Application (`app.py`)

Main web server providing the application.

**Features:**
- Serves HTML templates
- Handles file uploads
- Manages simulation state
- Provides REST API
- WebSocket support for real-time updates

**Usage:**
```python
python src/frontend/app.py
# Access at http://localhost:5000
```

### Map Viewer (`map_viewer.js`)

Interactive map display with zoom and pan.

**Features:**
- Load and display map images
- Zoom: Mouse wheel, pinch, buttons
- Pan: Click and drag, arrow keys
- Proportional scaling of all elements
- Maintains alignment during zoom/pan

**API:**
```javascript
const viewer = new MapViewer('canvas-id');
viewer.loadMap(mapData);
viewer.setZoom(2.0);
viewer.pan(dx, dy);
```

### Map Editor (`editor.js`)

Tools for manual map editing.

**Tools:**
- Zone tool: Draw zone polygons
- Road tool: Draw roads
- Crosswalk tool: Mark crosswalks
- Sidewalk tool: Mark sidewalks
- Select tool: Edit existing features
- Delete tool: Remove features

**Usage:**
```javascript
const editor = new MapEditor('canvas-id');
editor.selectTool('zone');
editor.setZoneType('urban');
// Click on canvas to draw
```

### Simulation Controls (`controls.js`)

UI controls for simulation parameters.

**Controls:**
- Start/Pause/Reset buttons
- Speed slider (0.5x - 5x)
- Traffic density slider (0-100%)
- Traffic temperature slider (0.0-1.0)
- Pedestrian density slider (0-100%)
- Visualization toggles

**API:**
```javascript
const controls = new SimulationControls();
controls.onStart(() => { /* Start simulation */ });
controls.onPause(() => { /* Pause simulation */ });
controls.setDensity(50);
```

### Animation Loop (`animation.js`)

Handles rendering at 60 FPS.

**Features:**
- RequestAnimationFrame for smooth animation
- Delta-time based updates
- Efficient canvas rendering
- Layer management (map, zones, vehicles, UI)

**API:**
```javascript
const animator = new Animator('canvas-id');
animator.addLayer('map', renderMap);
animator.addLayer('vehicles', renderVehicles);
animator.start();
```

## Layout Structure

```
┌─────────────────────────────────────────────┐
│  Top Toolbar                                │
│  [Load Map] [Start] [Pause] [Settings]     │
├──────────┬──────────────────────┬───────────┤
│          │                      │           │
│  Left    │   Main Canvas        │  Right    │
│ Sidebar  │   (Map & Simulation) │  Panel    │
│          │                      │           │
│ Controls │                      │ Info &    │
│          │                      │ Metrics   │
│          │                      │           │
├──────────┴──────────────────────┴───────────┤
│  Bottom Status Bar                          │
│  FPS: 60 | Entities: 150 | Time: 05:23     │
└─────────────────────────────────────────────┘
```

## Visualization Features

### Sensor Visualization

**Lidar:**
- Green rays for clear paths
- Red rays for obstacles
- Point cloud display

**Camera:**
- Blue circle for field of view
- Bounding boxes for detected objects
- Confidence scores

**Sonar:**
- Colored arcs around car
- Distance indicators

**GPS:**
- Route line
- Waypoint markers

### Entity Rendering

**Vehicles:**
- Bird's-eye view images
- Rotation based on heading
- Different colors for variety

**Pedestrians:**
- Colored dots
- Movement trails (optional)

**Main Car:**
- Distinct visual (taxi)
- Sensor overlays

## API Endpoints

See [API Documentation](api.md#frontend-rest-api) for complete REST API.

## WebSocket Events

Real-time updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.event === 'simulation_update') {
        updateEntities(data.data);
    } else if (data.event === 'sensor_update') {
        updateSensors(data.data);
    }
};
```

## Performance Optimization

**Canvas Optimization:**
- Dirty region tracking
- Layer caching
- Offscreen rendering for static elements
- RequestAnimationFrame for updates

**Target Performance:**
- 60 FPS rendering
- <16ms frame time
- Support 200+ entities

## Customization

### Custom Theme

Edit `static/css/blueprint.css`:

```css
:root {
    --blueprint-bg: #0f1419;
    --blueprint-grid: #1a2332;
    --blueprint-primary: #4a9eff;
    --blueprint-text: #e3e8ef;
}
```

### Custom Controls

Add custom controls in `static/js/controls.js`:

```javascript
class CustomControl extends SimulationControls {
    addCustomSlider(name, min, max, default) {
        // Implementation
    }
}
```

## Troubleshooting

**Issue: Low FPS**
- Reduce entity count
- Disable sensor visualization
- Lower canvas resolution

**Issue: Zoom/pan misalignment**
- Check canvas transform matrix
- Verify scaling calculations
- Reset transform if needed

**Issue: WebSocket disconnects**
- Check server logs
- Increase timeout
- Implement reconnection logic
