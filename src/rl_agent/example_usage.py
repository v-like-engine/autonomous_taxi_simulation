"""
Example Usage of RL Agent

This script demonstrates how to use the RL agent in different scenarios:
1. Training from scratch
2. Loading and using a trained model
3. Evaluation
4. Integration with the full system
"""

# NOTE: This is example code. The environment integration will depend on
# how Agent 2 (Traffic Simulation) and Agent 4 (Sensors) are implemented.


def example_1_training_from_scratch():
    """
    Example 1: Train a new agent from scratch.
    """
    print("=" * 60)
    print("Example 1: Training from Scratch")
    print("=" * 60)

    from rl_agent import create_default_agent, Trainer
    from rl_agent.training import MockEnvironment  # Replace with real environment

    # Create agent
    agent = create_default_agent(device='cpu')  # Use 'cuda' for GPU
    print("Agent created with default configuration")

    # Create environment (replace with real environment)
    # env = RealEnvironment()  # From Agent 2 + Agent 4
    env = MockEnvironment()  # Mock for demonstration

    # Configure training
    training_config = {
        'max_episodes': 1000,
        'max_steps_per_episode': 2000,
        'eval_frequency': 50,
        'save_frequency': 100,
        'checkpoint_dir': 'checkpoints/rl_agent',
        'log_dir': 'logs/rl_agent',
    }

    # Create trainer
    trainer = Trainer(agent, env, training_config)

    # Train
    print("Starting training...")
    trainer.train()
    print("Training complete!")


def example_2_custom_configuration():
    """
    Example 2: Train with custom hyperparameters.
    """
    print("=" * 60)
    print("Example 2: Custom Configuration")
    print("=" * 60)

    from rl_agent import PPOAgent

    # Custom agent configuration
    agent_config = {
        'device': 'cpu',
        'learning_rate': 1e-4,  # Lower learning rate
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_epsilon': 0.2,
        'value_loss_coef': 0.5,
        'entropy_coef': 0.02,  # Higher exploration
        'n_epochs': 15,  # More update epochs
        'batch_size': 128,  # Larger batch size
        'buffer_size': 4096,  # Larger buffer
        'hidden_dim': 512,  # Larger network
    }

    agent = PPOAgent(agent_config)
    print("Agent created with custom configuration")
    print(f"  Learning rate: {agent.lr}")
    print(f"  Hidden dim: {agent_config['hidden_dim']}")
    print(f"  Buffer size: {agent.buffer_size}")


def example_3_load_and_use():
    """
    Example 3: Load a trained model and use it.
    """
    print("=" * 60)
    print("Example 3: Load and Use Trained Model")
    print("=" * 60)

    from rl_agent import create_default_agent

    # Create agent
    agent = create_default_agent(device='cpu')

    # Load trained model
    checkpoint_path = 'checkpoints/rl_agent/best_model.pt'
    try:
        agent.load(checkpoint_path)
        print(f"Model loaded from {checkpoint_path}")
    except FileNotFoundError:
        print(f"Checkpoint not found: {checkpoint_path}")
        print("Train a model first using example_1_training_from_scratch()")
        return

    # Use in inference mode
    from rl_agent.training import MockEnvironment
    env = MockEnvironment()
    env.reset()

    print("\nRunning inference for 100 steps...")
    total_reward = 0

    for step in range(100):
        sensor_data = env.get_sensor_data()

        # Get action (deterministic for inference)
        control, debug_info = agent.select_action(sensor_data, deterministic=True)

        # Execute action
        next_sensor_data, info, done = env.step(control)

        total_reward += info.get('reward', 0)

        if step % 20 == 0:
            print(f"  Step {step}: Speed={sensor_data['telemetry']['speed']:.1f} km/h, "
                  f"Throttle={control['throttle']:.2f}, Steering={control['steering']:.2f}")

        if done:
            print(f"  Episode ended at step {step}")
            break

    print(f"Total reward: {total_reward:.2f}")


def example_4_evaluation():
    """
    Example 4: Evaluate a trained model.
    """
    print("=" * 60)
    print("Example 4: Evaluation")
    print("=" * 60)

    from rl_agent import create_default_agent
    from rl_agent.training import MockEnvironment

    # Load agent
    agent = create_default_agent()

    try:
        agent.load('checkpoints/rl_agent/best_model.pt')
    except FileNotFoundError:
        print("No trained model found. Using untrained agent for demonstration.")

    env = MockEnvironment()

    # Run multiple evaluation episodes
    n_episodes = 10
    results = {
        'rewards': [],
        'lengths': [],
        'successes': [],
        'collisions': [],
    }

    print(f"Running {n_episodes} evaluation episodes...")

    for ep in range(n_episodes):
        env.reset()
        episode_reward = 0
        episode_length = 0
        success = False
        collision = False

        for step in range(1000):
            sensor_data = env.get_sensor_data()
            control, _ = agent.select_action(sensor_data, deterministic=True)
            next_sensor_data, info, done = env.step(control)

            episode_reward += info.get('reward', 0)
            episode_length += 1

            if info.get('destination_reached', False):
                success = True
            if info.get('collision_vehicle', False) or info.get('collision_pedestrian', False):
                collision = True

            if done:
                break

        results['rewards'].append(episode_reward)
        results['lengths'].append(episode_length)
        results['successes'].append(success)
        results['collisions'].append(collision)

        print(f"  Episode {ep+1}: Reward={episode_reward:.2f}, "
              f"Length={episode_length}, Success={success}, Collision={collision}")

    # Print summary
    import numpy as np
    print("\nEvaluation Summary:")
    print(f"  Mean Reward: {np.mean(results['rewards']):.2f} ± {np.std(results['rewards']):.2f}")
    print(f"  Mean Length: {np.mean(results['lengths']):.1f} steps")
    print(f"  Success Rate: {np.mean(results['successes'])*100:.1f}%")
    print(f"  Collision Rate: {np.mean(results['collisions'])*100:.1f}%")


def example_5_with_safety_wrapper():
    """
    Example 5: Use agent with safety wrapper.
    """
    print("=" * 60)
    print("Example 5: Safety Wrapper")
    print("=" * 60)

    from rl_agent import create_default_agent, SafetyWrapper
    from rl_agent.training import MockEnvironment

    # Create agent
    agent = create_default_agent()

    # Wrap with safety layer
    safety_config = {
        'min_safe_distance': 3.0,  # meters
        'emergency_brake_threshold': 2.0,  # meters
    }
    safe_agent = SafetyWrapper(agent, safety_config)
    print("Agent wrapped with safety layer")
    print(f"  Min safe distance: {safety_config['min_safe_distance']}m")
    print(f"  Emergency brake threshold: {safety_config['emergency_brake_threshold']}m")

    # Use safe agent
    env = MockEnvironment()
    env.reset()

    print("\nRunning with safety wrapper...")
    interventions = 0

    for step in range(50):
        sensor_data = env.get_sensor_data()
        control, debug_info = safe_agent.select_action(sensor_data)

        if 'safety_intervention' in debug_info:
            interventions += 1
            print(f"  Step {step}: Safety intervention - {debug_info['safety_intervention']}")

        next_sensor_data, info, done = env.step(control)

        if done:
            break

    print(f"\nTotal safety interventions: {interventions}")


def example_6_integration_with_real_system():
    """
    Example 6: Integration with the full autonomous taxi system.

    This shows how the RL agent integrates with:
    - Agent 1 (Map Parser): Provides road network
    - Agent 2 (Traffic Simulation): Provides environment dynamics
    - Agent 4 (Sensors): Provides sensor data and control interface
    - Agent 3 (Frontend): Displays visualization
    """
    print("=" * 60)
    print("Example 6: Full System Integration")
    print("=" * 60)

    # NOTE: This is pseudocode showing the integration pattern.
    # Actual implementation depends on how other agents are structured.

    """
    # Import components from other agents
    from map_parsing import MapParser
    from traffic_simulation import TrafficManager
    from sensors import SensorFusion, CarControl

    # Initialize system components
    map_parser = MapParser('path/to/map.osm')
    traffic_manager = TrafficManager(map_parser)
    sensor_fusion = SensorFusion(traffic_manager)
    car_control = CarControl(traffic_manager)

    # Create RL agent
    from rl_agent import create_default_agent, SafetyWrapper
    agent = create_default_agent(device='cuda')
    agent.load('checkpoints/rl_agent/best_model.pt')
    safe_agent = SafetyWrapper(agent)

    # Main control loop
    while True:
        # Get sensor data from Agent 4
        sensor_data = sensor_fusion.get_sensor_data()

        # RL agent selects action
        control_commands, debug_info = safe_agent.select_action(
            sensor_data,
            deterministic=True
        )

        # Send control commands to car
        car_control.execute(control_commands)

        # Update traffic simulation
        traffic_manager.update(dt=0.1)

        # Send data to frontend for visualization
        visualization_data = {
            'car_position': sensor_data['gps']['position'],
            'car_speed': sensor_data['telemetry']['speed'],
            'action': control_commands,
            'value': debug_info['value'],
        }
        # frontend.update(visualization_data)

        # Check termination
        if sensor_data['gps'].get('destination_reached', False):
            print("Destination reached!")
            break
    """

    print("See code comments for integration pattern")
    print("This requires implementing the full system with all agents")


def main():
    """
    Main demonstration menu.
    """
    print("\n" + "=" * 60)
    print("RL AGENT USAGE EXAMPLES")
    print("=" * 60)
    print("\nAvailable examples:")
    print("  1. Training from scratch")
    print("  2. Custom configuration")
    print("  3. Load and use trained model")
    print("  4. Evaluation")
    print("  5. Safety wrapper")
    print("  6. Full system integration (pseudocode)")
    print("\nTo run an example:")
    print("  from rl_agent.example_usage import example_1_training_from_scratch")
    print("  example_1_training_from_scratch()")


if __name__ == '__main__':
    main()
