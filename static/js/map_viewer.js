/**
 * Map Viewer - Handles map display, zoom, and pan functionality
 * Maintains relative positions of all elements when zooming/panning
 */

class MapViewer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) {
            console.error('Canvas not found:', canvasId);
            return;
        }

        this.ctx = this.canvas.getContext('2d');
        this.canvasId = canvasId;

        // View state
        this.zoom = 1.0;
        this.minZoom = 0.1;
        this.maxZoom = 5.0;
        this.panX = 0;
        this.panY = 0;

        // Map data
        this.mapImage = null;
        this.mapData = null;
        this.mapWidth = 0;
        this.mapHeight = 0;

        // Interaction state
        this.isDragging = false;
        this.lastMouseX = 0;
        this.lastMouseY = 0;
        this.mouseX = 0;
        this.mouseY = 0;

        // Layer visibility
        this.layers = {
            zones: true,
            roads: true,
            vehicles: true,
            pedestrians: true,
            sensors: false,
            speedLimits: false,
            paths: false,
            grid: true,
            subzones: true
        };

        this.initCanvas();
        this.setupEventListeners();
    }

    initCanvas() {
        // Set canvas size to match container
        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const container = this.canvas.parentElement;
        this.canvas.width = container.clientWidth;
        this.canvas.height = container.clientHeight;
        this.render();
    }

    setupEventListeners() {
        // Mouse wheel for zoom
        this.canvas.addEventListener('wheel', (e) => this.handleWheel(e));

        // Mouse events for panning
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.handleMouseUp(e));
        this.canvas.addEventListener('mouseleave', (e) => this.handleMouseUp(e));

        // Touch events for mobile
        this.canvas.addEventListener('touchstart', (e) => this.handleTouchStart(e));
        this.canvas.addEventListener('touchmove', (e) => this.handleTouchMove(e));
        this.canvas.addEventListener('touchend', (e) => this.handleTouchEnd(e));
    }

    handleWheel(e) {
        e.preventDefault();

        const rect = this.canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        // Calculate world position before zoom
        const worldX = (mouseX - this.panX) / this.zoom;
        const worldY = (mouseY - this.panY) / this.zoom;

        // Update zoom
        const zoomDelta = e.deltaY > 0 ? 0.9 : 1.1;
        const newZoom = Math.max(this.minZoom, Math.min(this.maxZoom, this.zoom * zoomDelta));

        // Calculate new pan to keep mouse position fixed
        this.panX = mouseX - worldX * newZoom;
        this.panY = mouseY - worldY * newZoom;
        this.zoom = newZoom;

        this.updateZoomDisplay();
        this.render();
    }

    handleMouseDown(e) {
        this.isDragging = true;
        this.lastMouseX = e.clientX;
        this.lastMouseY = e.clientY;
        this.canvas.style.cursor = 'grabbing';
    }

    handleMouseMove(e) {
        const rect = this.canvas.getBoundingClientRect();
        this.mouseX = e.clientX - rect.left;
        this.mouseY = e.clientY - rect.top;

        // Update mouse position display
        const worldX = Math.floor((this.mouseX - this.panX) / this.zoom);
        const worldY = Math.floor((this.mouseY - this.panY) / this.zoom);
        this.updateMousePosition(worldX, worldY);

        if (this.isDragging) {
            const dx = e.clientX - this.lastMouseX;
            const dy = e.clientY - this.lastMouseY;

            this.panX += dx;
            this.panY += dy;

            this.lastMouseX = e.clientX;
            this.lastMouseY = e.clientY;

            this.render();
        }
    }

    handleMouseUp(e) {
        this.isDragging = false;
        this.canvas.style.cursor = 'grab';
    }

    handleTouchStart(e) {
        if (e.touches.length === 1) {
            this.isDragging = true;
            this.lastMouseX = e.touches[0].clientX;
            this.lastMouseY = e.touches[0].clientY;
        }
    }

    handleTouchMove(e) {
        e.preventDefault();
        if (e.touches.length === 1 && this.isDragging) {
            const dx = e.touches[0].clientX - this.lastMouseX;
            const dy = e.touches[0].clientY - this.lastMouseY;

            this.panX += dx;
            this.panY += dy;

            this.lastMouseX = e.touches[0].clientX;
            this.lastMouseY = e.touches[0].clientY;

            this.render();
        }
    }

    handleTouchEnd(e) {
        this.isDragging = false;
    }

    // Coordinate transformations
    worldToScreen(x, y) {
        return {
            x: x * this.zoom + this.panX,
            y: y * this.zoom + this.panY
        };
    }

    screenToWorld(x, y) {
        return {
            x: (x - this.panX) / this.zoom,
            y: (y - this.panY) / this.zoom
        };
    }

    // Zoom controls
    zoomIn(amount = 1.2) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        const worldX = (centerX - this.panX) / this.zoom;
        const worldY = (centerY - this.panY) / this.zoom;

        const newZoom = Math.min(this.maxZoom, this.zoom * amount);

        this.panX = centerX - worldX * newZoom;
        this.panY = centerY - worldY * newZoom;
        this.zoom = newZoom;

        this.updateZoomDisplay();
        this.render();
    }

    zoomOut(amount = 1.2) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;

        const worldX = (centerX - this.panX) / this.zoom;
        const worldY = (centerY - this.panY) / this.zoom;

        const newZoom = Math.max(this.minZoom, this.zoom / amount);

        this.panX = centerX - worldX * newZoom;
        this.panY = centerY - worldY * newZoom;
        this.zoom = newZoom;

        this.updateZoomDisplay();
        this.render();
    }

    resetZoom() {
        this.zoom = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.updateZoomDisplay();
        this.render();
    }

    fitToScreen() {
        if (!this.mapImage) return;

        const padding = 50;
        const availableWidth = this.canvas.width - padding * 2;
        const availableHeight = this.canvas.height - padding * 2;

        const scaleX = availableWidth / this.mapWidth;
        const scaleY = availableHeight / this.mapHeight;
        this.zoom = Math.min(scaleX, scaleY);

        // Center the map
        this.panX = (this.canvas.width - this.mapWidth * this.zoom) / 2;
        this.panY = (this.canvas.height - this.mapHeight * this.zoom) / 2;

        this.updateZoomDisplay();
        this.render();
    }

    // Layer controls
    toggleLayer(layerName, visible) {
        if (this.layers.hasOwnProperty(layerName)) {
            this.layers[layerName] = visible;
            this.render();
        }
    }

    // Map loading
    async loadMap(mapName) {
        try {
            // Load map data
            const response = await fetch(`/api/map/load/${mapName}`);
            if (!response.ok) throw new Error('Failed to load map');

            this.mapData = await response.json();

            // Load map image
            return new Promise((resolve, reject) => {
                const img = new Image();
                img.onload = () => {
                    this.mapImage = img;
                    this.mapWidth = img.width;
                    this.mapHeight = img.height;
                    this.fitToScreen();
                    resolve(this.mapData);
                };
                img.onerror = reject;
                img.src = this.mapData.image_path;
            });
        } catch (error) {
            console.error('Error loading map:', error);
            throw error;
        }
    }

    // Rendering
    render() {
        // Clear canvas
        this.ctx.fillStyle = '#0a2540';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Save context state
        this.ctx.save();

        // Apply pan and zoom transformations
        this.ctx.translate(this.panX, this.panY);
        this.ctx.scale(this.zoom, this.zoom);

        // Draw map image
        if (this.mapImage) {
            this.ctx.drawImage(this.mapImage, 0, 0, this.mapWidth, this.mapHeight);
        }

        // Draw layers
        if (this.mapData) {
            if (this.layers.zones) this.drawZones();
            if (this.layers.roads) this.drawRoads();
            if (this.layers.subzones) this.drawSubzones();
        }

        // Restore context state
        this.ctx.restore();

        // Draw UI overlays (not affected by pan/zoom)
        if (this.layers.grid) this.drawGridOverlay();
    }

    drawZones() {
        if (!this.mapData.zones) return;

        this.mapData.zones.forEach(zone => {
            this.ctx.strokeStyle = this.getZoneColor(zone.type);
            this.ctx.lineWidth = 2 / this.zoom;
            this.ctx.fillStyle = this.getZoneColor(zone.type) + '30';

            this.ctx.beginPath();
            if (zone.points && zone.points.length > 0) {
                this.ctx.moveTo(zone.points[0].x, zone.points[0].y);
                for (let i = 1; i < zone.points.length; i++) {
                    this.ctx.lineTo(zone.points[i].x, zone.points[i].y);
                }
                this.ctx.closePath();
                this.ctx.fill();
                this.ctx.stroke();
            }
        });
    }

    drawRoads() {
        if (!this.mapData.roads) return;

        this.mapData.roads.forEach(road => {
            this.ctx.strokeStyle = '#7cc5f0';
            this.ctx.lineWidth = (road.width || 20) / this.zoom;
            this.ctx.lineCap = 'round';
            this.ctx.lineJoin = 'round';

            this.ctx.beginPath();
            if (road.points && road.points.length > 0) {
                this.ctx.moveTo(road.points[0].x, road.points[0].y);
                for (let i = 1; i < road.points.length; i++) {
                    this.ctx.lineTo(road.points[i].x, road.points[i].y);
                }
                this.ctx.stroke();
            }
        });
    }

    drawSubzones() {
        if (!this.mapData.subzones) return;

        this.mapData.subzones.forEach(subzone => {
            const color = subzone.type === 'sidewalk' ? '#90b8d8' :
                         subzone.type === 'parking' ? '#facc15' : '#4da8da';

            this.ctx.strokeStyle = color;
            this.ctx.lineWidth = 1 / this.zoom;
            this.ctx.fillStyle = color + '20';

            this.ctx.beginPath();
            if (subzone.points && subzone.points.length > 0) {
                this.ctx.moveTo(subzone.points[0].x, subzone.points[0].y);
                for (let i = 1; i < subzone.points.length; i++) {
                    this.ctx.lineTo(subzone.points[i].x, subzone.points[i].y);
                }
                this.ctx.closePath();
                this.ctx.fill();
                this.ctx.stroke();
            }
        });
    }

    drawGridOverlay() {
        // This is drawn in screen space, not world space
        this.ctx.strokeStyle = 'rgba(77, 168, 218, 0.1)';
        this.ctx.lineWidth = 1;

        const gridSize = 50;
        for (let x = 0; x < this.canvas.width; x += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(x, 0);
            this.ctx.lineTo(x, this.canvas.height);
            this.ctx.stroke();
        }

        for (let y = 0; y < this.canvas.height; y += gridSize) {
            this.ctx.beginPath();
            this.ctx.moveTo(0, y);
            this.ctx.lineTo(this.canvas.width, y);
            this.ctx.stroke();
        }
    }

    getZoneColor(type) {
        const colors = {
            'prohibited': '#f87171',
            'yard': '#4ade80',
            'urban': '#60a5fa',
            'countryside': '#4ade80',
            'highway': '#facc15'
        };
        return colors[type] || '#4da8da';
    }

    updateZoomDisplay() {
        const zoomPercent = Math.round(this.zoom * 100);
        const elements = ['zoomLevel', 'editorZoomLevel', 'simZoomLevel', 'zoomStatus', 'simZoomStatus'];
        elements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = `${zoomPercent}%`;
        });
    }

    updateMousePosition(x, y) {
        const elements = ['mousePos', 'editorMousePos', 'simMousePos'];
        elements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = `${x}, ${y}`;
        });
    }
}

// Global viewer instance
let mapViewer = null;

// Initialize viewer when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const canvasId = document.getElementById('map-canvas') ? 'map-canvas' :
                     document.getElementById('editor-canvas') ? 'editor-canvas' :
                     document.getElementById('simulation-canvas') ? 'simulation-canvas' : null;

    if (canvasId) {
        mapViewer = new MapViewer(canvasId);
    }
});

// Global zoom control functions
function zoomIn() {
    if (mapViewer) mapViewer.zoomIn();
}

function zoomOut() {
    if (mapViewer) mapViewer.zoomOut();
}

function resetZoom() {
    if (mapViewer) mapViewer.resetZoom();
}

function fitToScreen() {
    if (mapViewer) mapViewer.fitToScreen();
}

function resetView() {
    if (mapViewer) {
        mapViewer.resetZoom();
        mapViewer.fitToScreen();
    }
}

function toggleGrid() {
    if (mapViewer) {
        mapViewer.layers.grid = !mapViewer.layers.grid;
        mapViewer.render();
    }
}

// Editor-specific zoom functions
function editorZoomIn() { zoomIn(); }
function editorZoomOut() { zoomOut(); }
function editorResetZoom() { resetZoom(); }
