/**
 * Map Editor - Tools for manual map editing
 * Allows drawing zones, roads, and subzones
 */

class MapEditor {
    constructor(viewer) {
        this.viewer = viewer;
        this.currentTool = 'select';
        this.isDrawing = false;
        this.drawingPoints = [];
        this.selectedElement = null;
        this.history = [];
        this.historyIndex = -1;

        // Editor data
        this.zones = [];
        this.roads = [];
        this.subzones = [];
        this.intersections = [];
        this.crosswalks = [];

        // Tool settings
        this.zoneType = 'prohibited';
        this.zoneName = '';
        this.roadWidth = 20;
        this.roadDirection = 'two-way';
        this.speedLimit = 50;

        this.setupEventListeners();
        this.updateInstructions();
    }

    setupEventListeners() {
        if (!this.viewer || !this.viewer.canvas) return;

        const canvas = this.viewer.canvas;

        // Override viewer's mouse handlers for editor
        canvas.addEventListener('mousedown', (e) => this.handleEditorMouseDown(e), true);
        canvas.addEventListener('mousemove', (e) => this.handleEditorMouseMove(e), true);
        canvas.addEventListener('mouseup', (e) => this.handleEditorMouseUp(e), true);
        canvas.addEventListener('dblclick', (e) => this.handleDoubleClick(e), true);

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }

    handleEditorMouseDown(e) {
        if (this.currentTool === 'select') {
            // Allow normal panning
            return;
        }

        e.stopPropagation();

        const rect = this.viewer.canvas.getBoundingClientRect();
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;
        const worldPos = this.viewer.screenToWorld(screenX, screenY);

        if (this.currentTool === 'zone' || this.currentTool === 'polygon') {
            // Start drawing polygon
            this.drawingPoints.push(worldPos);
            this.isDrawing = true;
        } else if (this.currentTool === 'road') {
            // Start drawing road
            this.drawingPoints.push(worldPos);
            this.isDrawing = true;
        } else if (this.currentTool === 'sidewalk' || this.currentTool === 'parking') {
            // Start drawing subzone
            this.drawingPoints.push(worldPos);
            this.isDrawing = true;
        } else if (this.currentTool === 'intersection') {
            // Place intersection
            this.addIntersection(worldPos);
        } else if (this.currentTool === 'crosswalk') {
            // Start drawing crosswalk
            this.drawingPoints.push(worldPos);
            this.isDrawing = true;
        } else if (this.currentTool === 'delete') {
            // Delete element at position
            this.deleteElementAt(worldPos);
        }

        this.viewer.render();
        this.renderEditor();
    }

    handleEditorMouseMove(e) {
        if (!this.isDrawing || this.currentTool === 'select') return;

        const rect = this.viewer.canvas.getBoundingClientRect();
        const screenX = e.clientX - rect.left;
        const screenY = e.clientY - rect.top;
        const worldPos = this.viewer.screenToWorld(screenX, screenY);

        // Store current mouse position for preview
        this.currentMousePos = worldPos;

        this.viewer.render();
        this.renderEditor();
    }

    handleEditorMouseUp(e) {
        if (this.currentTool === 'select') return;

        if (this.currentTool === 'zone' && this.drawingPoints.length === 1) {
            // For zone tool, allow drag to create rectangle
            const rect = this.viewer.canvas.getBoundingClientRect();
            const screenX = e.clientX - rect.left;
            const screenY = e.clientY - rect.top;
            const worldPos = this.viewer.screenToWorld(screenX, screenY);

            if (Math.abs(worldPos.x - this.drawingPoints[0].x) > 10 &&
                Math.abs(worldPos.y - this.drawingPoints[0].y) > 10) {
                // Create rectangle zone
                this.createRectangleZone(this.drawingPoints[0], worldPos);
                this.drawingPoints = [];
                this.isDrawing = false;
                this.viewer.render();
                this.renderEditor();
            }
        }
    }

    handleDoubleClick(e) {
        e.preventDefault();

        if (this.drawingPoints.length >= 2) {
            // Finish drawing
            this.finishDrawing();
        }
    }

    handleKeyDown(e) {
        // Escape to cancel
        if (e.key === 'Escape') {
            this.cancelDrawing();
        }
        // Enter to finish
        else if (e.key === 'Enter' && this.drawingPoints.length >= 2) {
            this.finishDrawing();
        }
        // Ctrl+Z to undo
        else if (e.ctrlKey && e.key === 'z') {
            this.undo();
        }
        // Delete key
        else if (e.key === 'Delete' && this.selectedElement) {
            this.deleteSelectedElement();
        }
    }

    finishDrawing() {
        if (this.drawingPoints.length < 2) return;

        if (this.currentTool === 'polygon') {
            this.createPolygonZone();
        } else if (this.currentTool === 'road') {
            this.createRoad();
        } else if (this.currentTool === 'sidewalk') {
            this.createSubzone('sidewalk');
        } else if (this.currentTool === 'parking') {
            this.createSubzone('parking');
        } else if (this.currentTool === 'crosswalk') {
            this.createCrosswalk();
        }

        this.drawingPoints = [];
        this.isDrawing = false;
        this.currentMousePos = null;
        this.addToHistory();
        this.viewer.render();
        this.renderEditor();
        this.updateCounts();
    }

    cancelDrawing() {
        this.drawingPoints = [];
        this.isDrawing = false;
        this.currentMousePos = null;
        this.viewer.render();
        this.renderEditor();
    }

    createRectangleZone(p1, p2) {
        const zone = {
            id: `zone_${Date.now()}`,
            type: this.zoneType,
            name: this.zoneName || `Zone ${this.zones.length + 1}`,
            points: [
                { x: p1.x, y: p1.y },
                { x: p2.x, y: p1.y },
                { x: p2.x, y: p2.y },
                { x: p1.x, y: p2.y }
            ]
        };

        this.zones.push(zone);
        this.addToHistory();
        this.updateCounts();
    }

    createPolygonZone() {
        const zone = {
            id: `zone_${Date.now()}`,
            type: this.zoneType,
            name: this.zoneName || `Zone ${this.zones.length + 1}`,
            points: [...this.drawingPoints]
        };

        this.zones.push(zone);
    }

    createRoad() {
        const road = {
            id: `road_${Date.now()}`,
            points: [...this.drawingPoints],
            width: this.roadWidth,
            direction: this.roadDirection,
            speedLimit: this.speedLimit
        };

        this.roads.push(road);
    }

    createSubzone(type) {
        const subzone = {
            id: `subzone_${Date.now()}`,
            type: type,
            points: [...this.drawingPoints]
        };

        this.subzones.push(subzone);
    }

    createCrosswalk() {
        if (this.drawingPoints.length !== 2) return;

        const crosswalk = {
            id: `crosswalk_${Date.now()}`,
            points: [...this.drawingPoints]
        };

        this.crosswalks.push(crosswalk);
    }

    addIntersection(position) {
        const intersection = {
            id: `intersection_${Date.now()}`,
            position: position
        };

        this.intersections.push(intersection);
        this.addToHistory();
        this.viewer.render();
        this.renderEditor();
    }

    deleteElementAt(position) {
        const tolerance = 10 / this.viewer.zoom;

        // Check zones
        for (let i = this.zones.length - 1; i >= 0; i--) {
            if (this.isPointInPolygon(position, this.zones[i].points)) {
                this.zones.splice(i, 1);
                this.addToHistory();
                this.updateCounts();
                return;
            }
        }

        // Check roads
        for (let i = this.roads.length - 1; i >= 0; i--) {
            if (this.isPointNearPolyline(position, this.roads[i].points, tolerance)) {
                this.roads.splice(i, 1);
                this.addToHistory();
                this.updateCounts();
                return;
            }
        }

        // Check subzones
        for (let i = this.subzones.length - 1; i >= 0; i--) {
            if (this.isPointInPolygon(position, this.subzones[i].points)) {
                this.subzones.splice(i, 1);
                this.addToHistory();
                return;
            }
        }

        this.viewer.render();
        this.renderEditor();
    }

    deleteSelectedElement() {
        // Implementation for deleting selected element
        this.selectedElement = null;
        this.viewer.render();
        this.renderEditor();
    }

    isPointInPolygon(point, polygon) {
        let inside = false;
        for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
            const xi = polygon[i].x, yi = polygon[i].y;
            const xj = polygon[j].x, yj = polygon[j].y;

            const intersect = ((yi > point.y) !== (yj > point.y))
                && (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    }

    isPointNearPolyline(point, polyline, tolerance) {
        for (let i = 0; i < polyline.length - 1; i++) {
            const dist = this.pointToSegmentDistance(point, polyline[i], polyline[i + 1]);
            if (dist < tolerance) return true;
        }
        return false;
    }

    pointToSegmentDistance(point, segStart, segEnd) {
        const dx = segEnd.x - segStart.x;
        const dy = segEnd.y - segStart.y;
        const lengthSq = dx * dx + dy * dy;

        if (lengthSq === 0) {
            const dpx = point.x - segStart.x;
            const dpy = point.y - segStart.y;
            return Math.sqrt(dpx * dpx + dpy * dpy);
        }

        let t = ((point.x - segStart.x) * dx + (point.y - segStart.y) * dy) / lengthSq;
        t = Math.max(0, Math.min(1, t));

        const projX = segStart.x + t * dx;
        const projY = segStart.y + t * dy;
        const dpx = point.x - projX;
        const dpy = point.y - projY;

        return Math.sqrt(dpx * dpx + dpy * dpy);
    }

    renderEditor() {
        if (!this.viewer) return;

        const ctx = this.viewer.ctx;
        ctx.save();
        ctx.translate(this.viewer.panX, this.viewer.panY);
        ctx.scale(this.viewer.zoom, this.viewer.zoom);

        // Draw editor elements
        this.drawEditorZones(ctx);
        this.drawEditorRoads(ctx);
        this.drawEditorSubzones(ctx);
        this.drawEditorIntersections(ctx);
        this.drawEditorCrosswalks(ctx);

        // Draw current drawing
        if (this.isDrawing && this.drawingPoints.length > 0) {
            this.drawCurrentDrawing(ctx);
        }

        ctx.restore();
    }

    drawEditorZones(ctx) {
        this.zones.forEach(zone => {
            const color = this.viewer.getZoneColor(zone.type);
            ctx.strokeStyle = color;
            ctx.lineWidth = 2 / this.viewer.zoom;
            ctx.fillStyle = color + '30';

            ctx.beginPath();
            if (zone.points.length > 0) {
                ctx.moveTo(zone.points[0].x, zone.points[0].y);
                for (let i = 1; i < zone.points.length; i++) {
                    ctx.lineTo(zone.points[i].x, zone.points[i].y);
                }
                ctx.closePath();
                ctx.fill();
                ctx.stroke();

                // Draw zone label
                const centerX = zone.points.reduce((sum, p) => sum + p.x, 0) / zone.points.length;
                const centerY = zone.points.reduce((sum, p) => sum + p.y, 0) / zone.points.length;
                ctx.fillStyle = '#ffffff';
                ctx.font = `${10 / this.viewer.zoom}px monospace`;
                ctx.textAlign = 'center';
                ctx.fillText(zone.name, centerX, centerY);
            }
        });
    }

    drawEditorRoads(ctx) {
        this.roads.forEach(road => {
            ctx.strokeStyle = '#7cc5f0';
            ctx.lineWidth = road.width / this.viewer.zoom;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            ctx.beginPath();
            if (road.points.length > 0) {
                ctx.moveTo(road.points[0].x, road.points[0].y);
                for (let i = 1; i < road.points.length; i++) {
                    ctx.lineTo(road.points[i].x, road.points[i].y);
                }
                ctx.stroke();
            }
        });
    }

    drawEditorSubzones(ctx) {
        this.subzones.forEach(subzone => {
            const color = subzone.type === 'sidewalk' ? '#90b8d8' :
                         subzone.type === 'parking' ? '#facc15' : '#4da8da';

            ctx.strokeStyle = color;
            ctx.lineWidth = 1 / this.viewer.zoom;
            ctx.fillStyle = color + '20';

            ctx.beginPath();
            if (subzone.points.length > 0) {
                ctx.moveTo(subzone.points[0].x, subzone.points[0].y);
                for (let i = 1; i < subzone.points.length; i++) {
                    ctx.lineTo(subzone.points[i].x, subzone.points[i].y);
                }
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
            }
        });
    }

    drawEditorIntersections(ctx) {
        this.intersections.forEach(intersection => {
            ctx.fillStyle = '#facc15';
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2 / this.viewer.zoom;

            ctx.beginPath();
            ctx.arc(intersection.position.x, intersection.position.y, 15, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();

            // Draw cross symbol
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 3 / this.viewer.zoom;
            const size = 8;
            ctx.beginPath();
            ctx.moveTo(intersection.position.x - size, intersection.position.y);
            ctx.lineTo(intersection.position.x + size, intersection.position.y);
            ctx.moveTo(intersection.position.x, intersection.position.y - size);
            ctx.lineTo(intersection.position.x, intersection.position.y + size);
            ctx.stroke();
        });
    }

    drawEditorCrosswalks(ctx) {
        this.crosswalks.forEach(crosswalk => {
            if (crosswalk.points.length !== 2) return;

            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 10 / this.viewer.zoom;
            ctx.setLineDash([5 / this.viewer.zoom, 5 / this.viewer.zoom]);

            ctx.beginPath();
            ctx.moveTo(crosswalk.points[0].x, crosswalk.points[0].y);
            ctx.lineTo(crosswalk.points[1].x, crosswalk.points[1].y);
            ctx.stroke();
            ctx.setLineDash([]);
        });
    }

    drawCurrentDrawing(ctx) {
        ctx.strokeStyle = '#4ade80';
        ctx.lineWidth = 2 / this.viewer.zoom;
        ctx.fillStyle = 'rgba(74, 222, 128, 0.2)';

        // Draw points
        this.drawingPoints.forEach(point => {
            ctx.fillStyle = '#4ade80';
            ctx.beginPath();
            ctx.arc(point.x, point.y, 5 / this.viewer.zoom, 0, Math.PI * 2);
            ctx.fill();
        });

        // Draw lines between points
        if (this.drawingPoints.length > 1) {
            ctx.strokeStyle = '#4ade80';
            ctx.beginPath();
            ctx.moveTo(this.drawingPoints[0].x, this.drawingPoints[0].y);
            for (let i = 1; i < this.drawingPoints.length; i++) {
                ctx.lineTo(this.drawingPoints[i].x, this.drawingPoints[i].y);
            }
            ctx.stroke();
        }

        // Draw preview line to current mouse position
        if (this.currentMousePos && this.drawingPoints.length > 0) {
            ctx.strokeStyle = 'rgba(74, 222, 128, 0.5)';
            ctx.setLineDash([5 / this.viewer.zoom, 5 / this.viewer.zoom]);
            ctx.beginPath();
            const lastPoint = this.drawingPoints[this.drawingPoints.length - 1];
            ctx.moveTo(lastPoint.x, lastPoint.y);
            ctx.lineTo(this.currentMousePos.x, this.currentMousePos.y);
            ctx.stroke();
            ctx.setLineDash([]);
        }
    }

    addToHistory() {
        const state = {
            zones: JSON.parse(JSON.stringify(this.zones)),
            roads: JSON.parse(JSON.stringify(this.roads)),
            subzones: JSON.parse(JSON.stringify(this.subzones)),
            intersections: JSON.parse(JSON.stringify(this.intersections)),
            crosswalks: JSON.parse(JSON.stringify(this.crosswalks))
        };

        this.history = this.history.slice(0, this.historyIndex + 1);
        this.history.push(state);
        this.historyIndex++;

        // Limit history size
        if (this.history.length > 50) {
            this.history.shift();
            this.historyIndex--;
        }
    }

    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            const state = this.history[this.historyIndex];
            this.zones = JSON.parse(JSON.stringify(state.zones));
            this.roads = JSON.parse(JSON.stringify(state.roads));
            this.subzones = JSON.parse(JSON.stringify(state.subzones));
            this.intersections = JSON.parse(JSON.stringify(state.intersections));
            this.crosswalks = JSON.parse(JSON.stringify(state.crosswalks));

            this.viewer.render();
            this.renderEditor();
            this.updateCounts();
        }
    }

    updateInstructions() {
        const instructions = {
            'select': 'Click on elements to select and edit them.',
            'zone': 'Click and drag to create a rectangular zone, or click points for polygon.',
            'road': 'Click points to draw a road. Double-click to finish.',
            'polygon': 'Click points to draw a polygon zone. Double-click to finish.',
            'sidewalk': 'Click points to mark sidewalk area. Double-click to finish.',
            'parking': 'Click points to mark parking area. Double-click to finish.',
            'intersection': 'Click to place intersection markers.',
            'crosswalk': 'Click two points to create a crosswalk.',
            'delete': 'Click on elements to delete them.'
        };

        const instructionElem = document.getElementById('toolInstructions');
        if (instructionElem) {
            const toolName = this.currentTool.charAt(0).toUpperCase() + this.currentTool.slice(1);
            instructionElem.innerHTML = `<strong>${toolName} Tool:</strong><br>${instructions[this.currentTool]}`;
        }
    }

    updateCounts() {
        const zoneCountElem = document.getElementById('editorZoneCount');
        const roadCountElem = document.getElementById('editorRoadCount');

        if (zoneCountElem) zoneCountElem.textContent = this.zones.length;
        if (roadCountElem) roadCountElem.textContent = this.roads.length;
    }

    loadFromMapData(mapData) {
        if (mapData.zones) this.zones = [...mapData.zones];
        if (mapData.roads) this.roads = [...mapData.roads];
        if (mapData.subzones) this.subzones = [...mapData.subzones];

        this.addToHistory();
        this.updateCounts();
        this.viewer.render();
        this.renderEditor();
    }

    exportData() {
        return {
            zones: this.zones,
            roads: this.roads,
            subzones: this.subzones,
            intersections: this.intersections,
            crosswalks: this.crosswalks
        };
    }
}

// Global editor instance
let mapEditor = null;

// Initialize editor when viewer is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for viewer to be initialized
    setTimeout(() => {
        if (mapViewer && document.getElementById('editor-canvas')) {
            mapEditor = new MapEditor(mapViewer);
            // Start rendering loop for editor
            function editorRenderLoop() {
                if (mapEditor) {
                    mapEditor.renderEditor();
                }
                requestAnimationFrame(editorRenderLoop);
            }
            editorRenderLoop();
        }
    }, 100);
});

// Tool selection
function selectTool(toolName) {
    if (!mapEditor) return;

    mapEditor.currentTool = toolName;
    mapEditor.updateInstructions();

    // Update UI
    document.querySelectorAll('.tool-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const selectedBtn = document.querySelector(`[data-tool="${toolName}"]`);
    if (selectedBtn) selectedBtn.classList.add('active');

    // Update status
    const currentToolElem = document.getElementById('currentTool');
    if (currentToolElem) {
        currentToolElem.textContent = toolName.charAt(0).toUpperCase() + toolName.slice(1);
    }

    // Show/hide property panels
    const zoneProps = document.getElementById('zoneProperties');
    const roadProps = document.getElementById('roadProperties');

    if (zoneProps) zoneProps.style.display = (toolName === 'zone' || toolName === 'polygon') ? 'block' : 'none';
    if (roadProps) roadProps.style.display = (toolName === 'road') ? 'block' : 'none';
}

// Property application
function applyZoneProperties() {
    if (!mapEditor) return;

    const typeElem = document.getElementById('zoneType');
    const nameElem = document.getElementById('zoneName');

    if (typeElem) mapEditor.zoneType = typeElem.value;
    if (nameElem) mapEditor.zoneName = nameElem.value;
}

function applyRoadProperties() {
    if (!mapEditor) return;

    const widthElem = document.getElementById('roadWidth');
    const directionElem = document.getElementById('roadDirection');
    const speedLimitElem = document.getElementById('speedLimit');

    if (widthElem) mapEditor.roadWidth = parseInt(widthElem.value);
    if (directionElem) mapEditor.roadDirection = directionElem.value;
    if (speedLimitElem) mapEditor.speedLimit = parseInt(speedLimitElem.value);
}

// Editor controls
function saveMapEdits() {
    if (!mapEditor || !mapViewer) return;

    const editorData = mapEditor.exportData();

    // Merge with existing map data
    if (mapViewer.mapData) {
        mapViewer.mapData.zones = editorData.zones;
        mapViewer.mapData.roads = editorData.roads;
        mapViewer.mapData.subzones = editorData.subzones;

        // Save via API
        fetch('/api/map/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(mapViewer.mapData)
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Map saved successfully!');
                } else {
                    alert('Error saving map: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error saving map:', error);
                alert('Error saving map');
            });
    }
}

function undoEdit() {
    if (mapEditor) {
        mapEditor.undo();
    }
}

function clearEdits() {
    if (!mapEditor) return;

    if (confirm('Clear all edits? This cannot be undone.')) {
        mapEditor.zones = [];
        mapEditor.roads = [];
        mapEditor.subzones = [];
        mapEditor.intersections = [];
        mapEditor.crosswalks = [];
        mapEditor.addToHistory();
        mapEditor.updateCounts();
        mapViewer.render();
        mapEditor.renderEditor();
    }
}

function toggleEditorLayer(layerName, visible) {
    if (mapViewer) {
        mapViewer.toggleLayer(layerName, visible);
    }
}
