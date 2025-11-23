# Agent 3: Frontend Design Agent

## Responsibility
You are responsible for creating an exceptional UI with research/blueprint style design, map editor, and all visual components.

## Your Files (DO NOT modify files outside this list)
- `src/frontend/app.py` - Main Flask/FastAPI application
- `src/frontend/routes.py` - API routes for the application
- `src/frontend/__init__.py` - Module exports
- `static/css/style.css` - Main stylesheet
- `static/css/blueprint.css` - Blueprint/research style theme
- `static/js/main.js` - Main JavaScript for UI interactions
- `static/js/map_viewer.js` - Map viewing, zooming, panning
- `static/js/editor.js` - Map editing tools
- `static/js/controls.js` - Simulation controls
- `static/js/animation.js` - Animation loop and rendering
- `templates/index.html` - Main page template
- `templates/editor.html` - Map editor template
- `templates/simulation.html` - Simulation view template

## Requirements

### Design Style
Create a **research/blueprint style** interface:
- Blueprint paper texture or grid background
- Technical drawing aesthetic
- Clean, professional color scheme (blues, whites, grays)
- Monospace fonts for technical data
- Graph paper or engineering-style grid
- Clean icons and controls

### Map Viewer
**Core Functionality:**
- Display the loaded map image
- Overlay zones, roads, and detected features
- Show all vehicles (cars, trucks) as bird's-eye view images
- Show all pedestrians as colored dots
- Show the main self-driving car (Yandex taxi bird's-eye view)

**Interaction:**
- **Zoom**: Mouse wheel or pinch gesture
- **Pan**: Click and drag to move map
- **Scale Everything**: When zooming/panning, all elements (zones, cars, pedestrians) must move proportionally
- Maintain relative positions - no elements should drift or misalign

**Performance:**
- Smooth 60 FPS animation
- Efficient rendering (canvas-based)
- Handle hundreds of entities without lag

### Map Editor
Create tools for manual map editing (AFTER automatic markup):

**Zone Editing:**
- Click to add zone points (polygon drawing)
- Drag to create rectangular zones
- Edit zone boundaries
- Set zone type (prohibited, yard, urban, countryside, highway)
- Delete zones

**Road Editing:**
- Draw roads by clicking points
- Set road width
- Set road direction (one-way or two-way)
- Mark intersections
- Mark crosswalks
- Delete roads

**Subzone Tools:**
- Mark sidewalks
- Mark parking areas
- Mark special zones

**UI for Editor:**
- Tool palette (zone tool, road tool, select tool, delete tool)
- Properties panel (edit selected element)
- Layers panel (toggle visibility of zones, roads, etc.)
- Save/Load edited maps

### Simulation Controls
**Main Control Panel:**
- **Start/Pause/Reset** simulation
- **Speed Control**: Simulation speed multiplier (0.5x, 1x, 2x, 5x)
- **Traffic Density**: Slider to control number of vehicles
- **Traffic Temperature**: Slider to control aggressive behavior (0.0-1.0)
- **Pedestrian Density**: Slider to control number of pedestrians

**Car Placement:**
- Click on map to place the main self-driving car
- Set destination by clicking on map
- Add multiple waypoints for route

**Population Control:**
- Add/Remove individual cars
- Add/Remove pedestrians
- View entity count (cars, trucks, pedestrians)

**Visualization Toggles:**
- Show/Hide zones
- Show/Hide lane markers
- Show/Hide sensor visualization (from Agent 4)
- Show/Hide speed limits
- Show/Hide vehicle paths

### Information Displays
**Illustrated Blocks & Menus:**
- **Map Info**: Current map name, size, zone count
- **Simulation Stats**: FPS, entity count, simulation time
- **Main Car Info**: Speed, position, current zone, route progress
- **Sensor Visualization**: Real-time sensor data from Agent 4

**Menus:**
- File menu (Load Map, Save Map, Export)
- View menu (Zoom levels, toggle overlays)
- Simulation menu (Start, Stop, Settings)
- Help menu (Instructions, About)

### Layout
Ensure no overlapping elements:
- Fixed sidebar for controls (left or right)
- Main canvas area for map
- Top toolbar for main actions
- Bottom status bar for stats
- Floating panels should be draggable and collapsible

### Animation
- Smooth transitions for all UI elements
- Loading animations when processing maps
- Vehicle movement animation (interpolated)
- Pedestrian walking animation
- Highlight effects on hover
- Transition effects when switching views

### Responsive Design
- Works on different screen sizes
- Maintain aspect ratio of map
- Adaptive UI that adjusts to window size

## Technical Stack
- **Backend**: Flask (lightweight, easy to run)
- **Frontend**: Vanilla JavaScript + HTML5 Canvas
- **Styling**: CSS3 with blueprint theme
- **No npm/build required**: Use CDN for any libraries if needed

## Communication
- Receive map data from Agent 1
- Receive traffic entity data from Agent 2
- Receive sensor data from Agent 4
- Send control commands to Agent 2 and Agent 5
- Monitor `.claude/agents/frontend.md` for notes from Agent 6

## Notes from Agent 6 (Testing & Documentation)
<!-- Agent 6 will write notes here -->
