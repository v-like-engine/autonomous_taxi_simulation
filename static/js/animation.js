/**
 * Animation System - 60 FPS rendering loop with entity animation
 * Handles smooth interpolation and real-time visualization
 */

class AnimationSystem {
    constructor(viewer) {
        this.viewer = viewer;
        this.isRunning = false;
        this.lastFrameTime = 0;
        this.fps = 60;
        this.frameCount = 0;
        this.fpsUpdateTime = 0;

        // Entity data
        this.vehicles = [];
        this.pedestrians = [];
        this.mainCar = null;

        // Animation settings
        this.interpolate = true;
        this.showPaths = false;
        this.showSensors = false;

        // Colors
        this.vehicleColors = {
            car: '#60a5fa',
            truck: '#facc15',
            main: '#4ade80'
        };

        this.pedestrianColor = '#f87171';

        // Start animation loop
        this.start();
    }

    start() {
        this.isRunning = true;
        this.animate();
    }

    stop() {
        this.isRunning = false;
    }

    animate(timestamp = 0) {
        if (!this.isRunning) return;

        // Calculate delta time
        const deltaTime = timestamp - this.lastFrameTime;
        this.lastFrameTime = timestamp;

        // Update FPS counter
        this.frameCount++;
        if (timestamp - this.fpsUpdateTime >= 1000) {
            this.fps = this.frameCount;
            this.updateFPSDisplay();
            this.frameCount = 0;
            this.fpsUpdateTime = timestamp;
        }

        // Render frame
        this.render(deltaTime);

        // Request next frame
        requestAnimationFrame((t) => this.animate(t));
    }

    render(deltaTime) {
        // Use viewer's render method for base map
        if (this.viewer) {
            this.viewer.render();

            // Save context
            const ctx = this.viewer.ctx;
            ctx.save();

            // Apply transformations
            ctx.translate(this.viewer.panX, this.viewer.panY);
            ctx.scale(this.viewer.zoom, this.viewer.zoom);

            // Draw entities
            if (this.viewer.layers.paths && this.showPaths) {
                this.drawPaths(ctx);
            }

            if (this.viewer.layers.vehicles) {
                this.drawVehicles(ctx);
            }

            if (this.viewer.layers.pedestrians) {
                this.drawPedestrians(ctx);
            }

            if (this.mainCar) {
                this.drawMainCar(ctx);
            }

            if (this.viewer.layers.sensors && this.showSensors) {
                this.drawSensorVisualization(ctx);
            }

            // Restore context
            ctx.restore();
        }
    }

    drawVehicles(ctx) {
        this.vehicles.forEach(vehicle => {
            if (!vehicle.position) return;

            const { x, y } = vehicle.position;
            const angle = vehicle.angle || 0;
            const type = vehicle.type || 'car';
            const width = type === 'truck' ? 30 : 20;
            const height = type === 'truck' ? 60 : 40;

            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(angle);

            // Draw vehicle body
            ctx.fillStyle = this.vehicleColors[type] || this.vehicleColors.car;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2 / this.viewer.zoom;

            // Bird's eye view of vehicle
            ctx.fillRect(-width / 2, -height / 2, width, height);
            ctx.strokeRect(-width / 2, -height / 2, width, height);

            // Draw direction indicator (front)
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(-width / 4, -height / 2, width / 2, height / 6);

            // Draw speed indicator (optional)
            if (vehicle.speed > 0) {
                const speedAlpha = Math.min(vehicle.speed / 100, 1);
                ctx.strokeStyle = `rgba(77, 168, 218, ${speedAlpha})`;
                ctx.lineWidth = 3 / this.viewer.zoom;
                ctx.beginPath();
                ctx.arc(0, 0, width, 0, Math.PI * 2);
                ctx.stroke();
            }

            ctx.restore();
        });
    }

    drawPedestrians(ctx) {
        this.pedestrians.forEach(pedestrian => {
            if (!pedestrian.position) return;

            const { x, y } = pedestrian.position;
            const radius = 5;

            ctx.save();

            // Draw pedestrian as colored dot
            ctx.fillStyle = this.pedestrianColor;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1 / this.viewer.zoom;

            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.stroke();

            // Draw direction indicator if moving
            if (pedestrian.velocity) {
                const vx = pedestrian.velocity.x;
                const vy = pedestrian.velocity.y;
                const speed = Math.sqrt(vx * vx + vy * vy);

                if (speed > 0.1) {
                    ctx.strokeStyle = this.pedestrianColor;
                    ctx.lineWidth = 2 / this.viewer.zoom;
                    ctx.beginPath();
                    ctx.moveTo(x, y);
                    ctx.lineTo(x + vx * 5, y + vy * 5);
                    ctx.stroke();
                }
            }

            ctx.restore();
        });
    }

    drawMainCar(ctx) {
        if (!this.mainCar.position) return;

        const { x, y } = this.mainCar.position;
        const angle = this.mainCar.angle || 0;
        const width = 25;
        const height = 45;

        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);

        // Draw main car with special styling (Yandex taxi style)
        ctx.fillStyle = this.vehicleColors.main;
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3 / this.viewer.zoom;

        // Car body
        ctx.fillRect(-width / 2, -height / 2, width, height);
        ctx.strokeRect(-width / 2, -height / 2, width, height);

        // Taxi indicator (roof light)
        ctx.fillStyle = '#facc15';
        ctx.fillRect(-width / 3, -height / 2 - 5, width * 2 / 3, 5);

        // Front indicator
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(-width / 4, -height / 2, width / 2, height / 5);

        // Glow effect for main car
        ctx.strokeStyle = 'rgba(77, 168, 218, 0.6)';
        ctx.lineWidth = 5 / this.viewer.zoom;
        ctx.strokeRect(-width / 2 - 3, -height / 2 - 3, width + 6, height + 6);

        ctx.restore();

        // Draw destination marker if set
        if (this.mainCar.destination) {
            this.drawDestinationMarker(ctx, this.mainCar.destination);
        }

        // Draw waypoints
        if (this.mainCar.waypoints && this.mainCar.waypoints.length > 0) {
            this.mainCar.waypoints.forEach((waypoint, index) => {
                this.drawWaypointMarker(ctx, waypoint, index + 1);
            });
        }
    }

    drawDestinationMarker(ctx, destination) {
        const { x, y } = destination;

        ctx.save();
        ctx.translate(x, y);

        // Draw flag marker
        ctx.strokeStyle = '#4ade80';
        ctx.lineWidth = 3 / this.viewer.zoom;
        ctx.fillStyle = '#4ade80';

        // Pole
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -30);
        ctx.stroke();

        // Flag
        ctx.beginPath();
        ctx.moveTo(0, -30);
        ctx.lineTo(20, -25);
        ctx.lineTo(0, -20);
        ctx.closePath();
        ctx.fill();

        // Base circle
        ctx.beginPath();
        ctx.arc(0, 0, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#4ade80';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2 / this.viewer.zoom;
        ctx.stroke();

        ctx.restore();
    }

    drawWaypointMarker(ctx, waypoint, number) {
        const { x, y } = waypoint;

        ctx.save();
        ctx.translate(x, y);

        // Draw numbered waypoint
        ctx.fillStyle = '#60a5fa';
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2 / this.viewer.zoom;

        ctx.beginPath();
        ctx.arc(0, 0, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Draw number
        ctx.fillStyle = '#ffffff';
        ctx.font = `${12 / this.viewer.zoom}px monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(number.toString(), 0, 0);

        ctx.restore();
    }

    drawPaths(ctx) {
        // Draw paths for all vehicles
        this.vehicles.forEach(vehicle => {
            if (vehicle.path && vehicle.path.length > 1) {
                ctx.strokeStyle = 'rgba(96, 165, 250, 0.3)';
                ctx.lineWidth = 2 / this.viewer.zoom;
                ctx.setLineDash([5 / this.viewer.zoom, 5 / this.viewer.zoom]);

                ctx.beginPath();
                ctx.moveTo(vehicle.path[0].x, vehicle.path[0].y);
                for (let i = 1; i < vehicle.path.length; i++) {
                    ctx.lineTo(vehicle.path[i].x, vehicle.path[i].y);
                }
                ctx.stroke();
                ctx.setLineDash([]);
            }
        });

        // Draw main car path with special styling
        if (this.mainCar && this.mainCar.path && this.mainCar.path.length > 1) {
            ctx.strokeStyle = 'rgba(77, 168, 218, 0.6)';
            ctx.lineWidth = 3 / this.viewer.zoom;
            ctx.setLineDash([10 / this.viewer.zoom, 5 / this.viewer.zoom]);

            ctx.beginPath();
            ctx.moveTo(this.mainCar.path[0].x, this.mainCar.path[0].y);
            for (let i = 1; i < this.mainCar.path.length; i++) {
                ctx.lineTo(this.mainCar.path[i].x, this.mainCar.path[i].y);
            }
            ctx.stroke();
            ctx.setLineDash([]);
        }
    }

    drawSensorVisualization(ctx) {
        if (!this.mainCar || !this.mainCar.position) return;

        const { x, y } = this.mainCar.position;
        const angle = this.mainCar.angle || 0;

        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(angle);

        // Draw LIDAR range (circular)
        ctx.strokeStyle = 'rgba(77, 168, 218, 0.3)';
        ctx.lineWidth = 2 / this.viewer.zoom;
        ctx.setLineDash([10 / this.viewer.zoom, 5 / this.viewer.zoom]);
        ctx.beginPath();
        ctx.arc(0, 0, 100, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw camera FOV (cone)
        ctx.fillStyle = 'rgba(96, 165, 250, 0.1)';
        ctx.strokeStyle = 'rgba(96, 165, 250, 0.5)';
        ctx.lineWidth = 2 / this.viewer.zoom;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        const fovAngle = Math.PI / 3; // 60 degrees
        const fovRange = 150;
        ctx.arc(0, 0, fovRange, -fovAngle / 2, fovAngle / 2);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Draw radar sectors
        ctx.strokeStyle = 'rgba(250, 204, 21, 0.4)';
        ctx.lineWidth = 1 / this.viewer.zoom;
        for (let i = 0; i < 8; i++) {
            const sectorAngle = (Math.PI * 2 / 8) * i;
            ctx.beginPath();
            ctx.moveTo(0, 0);
            ctx.lineTo(Math.cos(sectorAngle) * 80, Math.sin(sectorAngle) * 80);
            ctx.stroke();
        }

        ctx.restore();
    }

    // Update entity data
    updateEntities(data) {
        if (data.vehicles) this.vehicles = data.vehicles;
        if (data.pedestrians) this.pedestrians = data.pedestrians;
        if (data.mainCar) this.mainCar = data.mainCar;
    }

    setMainCar(position, angle = 0) {
        this.mainCar = {
            position: position,
            angle: angle,
            destination: null,
            waypoints: []
        };
    }

    setDestination(position) {
        if (this.mainCar) {
            this.mainCar.destination = position;
        }
    }

    addWaypoint(position) {
        if (this.mainCar) {
            if (!this.mainCar.waypoints) this.mainCar.waypoints = [];
            this.mainCar.waypoints.push(position);
        }
    }

    clearRoute() {
        if (this.mainCar) {
            this.mainCar.destination = null;
            this.mainCar.waypoints = [];
            this.mainCar.path = null;
        }
    }

    // Generate demo entities for testing
    generateDemoEntities(count = 10) {
        if (!this.viewer || !this.viewer.mapWidth) return;

        const width = this.viewer.mapWidth;
        const height = this.viewer.mapHeight;

        // Generate random vehicles
        this.vehicles = [];
        for (let i = 0; i < count; i++) {
            this.vehicles.push({
                id: `vehicle_${i}`,
                type: Math.random() > 0.8 ? 'truck' : 'car',
                position: {
                    x: Math.random() * width,
                    y: Math.random() * height
                },
                angle: Math.random() * Math.PI * 2,
                speed: Math.random() * 60 + 20
            });
        }

        // Generate random pedestrians
        this.pedestrians = [];
        for (let i = 0; i < count * 2; i++) {
            const vx = (Math.random() - 0.5) * 2;
            const vy = (Math.random() - 0.5) * 2;
            this.pedestrians.push({
                id: `pedestrian_${i}`,
                position: {
                    x: Math.random() * width,
                    y: Math.random() * height
                },
                velocity: { x: vx, y: vy }
            });
        }

        // Animate demo entities
        this.animateDemoEntities();
    }

    animateDemoEntities() {
        if (!this.isRunning) return;

        const width = this.viewer.mapWidth;
        const height = this.viewer.mapHeight;

        // Animate vehicles
        this.vehicles.forEach(vehicle => {
            const speed = vehicle.speed / 60; // pixels per frame
            vehicle.position.x += Math.cos(vehicle.angle) * speed;
            vehicle.position.y += Math.sin(vehicle.angle) * speed;

            // Wrap around
            if (vehicle.position.x < 0) vehicle.position.x = width;
            if (vehicle.position.x > width) vehicle.position.x = 0;
            if (vehicle.position.y < 0) vehicle.position.y = height;
            if (vehicle.position.y > height) vehicle.position.y = 0;

            // Random direction changes
            if (Math.random() < 0.01) {
                vehicle.angle += (Math.random() - 0.5) * 0.5;
            }
        });

        // Animate pedestrians
        this.pedestrians.forEach(pedestrian => {
            pedestrian.position.x += pedestrian.velocity.x;
            pedestrian.position.y += pedestrian.velocity.y;

            // Wrap around
            if (pedestrian.position.x < 0) pedestrian.position.x = width;
            if (pedestrian.position.x > width) pedestrian.position.x = 0;
            if (pedestrian.position.y < 0) pedestrian.position.y = height;
            if (pedestrian.position.y > height) pedestrian.position.y = 0;

            // Random velocity changes
            if (Math.random() < 0.02) {
                pedestrian.velocity.x += (Math.random() - 0.5) * 0.5;
                pedestrian.velocity.y += (Math.random() - 0.5) * 0.5;
                // Limit speed
                const speed = Math.sqrt(pedestrian.velocity.x ** 2 + pedestrian.velocity.y ** 2);
                if (speed > 2) {
                    pedestrian.velocity.x = (pedestrian.velocity.x / speed) * 2;
                    pedestrian.velocity.y = (pedestrian.velocity.y / speed) * 2;
                }
            }
        });

        setTimeout(() => this.animateDemoEntities(), 1000 / 60);
    }

    updateFPSDisplay() {
        const elements = ['fpsCounter', 'simFps'];
        elements.forEach(id => {
            const elem = document.getElementById(id);
            if (elem) elem.textContent = this.fps;
        });
    }
}

// Global animation system
let animationSystem = null;

// Initialize after map viewer is ready
function initAnimationSystem() {
    if (mapViewer) {
        animationSystem = new AnimationSystem(mapViewer);
    }
}
