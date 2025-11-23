# Autonomous Taxi Simulation - Frontend

A professional Flask-based web application with blueprint/research style UI for visualizing and controlling the autonomous taxi simulation.

## Features

### 🎨 Blueprint-Style Design
- Research/technical drawing aesthetic
- Blueprint paper texture and grid background
- Professional color scheme (blues, whites, grays)
- Monospace fonts for technical data
- Clean icons and controls

### 🗺️ Map Viewer
- **Display**: Loaded map image with overlay zones, roads, and features
- **Zoom**: Mouse wheel or pinch gesture (0.1x to 5.0x)
- **Pan**: Click and drag to move around the map
- **Scale Everything**: All elements (zones, cars, pedestrians) move proportionally
- **Maintain Positions**: No element drift or misalignment

### ✏️ Map Editor
- **Zone Tools**: Draw zones (rectangular or polygon), set zone types
- **Road Tools**: Draw roads with customizable width and direction
- **Subzone Tools**: Mark sidewalks, parking areas, special zones
- **Intersection Tools**: Mark intersections and crosswalks
- **Edit Tools**: Select, modify, and delete elements
- **Undo/Redo**: Full history support

### 🎮 Simulation Controls
- **Main Controls**: Start, Pause, Reset simulation
- **Speed Control**: Adjust simulation speed (0.1x to 5.0x)
- **Traffic Settings**: Control density and aggressiveness
- **Pedestrian Control**: Adjust pedestrian density
- **Car Placement**: Click to place main car and set destinations
- **Waypoints**: Add multiple waypoints for complex routes

### 📊 Information Displays
- **Map Info**: Name, size, zone count, road count
- **Simulation Stats**: FPS, entity count, simulation time
- **Main Car Info**: Speed, position, current zone, route progress
- **Sensor Visualization**: Real-time sensor data display

### 🎬 60 FPS Animation
- Smooth rendering loop using requestAnimationFrame
- Efficient canvas-based rendering
- Handles hundreds of entities without lag
- Interpolated movement for smooth transitions
- Vehicle bird's-eye view rendering
- Pedestrian dot visualization

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- Flask >= 2.0.0
- flask-socketio >= 5.1.0
- python-socketio >= 5.4.0

### 2. Run the Application

```bash
python3 run_frontend.py
```

Or directly:

```bash
python3 -m src.frontend.app
```

### 3. Open in Browser

Navigate to: http://localhost:5000

## Application Structure

```
autonomous_taxi_simulation/
├── src/frontend/
│   ├── __init__.py          # Module exports
│   ├── app.py               # Main Flask application
│   └── routes.py            # API routes
├── static/
│   ├── css/
│   │   ├── blueprint.css    # Blueprint theme styles
│   │   └── style.css        # Main layout styles
│   ├── js/
│   │   ├── main.js          # Main app coordinator
│   │   ├── map_viewer.js    # Map viewing with zoom/pan
│   │   ├── editor.js        # Map editing tools
│   │   ├── controls.js      # Simulation controls
│   │   └── animation.js     # 60 FPS animation system
│   └── images/              # Static images
├── templates/
│   ├── index.html           # Main control page
│   ├── editor.html          # Map editor page
│   └── simulation.html      # Full-screen simulation view
├── data/maps/               # Map storage
└── run_frontend.py          # Launcher script
```

## Pages

### Main Page (/)
- Full control center with sidebars
- Left sidebar: Simulation controls, layer toggles, statistics
- Center: Map canvas with zoom controls
- Right sidebar: Main car status, placement controls, sensor data
- Top toolbar: File, View, Help menus

### Editor Page (/editor)
- Map editing interface
- Left sidebar: Tool palette, properties panels
- Center: Editor canvas
- Tools: Zone, Road, Polygon, Sidewalk, Parking, Intersection, Crosswalk, Delete

### Simulation Page (/simulation)
- Full-screen simulation view
- Floating draggable panels for stats and controls
- Minimal UI for maximum visualization space

## Controls

### Mouse Controls
- **Zoom**: Mouse wheel up/down
- **Pan**: Click and drag
- **Place Elements**: Click on map (when tool is active)

### Keyboard Shortcuts
- **Space**: Start/Pause simulation
- **+ / -**: Zoom in/out
- **0**: Reset zoom
- **F**: Fit map to screen
- **Ctrl+S**: Save map
- **Ctrl+Z**: Undo (in editor)
- **Escape**: Cancel current operation
- **Delete**: Delete selected element
- **H or ?**: Show help

## API Endpoints

### Map Management
- `GET /api/maps/list` - List all available maps
- `GET /api/map/load/<name>` - Load a specific map
- `GET /api/map/image/<name>` - Get map image
- `POST /api/map/save` - Save map data

### Simulation Control
- `GET /api/simulation/state` - Get current simulation state
- `POST /api/simulation/config` - Update simulation configuration
- `GET /api/entities` - Get current entity data

### Health Check
- `GET /api/health` - Health check endpoint

## WebSocket Events

### Client → Server
- `start_simulation` - Start the simulation
- `pause_simulation` - Pause the simulation
- `reset_simulation` - Reset the simulation
- `update_speed` - Update simulation speed
- `update_traffic_density` - Update traffic density
- `update_traffic_temperature` - Update traffic aggressiveness
- `update_pedestrian_density` - Update pedestrian density
- `place_main_car` - Place the main car on map
- `set_destination` - Set destination for main car
- `add_waypoint` - Add waypoint to route

### Server → Client
- `connect` - Client connected
- `disconnect` - Client disconnected
- `simulation_state` - Simulation state update
- `entity_update` - Entity position updates

## Map Data Format

Maps are stored as JSON files with the following structure:

```json
{
  "name": "map_name",
  "width": 1000,
  "height": 800,
  "zones": [
    {
      "id": "zone_1",
      "type": "urban|highway|yard|countryside|prohibited",
      "name": "Zone Name",
      "points": [{"x": 0, "y": 0}, ...]
    }
  ],
  "roads": [
    {
      "id": "road_1",
      "points": [{"x": 0, "y": 0}, ...],
      "width": 40,
      "direction": "two-way|one-way",
      "speedLimit": 60
    }
  ],
  "subzones": [
    {
      "id": "subzone_1",
      "type": "sidewalk|parking",
      "points": [{"x": 0, "y": 0}, ...]
    }
  ]
}
```

## Customization

### Colors
Edit `static/css/blueprint.css` to customize the color scheme. Key CSS variables:
- `--blueprint-bg`: Background color
- `--blueprint-accent`: Accent/highlight color
- `--blueprint-text`: Text color

### Layout
Edit `static/css/style.css` to modify layout and component sizing.

### Animation
Edit `static/js/animation.js` to customize entity rendering and animation behavior.

## Performance

- **Target FPS**: 60 FPS
- **Rendering**: HTML5 Canvas with hardware acceleration
- **Entity Limit**: Tested with 500+ entities
- **Optimization**:
  - Efficient coordinate transformations
  - Minimal DOM manipulation
  - Canvas-based rendering
  - RequestAnimationFrame for smooth animation

## Browser Support

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ⚠️ Limited (touch controls work, but desktop recommended)

## Troubleshooting

### Map doesn't load
- Check that map files exist in `data/maps/`
- Verify JSON format is valid
- Check browser console for errors

### Low FPS
- Reduce number of entities
- Disable sensor visualization
- Close other browser tabs
- Use a modern browser

### WebSocket connection fails
- Check that Flask-SocketIO is installed
- Verify port 5000 is available
- Check firewall settings

### Canvas is blank
- Check that map image exists
- Verify canvas element is present in DOM
- Check browser console for errors

## Development

### Adding New Features
1. Backend: Add routes in `src/frontend/routes.py`
2. Frontend: Add JavaScript in appropriate module
3. Styling: Update CSS files as needed
4. Templates: Modify HTML templates

### Testing
```bash
# Run syntax check
python3 -m py_compile src/frontend/*.py

# Start development server
python3 run_frontend.py
```

## Integration

The frontend integrates with other simulation components:
- **Agent 1 (Map Parsing)**: Receives parsed map data
- **Agent 2 (Traffic Simulation)**: Sends/receives entity data
- **Agent 4 (Sensors)**: Displays sensor visualization
- **Agent 5 (RL Agent)**: Visualizes AI decision-making

## Technical Stack

- **Backend**: Flask 2.0+, Flask-SocketIO 5.1+
- **Frontend**: Vanilla JavaScript (ES6+), HTML5 Canvas
- **Styling**: CSS3 with custom blueprint theme
- **Real-time**: WebSocket (Socket.IO)
- **No Build Required**: Uses CDN for dependencies

## License

Part of the Autonomous Taxi Simulation project.

## Support

For issues or questions, check the main project documentation or the `.claude/agents/frontend.md` file.
