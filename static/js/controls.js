/**
 * Simulation Controls - Handles all simulation control UI and interactions
 */

class SimulationControls {
    constructor() {
        this.socket = null;
        this.isRunning = false;
        this.speed = 1.0;
        this.trafficDensity = 0.5;
        this.trafficTemperature = 0.5;
        this.pedestrianDensity = 0.3;

        // Modes
        this.currentMode = 'viewing'; // viewing, placing_car, setting_destination, adding_waypoints

        this.initSocketIO();
        this.updateUIState();
    }

    initSocketIO() {
        // Connect to WebSocket server
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to simulation server');
            this.updateStatus('Connected', 'success');
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from simulation server');
            this.updateStatus('Disconnected', 'error');
        });

        this.socket.on('simulation_state', (state) => {
            this.handleSimulationStateUpdate(state);
        });

        this.socket.on('entity_update', (data) => {
            this.handleEntityUpdate(data);
        });
    }

    handleSimulationStateUpdate(state) {
        this.isRunning = state.is_running;
        this.speed = state.speed;
        this.trafficDensity = state.traffic_density;
        this.trafficTemperature = state.traffic_temperature;
        this.pedestrianDensity = state.pedestrian_density;

        this.updateUIState();
    }

    handleEntityUpdate(data) {
        if (animationSystem) {
            animationSystem.updateEntities(data);
        }
        this.updateEntityCounts(data);
    }

    updateUIState() {
        // Update button states
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');

        if (startBtn) startBtn.disabled = this.isRunning;
        if (pauseBtn) pauseBtn.disabled = !this.isRunning;

        // Update status
        if (this.isRunning) {
            this.updateStatus('Running', 'success');
        } else {
            this.updateStatus('Paused', 'warning');
        }
    }

    updateStatus(text, level = 'info') {
        const statusElements = ['statusText', 'editorStatusText', 'simStatusText'];
        const indicatorElements = ['statusIndicator', 'editorStatus', 'simStatusIndicator'];

        statusElements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = text;
        });

        indicatorElements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) {
                elem.className = 'status-indicator';
                if (level === 'success') elem.classList.add('');
                else if (level === 'warning') elem.classList.add('warning');
                else if (level === 'error') elem.classList.add('error');
            }
        });
    }

    updateEntityCounts(data) {
        const vehicleCount = (data.entities && data.entities.filter(e => e.type !== 'pedestrian').length) || 0;
        const pedestrianCount = (data.entities && data.entities.filter(e => e.type === 'pedestrian').length) || 0;

        const vehicleElements = ['vehicleCount', 'simVehicleCount'];
        const pedestrianElements = ['pedestrianCount', 'simPedestrianCount'];

        vehicleElements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = vehicleCount;
        });

        pedestrianElements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = pedestrianCount;
        });
    }
}

// Global controls instance
let simulationControls = null;

// Control functions called from HTML
function startSimulation() {
    if (simulationControls && simulationControls.socket) {
        simulationControls.socket.emit('start_simulation');
        simulationControls.isRunning = true;
        simulationControls.updateUIState();
    }
}

function pauseSimulation() {
    if (simulationControls && simulationControls.socket) {
        simulationControls.socket.emit('pause_simulation');
        simulationControls.isRunning = false;
        simulationControls.updateUIState();
    }
}

function resetSimulation() {
    if (simulationControls && simulationControls.socket) {
        simulationControls.socket.emit('reset_simulation');
        simulationControls.isRunning = false;
        simulationControls.updateUIState();
    }

    if (animationSystem) {
        animationSystem.vehicles = [];
        animationSystem.pedestrians = [];
        animationSystem.mainCar = null;
    }
}

function updateSpeed(value) {
    const speed = parseFloat(value);
    if (simulationControls && simulationControls.socket) {
        simulationControls.socket.emit('update_speed', { speed: speed });
        simulationControls.speed = speed;
    }

    // Update display
    const speedElements = ['speedValue', 'simSpeedValue', 'simSpeedDisplay'];
    speedElements.forEach(id => {
        const elem = document.getElementById(id);
        if (elem) elem.textContent = `${speed.toFixed(1)}x`;
    });
}

function updateSimSpeed(value) {
    updateSpeed(value);
}

function updateDensity(value) {
    const density = parseFloat(value);
    if (simulationControls && simulationControls.socket) {
        simulationControls.socket.emit('update_traffic_density', { density: density });
        simulationControls.trafficDensity = density;
    }

    // Update display
    const elem = document.getElementById('densityValue');
    if (elem) elem.textContent = `${Math.round(density * 100)}%`;
}

function updateTemperature(value) {
    const temperature = parseFloat(value);
    if (simulationControls && simulationControls.socket) {
        simulationControls.socket.emit('update_traffic_temperature', { temperature: temperature });
        simulationControls.trafficTemperature = temperature;
    }

    // Update display
    const elem = document.getElementById('temperatureValue');
    if (elem) elem.textContent = `${Math.round(temperature * 100)}%`;
}

function updatePedestrianDensity(value) {
    const density = parseFloat(value);
    if (simulationControls && simulationControls.socket) {
        simulationControls.socket.emit('update_pedestrian_density', { density: density });
        simulationControls.pedestrianDensity = density;
    }

    // Update display
    const elem = document.getElementById('pedestrianValue');
    if (elem) elem.textContent = `${Math.round(density * 100)}%`;
}

function toggleLayer(layerName, visible) {
    if (mapViewer) {
        mapViewer.toggleLayer(layerName, visible);
    }

    if (animationSystem) {
        if (layerName === 'paths') animationSystem.showPaths = visible;
        if (layerName === 'sensors') animationSystem.showSensors = visible;
    }
}

function toggleSimLayer(layerName, visible) {
    toggleLayer(layerName, visible);
}

// Car placement functions
let placementMode = null;

function enableCarPlacement() {
    placementMode = 'car';
    if (simulationControls) {
        simulationControls.currentMode = 'placing_car';
        simulationControls.updateStatus('Click on map to place car', 'info');
    }

    // Add click handler
    if (mapViewer && mapViewer.canvas) {
        mapViewer.canvas.style.cursor = 'crosshair';
        mapViewer.canvas.addEventListener('click', handleMapClick);
    }
}

function enableDestinationSet() {
    placementMode = 'destination';
    if (simulationControls) {
        simulationControls.currentMode = 'setting_destination';
        simulationControls.updateStatus('Click on map to set destination', 'info');
    }

    if (mapViewer && mapViewer.canvas) {
        mapViewer.canvas.style.cursor = 'crosshair';
        mapViewer.canvas.addEventListener('click', handleMapClick);
    }
}

function enableWaypointMode() {
    placementMode = 'waypoint';
    if (simulationControls) {
        simulationControls.currentMode = 'adding_waypoints';
        simulationControls.updateStatus('Click on map to add waypoints (click again to finish)', 'info');
    }

    if (mapViewer && mapViewer.canvas) {
        mapViewer.canvas.style.cursor = 'crosshair';
        mapViewer.canvas.addEventListener('click', handleMapClick);
    }
}

function handleMapClick(e) {
    if (!placementMode || !mapViewer) return;

    const rect = mapViewer.canvas.getBoundingClientRect();
    const screenX = e.clientX - rect.left;
    const screenY = e.clientY - rect.top;
    const worldPos = mapViewer.screenToWorld(screenX, screenY);

    if (placementMode === 'car') {
        // Place main car
        if (simulationControls && simulationControls.socket) {
            simulationControls.socket.emit('place_main_car', { x: worldPos.x, y: worldPos.y });
        }

        if (animationSystem) {
            animationSystem.setMainCar({ x: worldPos.x, y: worldPos.y });
        }

        // Exit placement mode
        placementMode = null;
        mapViewer.canvas.style.cursor = 'grab';
        mapViewer.canvas.removeEventListener('click', handleMapClick);
        if (simulationControls) {
            simulationControls.currentMode = 'viewing';
            simulationControls.updateStatus('Car placed', 'success');
        }
    } else if (placementMode === 'destination') {
        // Set destination
        if (simulationControls && simulationControls.socket) {
            simulationControls.socket.emit('set_destination', { x: worldPos.x, y: worldPos.y });
        }

        if (animationSystem) {
            animationSystem.setDestination({ x: worldPos.x, y: worldPos.y });
        }

        // Exit placement mode
        placementMode = null;
        mapViewer.canvas.style.cursor = 'grab';
        mapViewer.canvas.removeEventListener('click', handleMapClick);
        if (simulationControls) {
            simulationControls.currentMode = 'viewing';
            simulationControls.updateStatus('Destination set', 'success');
        }
    } else if (placementMode === 'waypoint') {
        // Add waypoint
        if (simulationControls && simulationControls.socket) {
            simulationControls.socket.emit('add_waypoint', { x: worldPos.x, y: worldPos.y });
        }

        if (animationSystem) {
            animationSystem.addWaypoint({ x: worldPos.x, y: worldPos.y });
        }

        // Stay in waypoint mode until manually exited
        if (simulationControls) {
            simulationControls.updateStatus('Waypoint added (click to add more, or select another tool)', 'success');
        }
    }
}

function clearRoute() {
    if (animationSystem) {
        animationSystem.clearRoute();
    }

    if (simulationControls) {
        simulationControls.updateStatus('Route cleared', 'info');
    }
}

// Population control
function addVehicle() {
    if (animationSystem && mapViewer) {
        const width = mapViewer.mapWidth;
        const height = mapViewer.mapHeight;

        const newVehicle = {
            id: `vehicle_${Date.now()}`,
            type: Math.random() > 0.8 ? 'truck' : 'car',
            position: {
                x: Math.random() * width,
                y: Math.random() * height
            },
            angle: Math.random() * Math.PI * 2,
            speed: Math.random() * 60 + 20
        };

        animationSystem.vehicles.push(newVehicle);
    }
}

function removeVehicle() {
    if (animationSystem && animationSystem.vehicles.length > 0) {
        animationSystem.vehicles.pop();
    }
}

function addPedestrian() {
    if (animationSystem && mapViewer) {
        const width = mapViewer.mapWidth;
        const height = mapViewer.mapHeight;
        const vx = (Math.random() - 0.5) * 2;
        const vy = (Math.random() - 0.5) * 2;

        const newPedestrian = {
            id: `pedestrian_${Date.now()}`,
            position: {
                x: Math.random() * width,
                y: Math.random() * height
            },
            velocity: { x: vx, y: vy }
        };

        animationSystem.pedestrians.push(newPedestrian);
    }
}

function removePedestrian() {
    if (animationSystem && animationSystem.pedestrians.length > 0) {
        animationSystem.pedestrians.pop();
    }
}

// Initialize controls when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    simulationControls = new SimulationControls();

    // Setup dropdown menus
    setupDropdowns();
});

function setupDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const btn = dropdown.querySelector('.blueprint-btn');
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.toggle('active');
            });
        }
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', () => {
        dropdowns.forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    });
}

// Map loading
function loadMap() {
    openModal('loadMapModal');
    fetchMapList();
}

function fetchMapList() {
    fetch('/api/maps/list')
        .then(response => response.json())
        .then(data => {
            displayMapList(data.maps);
        })
        .catch(error => {
            console.error('Error fetching map list:', error);
            const mapList = document.getElementById('mapList');
            if (mapList) {
                mapList.innerHTML = '<p class="text-center" style="color: var(--danger-color);">Error loading maps</p>';
            }
        });
}

function displayMapList(maps) {
    const mapList = document.getElementById('mapList');
    if (!mapList) return;

    if (maps.length === 0) {
        mapList.innerHTML = '<p class="text-center">No maps found</p>';
        return;
    }

    let html = '<div style="display: flex; flex-direction: column; gap: 8px;">';
    maps.forEach(map => {
        html += `
            <button class="blueprint-btn" onclick="selectMap('${map.name}')" style="width: 100%; text-align: left;">
                ${map.name}
            </button>
        `;
    });
    html += '</div>';

    mapList.innerHTML = html;
}

function selectMap(mapName) {
    closeModal('loadMapModal');
    if (mapViewer) {
        mapViewer.loadMap(mapName).then(mapData => {
            console.log('Map loaded:', mapName);
            if (simulationControls) {
                simulationControls.updateStatus(`Loaded: ${mapName}`, 'success');
            }

            // Update map info display
            updateMapInfo(mapName, mapData);

            // Initialize animation system if not already
            if (!animationSystem) {
                initAnimationSystem();
            }
        }).catch(error => {
            console.error('Error loading map:', error);
            if (simulationControls) {
                simulationControls.updateStatus('Error loading map', 'error');
            }
        });
    }
}

function updateMapInfo(name, mapData) {
    const mapNameElem = document.getElementById('mapName');
    const mapSizeElem = document.getElementById('mapSize');
    const zoneCountElem = document.getElementById('zoneCount');
    const roadCountElem = document.getElementById('roadCount');

    if (mapNameElem) mapNameElem.textContent = name;
    if (mapSizeElem && mapData.width && mapData.height) {
        mapSizeElem.textContent = `${mapData.width}×${mapData.height}`;
    }
    if (zoneCountElem) {
        zoneCountElem.textContent = mapData.zones ? mapData.zones.length : 0;
    }
    if (roadCountElem) {
        roadCountElem.textContent = mapData.roads ? mapData.roads.length : 0;
    }
}

function saveMap() {
    if (!mapViewer || !mapViewer.mapData) {
        alert('No map loaded to save');
        return;
    }

    fetch('/api/map/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(mapViewer.mapData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (simulationControls) {
                    simulationControls.updateStatus('Map saved', 'success');
                }
            } else {
                alert('Error saving map: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error saving map:', error);
            alert('Error saving map');
        });
}

function exportData() {
    if (!mapViewer || !mapViewer.mapData) {
        alert('No map loaded to export');
        return;
    }

    const dataStr = JSON.stringify(mapViewer.mapData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${mapViewer.mapData.name || 'map'}_export.json`;
    link.click();
    URL.revokeObjectURL(url);
}

// Modal controls
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}

// Instructions and About
function showInstructions() {
    alert('Autonomous Taxi Simulation Instructions:\n\n' +
          '1. Load a map from File menu\n' +
          '2. Use mouse wheel to zoom, drag to pan\n' +
          '3. Place the main car by clicking "Place Main Car"\n' +
          '4. Set destination and waypoints\n' +
          '5. Adjust simulation parameters\n' +
          '6. Click Start to begin simulation');
}

function showAbout() {
    alert('Autonomous Taxi Simulation\n\n' +
          'A research-grade simulation platform for autonomous vehicle testing.\n\n' +
          'Features blueprint-style UI, real-time visualization, and comprehensive controls.');
}
