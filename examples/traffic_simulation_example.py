#!/usr/bin/env python3
"""
Traffic Simulation Example

This script demonstrates how to use the traffic simulation module
with a simple text-based visualization.
"""

import sys
import os
import time
import math

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from traffic_simulation import (
    TrafficManager,
    VehicleType,
    get_behavior_description
)


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def render_ascii_map(manager, width=80, height=40):
    """
    Render the traffic simulation as ASCII art.

    Args:
        manager: TrafficManager instance
        width: Terminal width
        height: Terminal height
    """
    # Create empty grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]

    # Map coordinates to grid
    scale_x = width / manager.map_width
    scale_y = height / manager.map_height

    # Draw vehicles
    for vehicle in manager.vehicles.values():
        grid_x = int(vehicle.x * scale_x)
        grid_y = int(vehicle.y * scale_y)

        if 0 <= grid_x < width and 0 <= grid_y < height:
            if vehicle.type == VehicleType.CAR:
                grid[grid_y][grid_x] = 'C'
            elif vehicle.type == VehicleType.TRUCK:
                grid[grid_y][grid_x] = 'T'
            else:
                grid[grid_y][grid_x] = 'X'

    # Draw pedestrians
    for pedestrian in manager.pedestrians.values():
        grid_x = int(pedestrian.x * scale_x)
        grid_y = int(pedestrian.y * scale_y)

        if 0 <= grid_x < width and 0 <= grid_y < height:
            grid[grid_y][grid_x] = 'p'

    # Draw borders
    border = '+' + '-' * width + '+'
    print(border)
    for row in grid:
        print('|' + ''.join(row) + '|')
    print(border)


def print_statistics(manager, elapsed_time):
    """Print simulation statistics."""
    stats = manager.get_statistics()

    print(f"\n{'=' * 80}")
    print(f"TRAFFIC SIMULATION STATISTICS (t={elapsed_time:.1f}s)")
    print(f"{'=' * 80}")
    print(f"Active Entities:")
    print(f"  Vehicles: {stats['vehicles_active']:3d} | Pedestrians: {stats['pedestrians_active']:3d}")
    print(f"\nTotal Spawned:")
    print(f"  Vehicles: {stats['vehicles_spawned']:3d} | Pedestrians: {stats['pedestrians_spawned']:3d}")
    print(f"\nTotal Despawned:")
    print(f"  Vehicles: {stats['vehicles_despawned']:3d} | Pedestrians: {stats['pedestrians_despawned']:3d}")
    print(f"\nSettings:")
    print(f"  Traffic Density: {stats['traffic_density']:.1%}")
    print(f"  Pedestrian Density: {stats['pedestrian_density']:.1%}")
    print(f"  Global Temperature: {stats['global_temperature']:.2f} "
          f"({get_behavior_description(stats['global_temperature'])})")

    # Show some random vehicle info
    if manager.vehicles:
        print(f"\nRandom Vehicle Sample:")
        sample = list(manager.vehicles.values())[:3]
        for v in sample:
            print(f"  {v.type.value.upper()} #{v.id}: "
                  f"pos=({v.x:.0f}, {v.y:.0f}), "
                  f"speed={v.speed:.1f} km/h, "
                  f"state={v.state.value}, "
                  f"temp={v.behavior.temperature:.2f}")

    print(f"{'=' * 80}\n")


def main():
    """Run the traffic simulation example."""
    print("=" * 80)
    print("Traffic Simulation Example")
    print("=" * 80)
    print("\nThis example demonstrates the traffic simulation module")
    print("with ASCII visualization in the terminal.\n")

    # Configuration
    print("Configuration:")
    traffic_density = 0.4
    pedestrian_density = 0.3
    global_temperature = 0.5
    simulation_speed = 1.0  # 1.0 = real-time
    duration = 30.0  # seconds

    print(f"  Traffic Density: {traffic_density:.0%}")
    print(f"  Pedestrian Density: {pedestrian_density:.0%}")
    print(f"  Global Temperature: {global_temperature:.2f}")
    print(f"  Simulation Speed: {simulation_speed}x")
    print(f"  Duration: {duration}s")

    input("\nPress ENTER to start simulation...")

    # Create traffic manager
    map_data = {
        'map_bounds': {'width': 1000.0, 'height': 1000.0}
    }
    manager = TrafficManager(map_data)
    manager.set_traffic_density(traffic_density)
    manager.set_pedestrian_density(pedestrian_density)
    manager.set_global_temperature(global_temperature)

    # Simulation parameters
    dt = 0.1  # 100ms time step
    display_interval = 1.0  # Update display every 1 second
    elapsed_time = 0.0
    time_since_display = 0.0

    print("\nStarting simulation...\n")

    try:
        while elapsed_time < duration:
            # Update simulation
            manager.update(dt)
            elapsed_time += dt
            time_since_display += dt

            # Update display
            if time_since_display >= display_interval:
                clear_screen()
                print("TRAFFIC SIMULATION (ASCII View)")
                print("Legend: C=Car, T=Truck, X=Taxi, p=Pedestrian\n")

                # Render map
                render_ascii_map(manager, width=70, height=25)

                # Show statistics
                print_statistics(manager, elapsed_time)

                time_since_display = 0.0

            # Real-time delay
            time.sleep(dt / simulation_speed)

    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")

    # Final statistics
    clear_screen()
    print("\nSIMULATION COMPLETE\n")
    print_statistics(manager, elapsed_time)

    print("Example completed successfully!")


if __name__ == '__main__':
    main()
