/**
 * Main application coordinator
 * Handles initialization and coordination between all modules
 */

class Application {
    constructor() {
        this.initialized = false;
        this.currentPage = this.detectPage();
        this.simTime = 0;
        this.simTimeInterval = null;

        this.init();
    }

    detectPage() {
        if (document.getElementById('editor-canvas')) return 'editor';
        if (document.getElementById('simulation-canvas')) return 'simulation';
        return 'main';
    }

    async init() {
        console.log('Initializing Autonomous Taxi Simulation...');
        console.log('Current page:', this.currentPage);

        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initModules());
        } else {
            this.initModules();
        }
    }

    initModules() {
        // Initialize map viewer (already initialized in map_viewer.js)
        if (mapViewer) {
            console.log('Map viewer initialized');
        }

        // Initialize animation system
        if (this.currentPage === 'main' || this.currentPage === 'simulation') {
            setTimeout(() => {
                initAnimationSystem();
                console.log('Animation system initialized');
            }, 500);
        }

        // Initialize simulation controls (already initialized in controls.js)
        if (simulationControls) {
            console.log('Simulation controls initialized');
        }

        // Page-specific initialization
        if (this.currentPage === 'main') {
            this.initMainPage();
        } else if (this.currentPage === 'editor') {
            this.initEditorPage();
        } else if (this.currentPage === 'simulation') {
            this.initSimulationPage();
        }

        this.initialized = true;
        console.log('Application initialized successfully');
    }

    initMainPage() {
        console.log('Initializing main page...');

        // Auto-load demo map for testing
        setTimeout(() => {
            this.loadDemoData();
        }, 1000);

        // Start simulation time counter
        this.startSimulationTime();
    }

    initEditorPage() {
        console.log('Initializing editor page...');

        // Auto-load a map if available
        setTimeout(() => {
            this.autoLoadMapForEditor();
        }, 1000);
    }

    initSimulationPage() {
        console.log('Initializing simulation page...');

        // Auto-load demo data
        setTimeout(() => {
            this.loadDemoData();
        }, 1000);

        // Start simulation time counter
        this.startSimulationTime();
    }

    async loadDemoData() {
        console.log('Loading demo data...');

        // Try to load first available map
        try {
            const response = await fetch('/api/maps/list');
            const data = await response.json();

            if (data.maps && data.maps.length > 0) {
                const firstMap = data.maps[0].name;
                console.log('Loading map:', firstMap);
                await this.loadMapByName(firstMap);
            } else {
                console.log('No maps found, creating demo visualization');
                this.createDemoVisualization();
            }
        } catch (error) {
            console.error('Error loading maps:', error);
            this.createDemoVisualization();
        }
    }

    async loadMapByName(mapName) {
        if (mapViewer) {
            try {
                await mapViewer.loadMap(mapName);
                console.log('Map loaded successfully:', mapName);

                // Update map info
                if (mapViewer.mapData) {
                    updateMapInfo(mapName, mapViewer.mapData);
                }

                // Initialize animation system if not already done
                if (!animationSystem) {
                    initAnimationSystem();
                }

                // Generate demo entities for testing
                if (animationSystem) {
                    setTimeout(() => {
                        animationSystem.generateDemoEntities(10);
                        console.log('Demo entities generated');
                    }, 500);
                }

                // If on editor page, load data into editor
                if (this.currentPage === 'editor' && mapEditor && mapViewer.mapData) {
                    mapEditor.loadFromMapData(mapViewer.mapData);
                }

            } catch (error) {
                console.error('Error loading map:', error);
            }
        }
    }

    async autoLoadMapForEditor() {
        // Try to load first available map for editing
        try {
            const response = await fetch('/api/maps/list');
            const data = await response.json();

            if (data.maps && data.maps.length > 0) {
                const firstMap = data.maps[0].name;
                await this.loadMapByName(firstMap);
            }
        } catch (error) {
            console.error('Error auto-loading map for editor:', error);
        }
    }

    createDemoVisualization() {
        console.log('Creating demo visualization without map...');

        // Create a simple demo canvas
        if (mapViewer) {
            mapViewer.mapWidth = 1000;
            mapViewer.mapHeight = 800;

            // Create demo map data
            mapViewer.mapData = {
                name: 'Demo Map',
                width: 1000,
                height: 800,
                zones: [
                    {
                        type: 'urban',
                        name: 'Urban Zone',
                        points: [
                            { x: 100, y: 100 },
                            { x: 400, y: 100 },
                            { x: 400, y: 400 },
                            { x: 100, y: 400 }
                        ]
                    },
                    {
                        type: 'highway',
                        name: 'Highway Zone',
                        points: [
                            { x: 500, y: 100 },
                            { x: 900, y: 100 },
                            { x: 900, y: 700 },
                            { x: 500, y: 700 }
                        ]
                    }
                ],
                roads: [
                    {
                        points: [
                            { x: 50, y: 400 },
                            { x: 950, y: 400 }
                        ],
                        width: 40,
                        direction: 'two-way'
                    },
                    {
                        points: [
                            { x: 500, y: 50 },
                            { x: 500, y: 750 }
                        ],
                        width: 40,
                        direction: 'two-way'
                    }
                ]
            };

            mapViewer.fitToScreen();
            mapViewer.render();

            // Initialize animation system
            if (!animationSystem) {
                initAnimationSystem();
            }

            // Generate demo entities
            if (animationSystem) {
                setTimeout(() => {
                    animationSystem.generateDemoEntities(15);
                }, 500);
            }

            // Update info
            updateMapInfo('Demo Map', mapViewer.mapData);
        }
    }

    startSimulationTime() {
        if (this.simTimeInterval) return;

        this.simTime = 0;
        this.simTimeInterval = setInterval(() => {
            if (simulationControls && simulationControls.isRunning) {
                this.simTime += simulationControls.speed;
                this.updateSimTimeDisplay();
            }
        }, 1000);
    }

    updateSimTimeDisplay() {
        const minutes = Math.floor(this.simTime / 60);
        const seconds = Math.floor(this.simTime % 60);
        const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        const timeElements = ['simTime', 'simTimeDisplay'];
        timeElements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = timeStr;
        });
    }

    // Utility methods
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // Could implement a toast notification system here
    }

    handleError(error, context = '') {
        console.error(`Error in ${context}:`, error);
        this.showNotification(`Error: ${error.message}`, 'error');
    }
}

// Global application instance
let app = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    app = new Application();
});

// Global utility functions
function formatNumber(num, decimals = 0) {
    return num.toFixed(decimals);
}

function formatPercent(value) {
    return `${Math.round(value * 100)}%`;
}

function formatSpeed(speed) {
    return `${Math.round(speed)} km/h`;
}

function formatPosition(x, y) {
    return `${Math.round(x)}, ${Math.round(y)}`;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+S to save
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        if (app.currentPage === 'editor') {
            saveMapEdits();
        } else {
            saveMap();
        }
    }

    // Space to pause/resume
    if (e.key === ' ' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        e.preventDefault();
        if (simulationControls) {
            if (simulationControls.isRunning) {
                pauseSimulation();
            } else {
                startSimulation();
            }
        }
    }

    // +/- to zoom
    if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        zoomIn();
    }
    if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        zoomOut();
    }

    // 0 to reset zoom
    if (e.key === '0') {
        e.preventDefault();
        resetZoom();
    }

    // F to fit to screen
    if (e.key === 'f') {
        e.preventDefault();
        fitToScreen();
    }

    // H to toggle help
    if (e.key === 'h' || e.key === '?') {
        e.preventDefault();
        showKeyboardShortcuts();
    }
});

function showKeyboardShortcuts() {
    const shortcuts = `
Keyboard Shortcuts:

Navigation:
  Mouse Wheel - Zoom in/out
  Click + Drag - Pan map
  + / - - Zoom in/out
  0 - Reset zoom
  F - Fit to screen

Simulation:
  Space - Start/Pause simulation
  R - Reset simulation

Editor (Editor page only):
  Ctrl+Z - Undo
  Delete - Delete selected element
  Escape - Cancel current operation
  Enter - Finish drawing

General:
  Ctrl+S - Save
  H or ? - Show this help
    `.trim();

    alert(shortcuts);
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
});

// Log application ready
console.log('Main application script loaded');
console.log('Autonomous Taxi Simulation - Frontend v1.0');
console.log('Ready for initialization...');
