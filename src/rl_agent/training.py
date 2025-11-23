"""
Training Loop for PPO Agent

This module provides the training infrastructure for the self-driving car RL agent.
Includes training loop, evaluation, logging, and checkpointing.
"""

import os
import time
import json
import numpy as np
from typing import Dict, Any, Optional, Callable
import matplotlib.pyplot as plt

from .agent import PPOAgent, SafetyWrapper, create_default_agent


class Trainer:
    """
    Training manager for PPO agent.

    Handles:
    - Training loop
    - Evaluation
    - Checkpointing
    - Logging and visualization
    """

    def __init__(
        self,
        agent: PPOAgent,
        env: Any,  # Environment interface (from traffic simulation + sensors)
        config: Dict[str, Any] = None
    ):
        """
        Initialize trainer.

        Args:
            agent: PPO agent to train
            env: Environment (provides reset(), step(), get_sensor_data())
            config: Training configuration
        """
        self.agent = agent
        self.env = env
        self.config = config or {}

        # Training parameters
        self.max_episodes = self.config.get('max_episodes', 1000)
        self.max_steps_per_episode = self.config.get('max_steps_per_episode', 2000)
        self.eval_frequency = self.config.get('eval_frequency', 50)
        self.eval_episodes = self.config.get('eval_episodes', 10)
        self.save_frequency = self.config.get('save_frequency', 100)
        self.log_frequency = self.config.get('log_frequency', 10)

        # Paths
        self.checkpoint_dir = self.config.get('checkpoint_dir', 'checkpoints/rl_agent')
        self.log_dir = self.config.get('log_dir', 'logs/rl_agent')
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)

        # Logging
        self.training_log = []
        self.best_reward = -float('inf')

    def train(self):
        """
        Main training loop.
        """
        print("=" * 60)
        print("Starting PPO Training for Autonomous Taxi")
        print("=" * 60)
        print(f"Max Episodes: {self.max_episodes}")
        print(f"Max Steps per Episode: {self.max_steps_per_episode}")
        print(f"Device: {self.agent.device}")
        print("=" * 60)

        start_time = time.time()

        for episode in range(self.max_episodes):
            episode_start = time.time()

            # Run episode
            episode_reward, episode_length, episode_info = self._run_episode(training=True)

            episode_time = time.time() - episode_start

            # Log episode
            if episode % self.log_frequency == 0:
                self._log_episode(episode, episode_reward, episode_length, episode_time, episode_info)

            # Evaluate
            if episode % self.eval_frequency == 0 and episode > 0:
                eval_reward = self._evaluate()
                print(f"\nEvaluation at episode {episode}: Mean Reward = {eval_reward:.2f}")

                # Save best model
                if eval_reward > self.best_reward:
                    self.best_reward = eval_reward
                    self._save_checkpoint(f"{self.checkpoint_dir}/best_model.pt")
                    print(f"New best model saved! Reward: {eval_reward:.2f}")

            # Save checkpoint
            if episode % self.save_frequency == 0 and episode > 0:
                self._save_checkpoint(f"{self.checkpoint_dir}/checkpoint_ep{episode}.pt")

        # Training complete
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"Training Complete! Total time: {total_time/3600:.2f} hours")
        print("=" * 60)

        # Save final model
        self._save_checkpoint(f"{self.checkpoint_dir}/final_model.pt")

        # Plot training curves
        self._plot_training_curves()

    def _run_episode(self, training: bool = True) -> tuple:
        """
        Run one episode.

        Args:
            training: If True, update the agent

        Returns:
            Tuple of (total_reward, episode_length, info_dict)
        """
        # Reset environment
        self.env.reset()
        sensor_data = self.env.get_sensor_data()

        episode_reward = 0.0
        episode_length = 0
        info_summary = {
            'collisions': 0,
            'speeding_violations': 0,
            'off_road': 0,
            'destination_reached': False,
        }

        for step in range(self.max_steps_per_episode):
            # Select action
            control, debug_info = self.agent.select_action(
                sensor_data,
                deterministic=not training
            )

            # Step environment
            next_sensor_data, env_info, done = self.env.step(control)

            # Process step (only during training)
            if training:
                reward, done_from_reward, reward_components = self.agent.step(
                    sensor_data,
                    next_sensor_data,
                    control,
                    env_info
                )
                episode_reward += reward

                # Update done flag
                done = done or done_from_reward
            else:
                # During evaluation, just accumulate simple reward
                episode_reward += env_info.get('reward', 0.0)

            # Update info
            if env_info.get('collision_vehicle', False) or env_info.get('collision_pedestrian', False):
                info_summary['collisions'] += 1

            if env_info.get('speeding', False):
                info_summary['speeding_violations'] += 1

            if env_info.get('off_road', False):
                info_summary['off_road'] += 1

            if env_info.get('destination_reached', False):
                info_summary['destination_reached'] = True

            episode_length += 1
            sensor_data = next_sensor_data

            if done:
                break

        return episode_reward, episode_length, info_summary

    def _evaluate(self) -> float:
        """
        Evaluate current policy.

        Returns:
            Mean evaluation reward
        """
        eval_rewards = []

        for _ in range(self.eval_episodes):
            episode_reward, _, _ = self._run_episode(training=False)
            eval_rewards.append(episode_reward)

        return np.mean(eval_rewards)

    def _log_episode(self, episode: int, reward: float, length: int, time: float, info: Dict[str, Any]):
        """
        Log episode information.

        Args:
            episode: Episode number
            reward: Total reward
            length: Episode length
            time: Episode duration
            info: Episode info
        """
        # Get agent stats
        stats = self.agent.get_stats()

        log_entry = {
            'episode': episode,
            'reward': reward,
            'length': length,
            'time': time,
            'info': info,
            'stats': stats,
        }

        self.training_log.append(log_entry)

        # Print summary
        print(f"\nEpisode {episode}:")
        print(f"  Reward: {reward:.2f}")
        print(f"  Length: {length} steps")
        print(f"  Time: {time:.2f}s")
        print(f"  Success Rate: {stats.get('success_rate', 0):.2%}")
        print(f"  Collision Rate: {stats.get('collision_rate', 0):.2%}")
        if 'actor_loss' in stats:
            print(f"  Actor Loss: {stats['actor_loss']:.4f}")
            print(f"  Critic Loss: {stats['critic_loss']:.4f}")
            print(f"  Entropy: {stats['entropy']:.4f}")

    def _save_checkpoint(self, path: str):
        """
        Save checkpoint.

        Args:
            path: Path to save checkpoint
        """
        self.agent.save(path)

        # Save training log
        log_path = path.replace('.pt', '_log.json')
        with open(log_path, 'w') as f:
            json.dump(self.training_log, f, indent=2)

    def _plot_training_curves(self):
        """
        Plot training curves.
        """
        if len(self.training_log) == 0:
            return

        # Extract data
        episodes = [log['episode'] for log in self.training_log]
        rewards = [log['reward'] for log in self.training_log]
        success_rates = [log['stats'].get('success_rate', 0) for log in self.training_log]
        collision_rates = [log['stats'].get('collision_rate', 0) for log in self.training_log]

        # Create figure
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))

        # Reward curve
        axes[0, 0].plot(episodes, rewards)
        axes[0, 0].set_xlabel('Episode')
        axes[0, 0].set_ylabel('Total Reward')
        axes[0, 0].set_title('Training Reward')
        axes[0, 0].grid(True)

        # Success rate
        axes[0, 1].plot(episodes, success_rates)
        axes[0, 1].set_xlabel('Episode')
        axes[0, 1].set_ylabel('Success Rate')
        axes[0, 1].set_title('Success Rate (Destination Reached)')
        axes[0, 1].grid(True)

        # Collision rate
        axes[1, 0].plot(episodes, collision_rates)
        axes[1, 0].set_xlabel('Episode')
        axes[1, 0].set_ylabel('Collision Rate')
        axes[1, 0].set_title('Collision Rate')
        axes[1, 0].grid(True)

        # Loss curves (if available)
        actor_losses = [log['stats'].get('actor_loss', None) for log in self.training_log]
        if any(l is not None for l in actor_losses):
            actor_losses = [l for l in actor_losses if l is not None]
            critic_losses = [log['stats'].get('critic_loss', 0) for log in self.training_log if 'actor_loss' in log['stats']]
            ep_with_loss = [log['episode'] for log in self.training_log if 'actor_loss' in log['stats']]

            axes[1, 1].plot(ep_with_loss, actor_losses, label='Actor Loss')
            axes[1, 1].plot(ep_with_loss, critic_losses, label='Critic Loss')
            axes[1, 1].set_xlabel('Episode')
            axes[1, 1].set_ylabel('Loss')
            axes[1, 1].set_title('Training Losses')
            axes[1, 1].legend()
            axes[1, 1].grid(True)

        plt.tight_layout()
        plt.savefig(f"{self.log_dir}/training_curves.png", dpi=150)
        print(f"\nTraining curves saved to {self.log_dir}/training_curves.png")


class MockEnvironment:
    """
    Mock environment for testing the training loop.

    This simulates the interface that the real environment should provide.
    Replace this with the actual environment from traffic simulation + sensors.
    """

    def __init__(self):
        self.position = np.array([0.0, 0.0])
        self.heading = 0.0
        self.speed = 0.0
        self.destination = np.array([100.0, 100.0])
        self.step_count = 0

    def reset(self):
        """Reset environment to initial state."""
        self.position = np.array([0.0, 0.0]) + np.random.randn(2) * 10
        self.heading = np.random.rand() * 360
        self.speed = 0.0
        self.destination = np.array([100.0, 100.0]) + np.random.randn(2) * 20
        self.step_count = 0

    def get_sensor_data(self) -> Dict[str, Any]:
        """
        Get current sensor data.

        Returns:
            Dictionary of sensor data
        """
        # Mock lidar (360 points)
        lidar_points = []
        for i in range(360):
            distance = 50.0 + np.random.randn() * 5
            lidar_points.append({
                'angle': i,
                'distance': max(distance, 0),
                'intensity': 0.8
            })

        # Mock sonar
        sonar = {
            'front_left': 5.0 + np.random.randn(),
            'front_center': 5.0 + np.random.randn(),
            'front_right': 5.0 + np.random.randn(),
            'rear_left': 5.0,
            'rear_center': 5.0,
            'rear_right': 5.0,
            'side_left': 3.0,
            'side_right': 3.0,
        }

        # Mock GPS
        gps = {
            'position': self.position.tolist(),
            'heading': self.heading,
            'route': [self.destination.tolist()],
            'speed_limit': 60,
            'current_zone': 'urban',
        }

        # Mock telemetry
        telemetry = {
            'speed': self.speed,
            'acceleration': 0.0,
            'steering_angle': 0.0,
            'gear': 1,
        }

        # Mock camera
        camera = {
            'vehicles': [],
            'pedestrians': [],
        }

        return {
            'lidar': {'points': lidar_points},
            'sonar': sonar,
            'gps': gps,
            'telemetry': telemetry,
            'camera': camera,
        }

    def step(self, control: Dict[str, float]) -> tuple:
        """
        Execute action in environment.

        Args:
            control: Control commands

        Returns:
            Tuple of (next_sensor_data, info, done)
        """
        # Simple physics
        throttle = control.get('throttle', 0)
        brake = control.get('brake', 0)
        steering = control.get('steering', 0)

        # Update speed
        acceleration = throttle * 5.0 - brake * 10.0
        self.speed += acceleration * 0.1
        self.speed = np.clip(self.speed, 0, 100)

        # Update heading
        self.heading += steering * 5.0

        # Update position
        rad_heading = np.radians(self.heading)
        self.position += np.array([
            np.cos(rad_heading),
            np.sin(rad_heading)
        ]) * self.speed * 0.1

        self.step_count += 1

        # Check conditions
        distance_to_dest = np.linalg.norm(self.position - self.destination)
        done = distance_to_dest < 5.0 or self.step_count > 1000

        info = {
            'collision_vehicle': False,
            'collision_pedestrian': False,
            'off_road': False,
            'speeding': self.speed > 60,
            'destination_reached': distance_to_dest < 5.0,
            'distance_from_lane_center': 0.5,
            'reward': -0.01,  # Simple time penalty
        }

        if info['destination_reached']:
            info['reward'] = 100.0

        return self.get_sensor_data(), info, done


def train_agent(
    agent: Optional[PPOAgent] = None,
    env: Optional[Any] = None,
    config: Optional[Dict[str, Any]] = None
):
    """
    Train the RL agent.

    Args:
        agent: PPO agent (creates default if None)
        env: Environment (creates mock if None)
        config: Training configuration
    """
    # Create default agent if not provided
    if agent is None:
        print("Creating default PPO agent...")
        agent = create_default_agent()

    # Create mock environment if not provided
    if env is None:
        print("Using mock environment (replace with real environment)...")
        env = MockEnvironment()

    # Create trainer
    trainer = Trainer(agent, env, config)

    # Run training
    trainer.train()


if __name__ == '__main__':
    """
    Example training script.

    To use with real environment:
    1. Import the environment from traffic_simulation + sensors
    2. Create environment instance
    3. Call train_agent(env=real_env)
    """
    print("PPO Agent Training")
    print("This is a standalone training module.")
    print("\nTo train:")
    print("  from rl_agent.training import train_agent")
    print("  train_agent()")
    print("\nOr with custom config:")
    print("  config = {'max_episodes': 2000, 'learning_rate': 1e-4}")
    print("  train_agent(config=config)")

    # Example: Train with mock environment
    # train_agent()
