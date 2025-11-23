"""
Traffic manager for the simulation.

This module manages all traffic entities including vehicles and pedestrians,
handles spawning/despawning, traffic density control, and spatial partitioning
for efficient collision detection.
"""

import math
import random
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict

from .vehicle import Vehicle, VehicleType
from .pedestrian import Pedestrian, create_pedestrian_group
from .behavior import generate_temperature_distribution


class SpatialGrid:
    """
    Spatial partitioning grid for efficient collision detection and queries.

    Divides the map into cells and tracks which entities are in each cell.
    """

    def __init__(self, cell_size: float = 50.0):
        """
        Initialize spatial grid.

        Args:
            cell_size: Size of each grid cell in meters
        """
        self.cell_size = cell_size
        self.grid: Dict[Tuple[int, int], Set[int]] = defaultdict(set)
        self.entity_cells: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)

    def _get_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Get grid cell for a position."""
        return (int(x // self.cell_size), int(y // self.cell_size))

    def _get_cells_for_entity(self, x: float, y: float, radius: float) -> List[Tuple[int, int]]:
        """Get all cells that an entity occupies."""
        cells = []
        min_cell_x = int((x - radius) // self.cell_size)
        max_cell_x = int((x + radius) // self.cell_size)
        min_cell_y = int((y - radius) // self.cell_size)
        max_cell_y = int((y + radius) // self.cell_size)

        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                cells.append((cx, cy))

        return cells

    def insert(self, entity_id: int, x: float, y: float, radius: float) -> None:
        """Insert an entity into the grid."""
        cells = self._get_cells_for_entity(x, y, radius)
        for cell in cells:
            self.grid[cell].add(entity_id)
            self.entity_cells[entity_id].add(cell)

    def remove(self, entity_id: int) -> None:
        """Remove an entity from the grid."""
        if entity_id in self.entity_cells:
            for cell in self.entity_cells[entity_id]:
                self.grid[cell].discard(entity_id)
            del self.entity_cells[entity_id]

    def update(self, entity_id: int, x: float, y: float, radius: float) -> None:
        """Update an entity's position in the grid."""
        self.remove(entity_id)
        self.insert(entity_id, x, y, radius)

    def query_radius(self, x: float, y: float, radius: float) -> Set[int]:
        """Query all entities within a radius of a position."""
        cells = self._get_cells_for_entity(x, y, radius)
        entity_ids = set()
        for cell in cells:
            entity_ids.update(self.grid.get(cell, set()))
        return entity_ids

    def query_rect(self, min_x: float, min_y: float, max_x: float, max_y: float) -> Set[int]:
        """Query all entities within a rectangular area."""
        min_cell_x = int(min_x // self.cell_size)
        max_cell_x = int(max_x // self.cell_size)
        min_cell_y = int(min_y // self.cell_size)
        max_cell_y = int(max_y // self.cell_size)

        entity_ids = set()
        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                entity_ids.update(self.grid.get((cx, cy), set()))

        return entity_ids

    def clear(self) -> None:
        """Clear the grid."""
        self.grid.clear()
        self.entity_cells.clear()


class TrafficManager:
    """
    Manages all traffic entities in the simulation.

    Handles spawning, despawning, updates, collision detection, and
    provides spatial queries for sensors.
    """

    def __init__(self, map_data: Optional[Dict] = None):
        """
        Initialize traffic manager.

        Args:
            map_data: Map data from Agent 1 (zones, roads, etc.)
        """
        self.map_data = map_data

        # Entity storage
        self.vehicles: Dict[int, Vehicle] = {}
        self.pedestrians: Dict[int, Pedestrian] = {}

        # Spatial partitioning
        self.spatial_grid = SpatialGrid(cell_size=50.0)

        # Traffic control parameters
        self.traffic_density = 0.5  # 0.0-1.0
        self.pedestrian_density = 0.5  # 0.0-1.0
        self.global_temperature = 0.5  # 0.0-1.0, affects average driver aggression

        # Spawning parameters
        self.max_vehicles = 100
        self.max_pedestrians = 50
        self.spawn_interval = 2.0  # seconds
        self.time_since_spawn = 0.0

        # Statistics
        self.total_vehicles_spawned = 0
        self.total_pedestrians_spawned = 0
        self.total_vehicles_despawned = 0
        self.total_pedestrians_despawned = 0

        # Map bounds (will be set from map_data)
        self.map_width = 1000.0
        self.map_height = 1000.0
        if map_data and 'map_bounds' in map_data:
            self.map_width = map_data['map_bounds'].get('width', 1000.0)
            self.map_height = map_data['map_bounds'].get('height', 1000.0)

        # Spawn points (will be populated from map_data)
        self.vehicle_spawn_points = []
        self.pedestrian_spawn_points = []
        self._initialize_spawn_points()

    def _initialize_spawn_points(self) -> None:
        """Initialize spawn points from map data or use defaults."""
        if self.map_data and 'roads' in self.map_data:
            # TODO: Extract actual spawn points from road network
            # For now, use edge points
            pass

        # Default spawn points at map edges
        if not self.vehicle_spawn_points:
            margin = 50.0
            # Top edge
            for i in range(5):
                x = margin + (self.map_width - 2 * margin) * i / 4
                self.vehicle_spawn_points.append((x, margin, 180.0))  # Heading south

            # Bottom edge
            for i in range(5):
                x = margin + (self.map_width - 2 * margin) * i / 4
                self.vehicle_spawn_points.append((x, self.map_height - margin, 0.0))  # Heading north

            # Left edge
            for i in range(5):
                y = margin + (self.map_height - 2 * margin) * i / 4
                self.vehicle_spawn_points.append((margin, y, 90.0))  # Heading east

            # Right edge
            for i in range(5):
                y = margin + (self.map_height - 2 * margin) * i / 4
                self.vehicle_spawn_points.append((self.map_width - margin, y, 270.0))  # Heading west

        # Pedestrian spawn points (sidewalks, near edges)
        if not self.pedestrian_spawn_points:
            margin = 30.0
            for i in range(20):
                x = random.uniform(margin, self.map_width - margin)
                y = random.uniform(margin, self.map_height - margin)
                self.pedestrian_spawn_points.append((x, y))

    def update(self, dt: float) -> None:
        """
        Update all traffic entities.

        Args:
            dt: Time step in seconds
        """
        # Update spawning
        self.time_since_spawn += dt
        if self.time_since_spawn >= self.spawn_interval:
            self._try_spawn_entities()
            self.time_since_spawn = 0.0

        # Update vehicles
        vehicles_to_remove = []
        for vehicle_id, vehicle in list(self.vehicles.items()):
            # Update vehicle
            vehicle.update(dt, self.map_data)

            # Update spatial grid
            self.spatial_grid.update(vehicle_id, vehicle.x, vehicle.y, vehicle.collision_radius)

            # Check for despawning
            if self._should_despawn_vehicle(vehicle):
                vehicles_to_remove.append(vehicle_id)

        # Remove despawned vehicles
        for vehicle_id in vehicles_to_remove:
            self.despawn_vehicle(vehicle_id)

        # Update pedestrians
        pedestrians_to_remove = []
        for ped_id, pedestrian in list(self.pedestrians.items()):
            # Get nearby vehicles for awareness
            nearby_vehicle_ids = self.spatial_grid.query_radius(
                pedestrian.x, pedestrian.y, 30.0
            )
            nearby_vehicles = [
                self.vehicles[vid] for vid in nearby_vehicle_ids
                if vid in self.vehicles
            ]

            # Update pedestrian
            pedestrian.update(dt, self.map_data, nearby_vehicles)

            # Update spatial grid
            self.spatial_grid.update(ped_id + 1000000, pedestrian.x, pedestrian.y, pedestrian.radius)

            # Check for despawning
            if self._should_despawn_pedestrian(pedestrian):
                pedestrians_to_remove.append(ped_id)

        # Remove despawned pedestrians
        for ped_id in pedestrians_to_remove:
            self.despawn_pedestrian(ped_id)

        # Update vehicle awareness (find vehicle ahead)
        self._update_vehicle_awareness()

        # Check collisions
        self._check_collisions()

    def _try_spawn_entities(self) -> None:
        """Try to spawn new vehicles and pedestrians based on density settings."""
        # Calculate target counts based on density
        target_vehicles = int(self.max_vehicles * self.traffic_density)
        target_pedestrians = int(self.max_pedestrians * self.pedestrian_density)

        # Spawn vehicles
        if len(self.vehicles) < target_vehicles:
            num_to_spawn = min(3, target_vehicles - len(self.vehicles))
            for _ in range(num_to_spawn):
                self.spawn_vehicle()

        # Spawn pedestrians
        if len(self.pedestrians) < target_pedestrians:
            num_to_spawn = min(2, target_pedestrians - len(self.pedestrians))
            for _ in range(num_to_spawn):
                # Sometimes spawn groups
                if random.random() < 0.2:  # 20% chance of group
                    self.spawn_pedestrian_group(random.randint(2, 4))
                else:
                    self.spawn_pedestrian()

    def spawn_vehicle(
        self,
        vehicle_type: Optional[VehicleType] = None,
        position: Optional[Tuple[float, float]] = None,
        heading: Optional[float] = None,
        temperature: Optional[float] = None
    ) -> Optional[Vehicle]:
        """
        Spawn a new vehicle.

        Args:
            vehicle_type: Type of vehicle (random if None)
            position: Spawn position (random spawn point if None)
            heading: Initial heading (from spawn point if None)
            temperature: Behavior temperature (from distribution if None)

        Returns:
            Spawned Vehicle or None if failed
        """
        if len(self.vehicles) >= self.max_vehicles:
            return None

        # Choose vehicle type
        if vehicle_type is None:
            # 80% cars, 20% trucks
            vehicle_type = VehicleType.CAR if random.random() < 0.8 else VehicleType.TRUCK

        # Choose spawn point
        if position is None and self.vehicle_spawn_points:
            spawn_point = random.choice(self.vehicle_spawn_points)
            position = (spawn_point[0], spawn_point[1])
            if heading is None:
                heading = spawn_point[2]
        elif position is None:
            # Fallback to random position
            position = (
                random.uniform(50, self.map_width - 50),
                random.uniform(50, self.map_height - 50)
            )

        if heading is None:
            heading = random.uniform(0.0, 360.0)

        # Choose temperature
        if temperature is None:
            temperatures = generate_temperature_distribution(1, self.global_temperature, 0.2)
            temperature = temperatures[0]

        # Create vehicle
        vehicle = Vehicle(vehicle_type, position, heading, temperature)

        # Generate a simple path (in reality, would use road network)
        self._generate_vehicle_path(vehicle)

        # Add to manager
        self.vehicles[vehicle.id] = vehicle
        self.spatial_grid.insert(vehicle.id, vehicle.x, vehicle.y, vehicle.collision_radius)

        self.total_vehicles_spawned += 1

        return vehicle

    def spawn_pedestrian(
        self,
        position: Optional[Tuple[float, float]] = None,
        caution_level: Optional[float] = None
    ) -> Optional[Pedestrian]:
        """
        Spawn a new pedestrian.

        Args:
            position: Spawn position (random spawn point if None)
            caution_level: Caution level (random if None)

        Returns:
            Spawned Pedestrian or None if failed
        """
        if len(self.pedestrians) >= self.max_pedestrians:
            return None

        # Choose spawn point
        if position is None and self.pedestrian_spawn_points:
            position = random.choice(self.pedestrian_spawn_points)
        elif position is None:
            position = (
                random.uniform(50, self.map_width - 50),
                random.uniform(50, self.map_height - 50)
            )

        # Choose caution level
        if caution_level is None:
            caution_level = random.uniform(0.3, 0.7)

        # Create pedestrian
        pedestrian = Pedestrian(position, caution_level)

        # Add to manager
        self.pedestrians[pedestrian.id] = pedestrian
        self.spatial_grid.insert(
            pedestrian.id + 1000000,  # Offset ID to avoid collision with vehicles
            pedestrian.x,
            pedestrian.y,
            pedestrian.radius
        )

        self.total_pedestrians_spawned += 1

        return pedestrian

    def spawn_pedestrian_group(
        self,
        count: int,
        position: Optional[Tuple[float, float]] = None
    ) -> List[Pedestrian]:
        """
        Spawn a group of pedestrians.

        Args:
            count: Number of pedestrians in group
            position: Center position for group

        Returns:
            List of spawned pedestrians
        """
        if position is None and self.pedestrian_spawn_points:
            position = random.choice(self.pedestrian_spawn_points)
        elif position is None:
            position = (
                random.uniform(50, self.map_width - 50),
                random.uniform(50, self.map_height - 50)
            )

        group = create_pedestrian_group(position, count)

        spawned = []
        for pedestrian in group:
            if len(self.pedestrians) < self.max_pedestrians:
                self.pedestrians[pedestrian.id] = pedestrian
                self.spatial_grid.insert(
                    pedestrian.id + 1000000,
                    pedestrian.x,
                    pedestrian.y,
                    pedestrian.radius
                )
                self.total_pedestrians_spawned += 1
                spawned.append(pedestrian)

        return spawned

    def despawn_vehicle(self, vehicle_id: int) -> None:
        """
        Despawn a vehicle.

        Args:
            vehicle_id: ID of vehicle to remove
        """
        if vehicle_id in self.vehicles:
            self.spatial_grid.remove(vehicle_id)
            del self.vehicles[vehicle_id]
            self.total_vehicles_despawned += 1

    def despawn_pedestrian(self, pedestrian_id: int) -> None:
        """
        Despawn a pedestrian.

        Args:
            pedestrian_id: ID of pedestrian to remove
        """
        if pedestrian_id in self.pedestrians:
            self.spatial_grid.remove(pedestrian_id + 1000000)
            del self.pedestrians[pedestrian_id]
            self.total_pedestrians_despawned += 1

    def _should_despawn_vehicle(self, vehicle: Vehicle) -> bool:
        """Check if vehicle should be despawned."""
        # Despawn if out of bounds
        margin = 100.0
        if (vehicle.x < -margin or vehicle.x > self.map_width + margin or
            vehicle.y < -margin or vehicle.y > self.map_height + margin):
            return True

        # Despawn if reached end of path
        if vehicle.path and vehicle.current_waypoint_index >= len(vehicle.path):
            return True

        return False

    def _should_despawn_pedestrian(self, pedestrian: Pedestrian) -> bool:
        """Check if pedestrian should be despawned."""
        # Despawn if out of bounds
        margin = 50.0
        if (pedestrian.x < -margin or pedestrian.x > self.map_width + margin or
            pedestrian.y < -margin or pedestrian.y > self.map_height + margin):
            return True

        return False

    def _generate_vehicle_path(self, vehicle: Vehicle) -> None:
        """
        Generate a path for a vehicle.

        Args:
            vehicle: Vehicle to generate path for
        """
        # Simplified path generation
        # In reality, would use A* or similar on road network
        waypoints = []

        # Generate waypoints across the map
        num_waypoints = random.randint(5, 10)
        current_x, current_y = vehicle.x, vehicle.y

        for _ in range(num_waypoints):
            # Move in general direction
            distance = random.uniform(50.0, 150.0)
            angle = random.uniform(-45.0, 45.0) + vehicle.heading
            angle_rad = math.radians(angle)

            next_x = current_x + distance * math.sin(angle_rad)
            next_y = current_y - distance * math.cos(angle_rad)

            # Clamp to map bounds
            next_x = max(50, min(self.map_width - 50, next_x))
            next_y = max(50, min(self.map_height - 50, next_y))

            waypoints.append((next_x, next_y))
            current_x, current_y = next_x, next_y

        vehicle.set_path(waypoints)

    def _update_vehicle_awareness(self) -> None:
        """Update which vehicles are aware of vehicles ahead."""
        for vehicle in self.vehicles.values():
            # Find vehicles ahead in same direction
            ahead_distance = 100.0  # Look ahead distance
            heading_rad = math.radians(vehicle.heading)

            # Calculate look-ahead point
            look_x = vehicle.x + ahead_distance * math.sin(heading_rad)
            look_y = vehicle.y - ahead_distance * math.cos(heading_rad)

            # Query nearby vehicles
            nearby_ids = self.spatial_grid.query_radius(vehicle.x, vehicle.y, ahead_distance)

            closest_vehicle = None
            closest_distance = float('inf')

            for other_id in nearby_ids:
                if other_id == vehicle.id or other_id not in self.vehicles:
                    continue

                other = self.vehicles[other_id]

                # Check if other vehicle is ahead
                dx = other.x - vehicle.x
                dy = other.y - vehicle.y
                distance = math.sqrt(dx * dx + dy * dy)

                # Check if in front (angle check)
                angle_to_other = math.degrees(math.atan2(dx, -dy)) % 360.0
                angle_diff = abs((angle_to_other - vehicle.heading + 180.0) % 360.0 - 180.0)

                if angle_diff < 30.0 and distance < closest_distance:
                    closest_vehicle = other
                    closest_distance = distance

            vehicle.set_vehicle_ahead(closest_vehicle, closest_distance)

    def _check_collisions(self) -> None:
        """Check and handle collisions between entities."""
        # Vehicle-vehicle collisions
        checked_pairs = set()
        for vehicle in self.vehicles.values():
            nearby_ids = self.spatial_grid.query_radius(
                vehicle.x, vehicle.y, vehicle.collision_radius * 2
            )

            for other_id in nearby_ids:
                if other_id == vehicle.id or other_id not in self.vehicles:
                    continue

                # Avoid checking same pair twice
                pair = tuple(sorted([vehicle.id, other_id]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                other = self.vehicles[other_id]
                if vehicle.check_collision(other):
                    # Handle collision (for now, just stop both vehicles)
                    vehicle.stop()
                    other.stop()

        # Vehicle-pedestrian collisions
        for vehicle in self.vehicles.values():
            nearby_ids = self.spatial_grid.query_radius(
                vehicle.x, vehicle.y, vehicle.collision_radius + 5.0
            )

            for entity_id in nearby_ids:
                ped_id = entity_id - 1000000
                if ped_id in self.pedestrians:
                    pedestrian = self.pedestrians[ped_id]
                    if pedestrian.check_vehicle_collision(vehicle):
                        # Handle collision (stop vehicle, pedestrian injured)
                        vehicle.stop()
                        pedestrian.stop()

    def set_traffic_density(self, density: float) -> None:
        """
        Set traffic density.

        Args:
            density: Traffic density (0.0-1.0)
        """
        self.traffic_density = max(0.0, min(1.0, density))

    def set_pedestrian_density(self, density: float) -> None:
        """
        Set pedestrian density.

        Args:
            density: Pedestrian density (0.0-1.0)
        """
        self.pedestrian_density = max(0.0, min(1.0, density))

    def set_global_temperature(self, temperature: float) -> None:
        """
        Set global behavior temperature.

        Args:
            temperature: Global temperature (0.0-1.0)
        """
        self.global_temperature = max(0.0, min(1.0, temperature))

    def get_entities_in_radius(self, x: float, y: float, radius: float) -> Dict[str, List]:
        """
        Query all entities within a radius (for sensors).

        Args:
            x: Center x position
            y: Center y position
            radius: Query radius in meters

        Returns:
            Dictionary with 'vehicles' and 'pedestrians' lists
        """
        entity_ids = self.spatial_grid.query_radius(x, y, radius)

        vehicles = []
        pedestrians = []

        for entity_id in entity_ids:
            if entity_id in self.vehicles:
                vehicle = self.vehicles[entity_id]
                dx = vehicle.x - x
                dy = vehicle.y - y
                if math.sqrt(dx * dx + dy * dy) <= radius:
                    vehicles.append(vehicle)
            else:
                ped_id = entity_id - 1000000
                if ped_id in self.pedestrians:
                    pedestrian = self.pedestrians[ped_id]
                    dx = pedestrian.x - x
                    dy = pedestrian.y - y
                    if math.sqrt(dx * dx + dy * dy) <= radius:
                        pedestrians.append(pedestrian)

        return {
            'vehicles': vehicles,
            'pedestrians': pedestrians
        }

    def get_all_entities(self) -> Dict[str, Any]:
        """
        Get all entities for rendering.

        Returns:
            Dictionary with all entity data
        """
        return {
            'vehicles': [v.to_dict() for v in self.vehicles.values()],
            'pedestrians': [p.to_dict() for p in self.pedestrians.values()]
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get traffic statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            'vehicles_active': len(self.vehicles),
            'pedestrians_active': len(self.pedestrians),
            'vehicles_spawned': self.total_vehicles_spawned,
            'vehicles_despawned': self.total_vehicles_despawned,
            'pedestrians_spawned': self.total_pedestrians_spawned,
            'pedestrians_despawned': self.total_pedestrians_despawned,
            'traffic_density': self.traffic_density,
            'pedestrian_density': self.pedestrian_density,
            'global_temperature': self.global_temperature
        }

    def clear(self) -> None:
        """Clear all entities."""
        self.vehicles.clear()
        self.pedestrians.clear()
        self.spatial_grid.clear()

    def __repr__(self) -> str:
        return (f"TrafficManager(vehicles={len(self.vehicles)}, "
                f"pedestrians={len(self.pedestrians)})")
