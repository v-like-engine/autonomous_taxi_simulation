"""
Test script for RL Agent components.

This script tests all major components of the RL agent:
- Model architecture
- Reward function
- Rollout buffer
- PPO agent
- Training loop
"""

import torch
import numpy as np
from typing import Dict, Any

# Test imports
try:
    from .model import ActorCritic, preprocess_sensor_data, postprocess_action
    from .reward import RewardFunction, create_default_reward_function
    from .replay_buffer import RolloutBuffer, EpisodeBuffer, MetricsTracker
    from .agent import PPOAgent, create_default_agent
    from .training import MockEnvironment, Trainer
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    exit(1)


def create_mock_sensor_data() -> Dict[str, Any]:
    """Create mock sensor data for testing."""
    lidar_points = []
    for i in range(360):
        lidar_points.append({
            'angle': i,
            'distance': 30.0 + np.random.randn() * 5,
            'intensity': 0.8
        })

    return {
        'lidar': {'points': lidar_points},
        'sonar': {
            'front_left': 5.0,
            'front_center': 6.0,
            'front_right': 5.5,
            'rear_left': 4.0,
            'rear_center': 4.5,
            'rear_right': 4.2,
            'side_left': 3.0,
            'side_right': 3.2,
        },
        'gps': {
            'position': [10.0, 20.0],
            'heading': 45.0,
            'route': [[100.0, 200.0]],
            'speed_limit': 60,
            'current_zone': 'urban',
        },
        'telemetry': {
            'speed': 30.0,
            'acceleration': 1.0,
            'steering_angle': 5.0,
            'gear': 1,
        },
        'camera': {
            'vehicles': [
                {'type': 'car', 'position': [15.0, 25.0], 'confidence': 0.9}
            ],
            'pedestrians': [
                {'position': [12.0, 22.0], 'confidence': 0.8}
            ],
        }
    }


def test_model():
    """Test model components."""
    print("\n" + "="*60)
    print("Testing Model Components")
    print("="*60)

    try:
        # Create model
        config = {'hidden_dim': 128, 'action_dim': 3}
        model = ActorCritic(config)
        print(f"✓ Model created successfully")
        print(f"  Feature dim: {model.encoder.feature_dim}")
        print(f"  Hidden dim: 128")
        print(f"  Action dim: 3")

        # Test preprocessing
        sensor_data = create_mock_sensor_data()
        processed = preprocess_sensor_data(sensor_data)
        print(f"✓ Sensor data preprocessed")
        print(f"  Lidar shape: {processed['lidar'].shape}")
        print(f"  Sonar shape: {processed['sonar'].shape}")
        print(f"  GPS shape: {processed['gps'].shape}")
        print(f"  Telemetry shape: {processed['telemetry'].shape}")
        print(f"  Camera shape: {processed['camera'].shape}")

        # Test forward pass
        for key in processed:
            processed[key] = processed[key].unsqueeze(0)

        action, log_prob, entropy, value = model.get_action(processed)
        print(f"✓ Forward pass successful")
        print(f"  Action shape: {action.shape}")
        print(f"  Action values: {action.squeeze().detach().numpy()}")
        print(f"  Log prob: {log_prob.item():.4f}")
        print(f"  Entropy: {entropy.item():.4f}")
        print(f"  Value: {value.item():.4f}")

        # Test action postprocessing
        control = postprocess_action(action.squeeze())
        print(f"✓ Action postprocessed")
        print(f"  Throttle: {control['throttle']:.3f}")
        print(f"  Brake: {control['brake']:.3f}")
        print(f"  Steering: {control['steering']:.3f}")
        print(f"  Gear: {control['gear']}")

        return True

    except Exception as e:
        print(f"✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reward_function():
    """Test reward function."""
    print("\n" + "="*60)
    print("Testing Reward Function")
    print("="*60)

    try:
        reward_fn = create_default_reward_function()
        print("✓ Reward function created")

        # Create mock states
        state = create_mock_sensor_data()
        next_state = create_mock_sensor_data()
        next_state['gps']['position'] = [11.0, 21.0]  # Moved forward

        action = np.array([0.5, 0.0, 0.1])  # throttle, brake, steering

        # Test normal driving
        info = {
            'collision_vehicle': False,
            'collision_pedestrian': False,
            'off_road': False,
            'distance_from_lane_center': 0.5,
        }

        reward, done, components = reward_fn.calculate_reward(state, action, next_state, info)
        print(f"✓ Normal driving reward calculated")
        print(f"  Total reward: {reward:.3f}")
        print(f"  Done: {done}")
        print(f"  Components: {list(components.keys())}")

        # Test collision
        info['collision_vehicle'] = True
        reward, done, components = reward_fn.calculate_reward(state, action, next_state, info)
        print(f"✓ Collision reward calculated")
        print(f"  Total reward: {reward:.3f} (should be very negative)")
        print(f"  Done: {done} (should be True)")

        # Test destination reached
        info = {'destination_reached': True}
        reward, done, components = reward_fn.calculate_reward(state, action, next_state, info)
        print(f"✓ Destination reached reward calculated")
        print(f"  Total reward: {reward:.3f} (should be very positive)")
        print(f"  Done: {done} (should be True)")

        return True

    except Exception as e:
        print(f"✗ Reward function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_buffer():
    """Test rollout buffer."""
    print("\n" + "="*60)
    print("Testing Rollout Buffer")
    print("="*60)

    try:
        buffer = RolloutBuffer(buffer_size=100, gamma=0.99, gae_lambda=0.95)
        print("✓ Rollout buffer created")

        # Add some transitions
        sensor_data = create_mock_sensor_data()
        processed = preprocess_sensor_data(sensor_data)

        for i in range(10):
            buffer.add(
                state=processed,
                action=torch.randn(3),
                reward=1.0 + np.random.randn() * 0.1,
                value=5.0 + np.random.randn(),
                log_prob=-1.5 + np.random.randn() * 0.1,
                done=False
            )

        print(f"✓ Added 10 transitions")
        print(f"  Buffer size: {len(buffer)}")

        # Compute advantages
        buffer.compute_returns_and_advantages(last_value=5.0)
        print(f"✓ Computed returns and advantages")

        # Get batches
        batches = buffer.get(batch_size=5)
        print(f"✓ Retrieved batches")
        print(f"  Number of batches: {len(batches)}")
        print(f"  Batch 0 shapes:")
        states, actions, log_probs, returns, advantages = batches[0]
        print(f"    Actions: {actions.shape}")
        print(f"    Log probs: {log_probs.shape}")
        print(f"    Returns: {returns.shape}")
        print(f"    Advantages: {advantages.shape}")

        return True

    except Exception as e:
        print(f"✗ Buffer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_agent():
    """Test PPO agent."""
    print("\n" + "="*60)
    print("Testing PPO Agent")
    print("="*60)

    try:
        agent = create_default_agent(device='cpu')
        print("✓ Agent created")
        print(f"  Device: {agent.device}")
        print(f"  Learning rate: {agent.lr}")
        print(f"  Gamma: {agent.gamma}")

        # Test action selection
        sensor_data = create_mock_sensor_data()
        control, debug_info = agent.select_action(sensor_data, deterministic=False)
        print(f"✓ Action selected")
        print(f"  Throttle: {control['throttle']:.3f}")
        print(f"  Brake: {control['brake']:.3f}")
        print(f"  Steering: {control['steering']:.3f}")
        print(f"  Value estimate: {debug_info['value']:.3f}")

        # Test step processing
        next_sensor_data = create_mock_sensor_data()
        info = {'collision_vehicle': False, 'distance_from_lane_center': 0.5}
        reward, done, components = agent.step(sensor_data, next_sensor_data, control, info)
        print(f"✓ Step processed")
        print(f"  Reward: {reward:.3f}")
        print(f"  Done: {done}")

        return True

    except Exception as e:
        print(f"✗ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_environment():
    """Test mock environment."""
    print("\n" + "="*60)
    print("Testing Mock Environment")
    print("="*60)

    try:
        env = MockEnvironment()
        print("✓ Environment created")

        env.reset()
        print("✓ Environment reset")

        sensor_data = env.get_sensor_data()
        print("✓ Sensor data retrieved")
        print(f"  Position: {sensor_data['gps']['position']}")
        print(f"  Speed: {sensor_data['telemetry']['speed']}")

        control = {'throttle': 0.5, 'brake': 0.0, 'steering': 0.1, 'gear': 1}
        next_sensor, info, done = env.step(control)
        print("✓ Step executed")
        print(f"  New position: {next_sensor['gps']['position']}")
        print(f"  New speed: {next_sensor['telemetry']['speed']:.2f}")
        print(f"  Done: {done}")

        return True

    except Exception as e:
        print(f"✗ Environment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration():
    """Test full integration with short training run."""
    print("\n" + "="*60)
    print("Testing Integration (Short Training)")
    print("="*60)

    try:
        # Create agent and environment
        agent = create_default_agent(device='cpu')
        env = MockEnvironment()
        print("✓ Agent and environment created")

        # Run a few steps
        env.reset()
        total_reward = 0

        for step in range(10):
            sensor_data = env.get_sensor_data()
            control, debug = agent.select_action(sensor_data)
            next_sensor, info, done = env.step(control)

            reward, done_agent, components = agent.step(sensor_data, next_sensor, control, info)
            total_reward += reward

            if done or done_agent:
                break

        print(f"✓ Ran 10 steps successfully")
        print(f"  Total reward: {total_reward:.3f}")
        print(f"  Buffer size: {len(agent.buffer)}")

        return True

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("RL AGENT TEST SUITE")
    print("="*60)

    tests = [
        ("Model", test_model),
        ("Reward Function", test_reward_function),
        ("Rollout Buffer", test_buffer),
        ("PPO Agent", test_agent),
        ("Mock Environment", test_environment),
        ("Integration", test_integration),
    ]

    results = []
    for name, test_fn in tests:
        result = test_fn()
        results.append((name, result))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")

    print("="*60)
    print(f"Total: {passed}/{total} tests passed")
    print("="*60)

    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
