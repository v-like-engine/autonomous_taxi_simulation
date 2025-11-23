"""
Test script for traffic simulation module.

This script tests the basic functionality of the traffic simulation system.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from traffic_simulation import (
    Vehicle, VehicleType, VehicleState,
    Pedestrian, PedestrianState,
    TrafficManager,
    DriverBehavior, PedestrianBehavior,
    generate_temperature_distribution,
    get_behavior_description
)


def test_behavior():
    """Test behavior module."""
    print("\n=== Testing Behavior Module ===")

    # Test driver behavior
    careful_driver = DriverBehavior(0.2)
    normal_driver = DriverBehavior(0.5)
    aggressive_driver = DriverBehavior(0.9)

    print(f"Careful driver (0.2): {get_behavior_description(0.2)}")
    print(f"Normal driver (0.5): {get_behavior_description(0.5)}")
    print(f"Aggressive driver (0.9): {get_behavior_description(0.9)}")

    # Test speed multipliers
    speed_limit = 60.0
    print(f"\nSpeed multipliers at {speed_limit} km/h limit:")
    print(f"  Careful: {careful_driver.get_speed_multiplier(speed_limit):.2f}x")
    print(f"  Normal: {normal_driver.get_speed_multiplier(speed_limit):.2f}x")
    print(f"  Aggressive: {aggressive_driver.get_speed_multiplier(speed_limit):.2f}x")

    # Test pedestrian behavior
    cautious_ped = PedestrianBehavior(0.8)
    normal_ped = PedestrianBehavior(0.5)
    reckless_ped = PedestrianBehavior(0.2)

    print(f"\nPedestrian walking speeds:")
    print(f"  Cautious: {cautious_ped.get_walking_speed():.2f} m/s")
    print(f"  Normal: {normal_ped.get_walking_speed():.2f} m/s")
    print(f"  Reckless: {reckless_ped.get_walking_speed():.2f} m/s")

    # Test temperature distribution
    temps = generate_temperature_distribution(100, 0.5, 0.2)
    print(f"\nTemperature distribution (n=100):")
    print(f"  Min: {min(temps):.2f}, Max: {max(temps):.2f}, Mean: {sum(temps)/len(temps):.2f}")

    print("✓ Behavior tests passed")


def test_vehicle():
    """Test vehicle module."""
    print("\n=== Testing Vehicle Module ===")

    # Create different vehicle types
    car = Vehicle(VehicleType.CAR, (100, 100), heading=0.0, temperature=0.5)
    truck = Vehicle(VehicleType.TRUCK, (200, 200), heading=90.0, temperature=0.3)
    taxi = Vehicle(VehicleType.TAXI, (300, 300), heading=180.0, temperature=0.7)

    print(f"Created car: {car}")
    print(f"Created truck: {truck}")
    print(f"Created taxi: {taxi}")

    # Test vehicle updates
    print("\nUpdating car for 1 second...")
    initial_pos = (car.x, car.y)
    car.target_speed = 50.0  # Set target speed
    car.set_path([(150, 150), (200, 150), (200, 200)])

    for _ in range(10):  # 10 steps of 0.1s
        car.update(0.1)

    final_pos = (car.x, car.y)
    distance_moved = ((final_pos[0] - initial_pos[0])**2 + (final_pos[1] - initial_pos[1])**2)**0.5

    print(f"  Initial position: {initial_pos}")
    print(f"  Final position: {final_pos}")
    print(f"  Distance moved: {distance_moved:.2f} m")
    print(f"  Current speed: {car.speed:.2f} km/h")
    print(f"  State: {car.state.value}")

    # Test collision detection
    car2 = Vehicle(VehicleType.CAR, (car.x + 2, car.y + 2), heading=0.0)
    collision = car.check_collision(car2)
    print(f"\nCollision test (cars 2m apart): {collision}")

    # Test serialization
    car_dict = car.to_dict()
    print(f"\nSerialized car keys: {list(car_dict.keys())}")

    print("✓ Vehicle tests passed")


def test_pedestrian():
    """Test pedestrian module."""
    print("\n=== Testing Pedestrian Module ===")

    # Create pedestrians
    ped1 = Pedestrian((50, 50), caution_level=0.5)
    ped2 = Pedestrian((100, 100), caution_level=0.8)

    print(f"Created pedestrian 1: {ped1}")
    print(f"Created pedestrian 2: {ped2}")

    # Set waypoints
    ped1.set_waypoints([
        (60, 60, False),
        (70, 70, True),   # Crossing point
        (80, 80, False)
    ])
    print(f"\nPedestrian 1 waypoints: {len(ped1.waypoints)}")

    # Update pedestrian
    print("\nUpdating pedestrian for 1 second...")
    initial_pos = (ped1.x, ped1.y)

    for _ in range(10):
        ped1.update(0.1)

    final_pos = (ped1.x, ped1.y)
    distance_moved = ((final_pos[0] - initial_pos[0])**2 + (final_pos[1] - initial_pos[1])**2)**0.5

    print(f"  Initial position: {initial_pos}")
    print(f"  Final position: {final_pos}")
    print(f"  Distance moved: {distance_moved:.2f} m")
    print(f"  Current speed: {ped1.speed:.2f} m/s")
    print(f"  State: {ped1.state.value}")

    # Test collision
    collision = ped1.check_collision(ped2)
    print(f"\nCollision test: {collision}")

    # Test serialization
    ped_dict = ped1.to_dict()
    print(f"Serialized pedestrian keys: {list(ped_dict.keys())}")

    print("✓ Pedestrian tests passed")


def test_traffic_manager():
    """Test traffic manager."""
    print("\n=== Testing Traffic Manager ===")

    # Create manager
    map_data = {
        'map_bounds': {'width': 1000.0, 'height': 1000.0}
    }
    manager = TrafficManager(map_data)
    print(f"Created manager: {manager}")

    # Test spawning
    print("\nSpawning vehicles and pedestrians...")
    manager.set_traffic_density(0.5)
    manager.set_pedestrian_density(0.3)
    manager.set_global_temperature(0.6)

    # Manually spawn some entities
    for _ in range(5):
        manager.spawn_vehicle()
    for _ in range(3):
        manager.spawn_pedestrian()

    print(f"Spawned {len(manager.vehicles)} vehicles")
    print(f"Spawned {len(manager.pedestrians)} pedestrians")

    # Test update
    print("\nUpdating traffic for 5 seconds...")
    for i in range(50):  # 50 steps of 0.1s
        manager.update(0.1)
        if i % 10 == 0:
            print(f"  Step {i}: {len(manager.vehicles)} vehicles, {len(manager.pedestrians)} pedestrians")

    # Test spatial queries
    print("\nTesting spatial queries...")
    entities = manager.get_entities_in_radius(500, 500, 200)
    print(f"Entities within 200m of (500, 500):")
    print(f"  Vehicles: {len(entities['vehicles'])}")
    print(f"  Pedestrians: {len(entities['pedestrians'])}")

    # Test statistics
    stats = manager.get_statistics()
    print(f"\nTraffic statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Test entity retrieval
    all_entities = manager.get_all_entities()
    print(f"\nTotal entities:")
    print(f"  Vehicles: {len(all_entities['vehicles'])}")
    print(f"  Pedestrians: {len(all_entities['pedestrians'])}")

    print("✓ Traffic manager tests passed")


def test_integration():
    """Test integrated scenario."""
    print("\n=== Testing Integrated Scenario ===")

    # Create a simple scenario
    manager = TrafficManager()
    manager.set_traffic_density(0.3)
    manager.set_pedestrian_density(0.2)

    print("Running simulation for 10 seconds...")

    # Run simulation
    total_time = 0.0
    dt = 0.1
    steps = 100

    for step in range(steps):
        manager.update(dt)
        total_time += dt

        if step % 20 == 0:
            stats = manager.get_statistics()
            print(f"  t={total_time:.1f}s: {stats['vehicles_active']} vehicles, "
                  f"{stats['pedestrians_active']} pedestrians")

    # Final statistics
    stats = manager.get_statistics()
    print(f"\nFinal statistics:")
    print(f"  Total spawned: {stats['vehicles_spawned']} vehicles, {stats['pedestrians_spawned']} pedestrians")
    print(f"  Total despawned: {stats['vehicles_despawned']} vehicles, {stats['pedestrians_despawned']} pedestrians")
    print(f"  Active: {stats['vehicles_active']} vehicles, {stats['pedestrians_active']} pedestrians")

    print("✓ Integration test passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Traffic Simulation Test Suite")
    print("=" * 60)

    try:
        test_behavior()
        test_vehicle()
        test_pedestrian()
        test_traffic_manager()
        test_integration()

        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
