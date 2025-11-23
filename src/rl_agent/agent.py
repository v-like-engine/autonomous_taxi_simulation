"""
PPO (Proximal Policy Optimization) Agent for Self-Driving Car

This module implements the main PPO agent that learns to drive safely and legally.
PPO is an on-policy algorithm that uses clipped surrogate objective for stable learning.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, Any, Tuple, Optional
import os
import json

from .model import ActorCritic, preprocess_sensor_data, postprocess_action
from .replay_buffer import RolloutBuffer, EpisodeBuffer, MetricsTracker
from .reward import RewardFunction, create_default_reward_function


class PPOAgent:
    """
    Proximal Policy Optimization agent for autonomous driving.

    Implements PPO algorithm with:
    - Clipped surrogate objective
    - Generalized Advantage Estimation (GAE)
    - Value function clipping
    - Entropy bonus for exploration
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize PPO agent.

        Args:
            config: Configuration dictionary with hyperparameters
        """
        self.config = config or {}

        # Device
        self.device = torch.device(
            self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        )

        # Hyperparameters
        self.lr = self.config.get('learning_rate', 3e-4)
        self.gamma = self.config.get('gamma', 0.99)
        self.gae_lambda = self.config.get('gae_lambda', 0.95)
        self.clip_epsilon = self.config.get('clip_epsilon', 0.2)
        self.value_loss_coef = self.config.get('value_loss_coef', 0.5)
        self.entropy_coef = self.config.get('entropy_coef', 0.01)
        self.max_grad_norm = self.config.get('max_grad_norm', 0.5)
        self.n_epochs = self.config.get('n_epochs', 10)
        self.batch_size = self.config.get('batch_size', 64)
        self.buffer_size = self.config.get('buffer_size', 2048)

        # Model
        self.policy = ActorCritic(self.config).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=self.lr)

        # Rollout buffer
        self.buffer = RolloutBuffer(
            buffer_size=self.buffer_size,
            gamma=self.gamma,
            gae_lambda=self.gae_lambda,
            device=self.device
        )

        # Reward function
        self.reward_fn = create_default_reward_function()

        # Episode tracking
        self.current_episode = EpisodeBuffer()
        self.metrics = MetricsTracker(window_size=100)

        # Training state
        self.total_timesteps = 0
        self.num_updates = 0

    def select_action(
        self,
        sensor_data: Dict[str, Any],
        deterministic: bool = False
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        Select action given sensor data.

        Args:
            sensor_data: Raw sensor data from environment
            deterministic: If True, use mean action (no exploration)

        Returns:
            Tuple of (control_commands, debug_info)
        """
        # Preprocess sensor data
        processed_data = preprocess_sensor_data(sensor_data)

        # Add batch dimension
        for key in processed_data:
            processed_data[key] = processed_data[key].unsqueeze(0).to(self.device)

        # Get action from policy
        with torch.no_grad():
            action, log_prob, entropy, value = self.policy.get_action(
                processed_data,
                deterministic=deterministic
            )

        # Store for training (if not deterministic)
        if not deterministic:
            self.last_state = processed_data
            self.last_action = action.squeeze(0)
            self.last_log_prob = log_prob.item()
            self.last_value = value.item()

        # Convert to control commands
        control = postprocess_action(action.squeeze(0))

        debug_info = {
            'value': value.item(),
            'log_prob': log_prob.item(),
            'entropy': entropy.item(),
        }

        return control, debug_info

    def step(
        self,
        sensor_data: Dict[str, Any],
        next_sensor_data: Dict[str, Any],
        action: Dict[str, float],
        info: Dict[str, Any]
    ):
        """
        Process one environment step.

        Args:
            sensor_data: Sensor data before action
            next_sensor_data: Sensor data after action
            action: Action taken
            info: Environment info (collisions, violations, etc.)
        """
        # Calculate reward
        reward, done, reward_components = self.reward_fn.calculate_reward(
            sensor_data,
            np.array([action['throttle'], action['brake'], action['steering']]),
            next_sensor_data,
            info
        )

        # Store in buffer
        self.buffer.add(
            state=self.last_state,
            action=self.last_action,
            reward=reward,
            value=self.last_value,
            log_prob=self.last_log_prob,
            done=done
        )

        # Store in episode buffer
        self.current_episode.add(
            state=sensor_data,
            action=np.array([action['throttle'], action['brake'], action['steering']]),
            reward=reward,
            info=info
        )

        self.total_timesteps += 1

        # Check if episode ended
        if done:
            self._on_episode_end()

        # Check if buffer is full (time to update)
        if self.buffer.is_full():
            self.update()

        return reward, done, reward_components

    def _on_episode_end(self):
        """Handle end of episode."""
        episode_summary = self.current_episode.get_summary()
        self.metrics.add_episode(episode_summary)

        # Log episode summary
        print(f"Episode ended: Reward={episode_summary['total_reward']:.2f}, "
              f"Length={episode_summary['length']}, "
              f"Success={episode_summary['destination_reached']}, "
              f"Collision={episode_summary['collision']}")

        # Reset episode buffer
        self.current_episode.clear()
        self.reward_fn.reset()

    def update(self) -> Dict[str, float]:
        """
        Update policy using PPO algorithm.

        Returns:
            Dictionary of training metrics
        """
        # Compute returns and advantages
        # Get last value for bootstrapping
        if len(self.buffer.states) > 0:
            with torch.no_grad():
                last_state = {k: v[-1:] for k, v in self.buffer.states[-1].items()}
                for k in last_state:
                    last_state[k] = last_state[k].to(self.device)
                last_value = self.policy.get_value(last_state).item()
        else:
            last_value = 0.0

        self.buffer.compute_returns_and_advantages(last_value)

        # Training metrics
        total_actor_loss = 0.0
        total_critic_loss = 0.0
        total_entropy = 0.0
        n_batches = 0

        # Multiple epochs of updates
        for epoch in range(self.n_epochs):
            # Get batches
            batches = self.buffer.get(batch_size=self.batch_size)

            for batch in batches:
                states, actions, old_log_probs, returns, advantages = batch

                # Evaluate actions with current policy
                log_probs, entropy, values = self.policy.evaluate_actions(states, actions)

                # Policy loss (clipped surrogate objective)
                ratio = torch.exp(log_probs - old_log_probs)
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1.0 - self.clip_epsilon, 1.0 + self.clip_epsilon) * advantages
                actor_loss = -torch.min(surr1, surr2).mean()

                # Value loss (clipped)
                values_clipped = old_log_probs + torch.clamp(
                    values - old_log_probs,
                    -self.clip_epsilon,
                    self.clip_epsilon
                )
                value_loss1 = (values - returns) ** 2
                value_loss2 = (values_clipped - returns) ** 2
                critic_loss = 0.5 * torch.max(value_loss1, value_loss2).mean()

                # Entropy bonus (for exploration)
                entropy_loss = -entropy.mean()

                # Total loss
                loss = (
                    actor_loss +
                    self.value_loss_coef * critic_loss +
                    self.entropy_coef * entropy_loss
                )

                # Optimize
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.policy.parameters(), self.max_grad_norm)
                self.optimizer.step()

                # Track metrics
                total_actor_loss += actor_loss.item()
                total_critic_loss += critic_loss.item()
                total_entropy += entropy.mean().item()
                n_batches += 1

        # Average metrics
        avg_actor_loss = total_actor_loss / max(n_batches, 1)
        avg_critic_loss = total_critic_loss / max(n_batches, 1)
        avg_entropy = total_entropy / max(n_batches, 1)

        # Update metrics tracker
        self.metrics.add_training_step(avg_actor_loss, avg_critic_loss, avg_entropy)

        # Clear buffer
        self.buffer.clear()

        self.num_updates += 1

        metrics = {
            'actor_loss': avg_actor_loss,
            'critic_loss': avg_critic_loss,
            'entropy': avg_entropy,
        }

        return metrics

    def save(self, path: str):
        """
        Save model checkpoint.

        Args:
            path: Path to save checkpoint
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)

        checkpoint = {
            'policy_state_dict': self.policy.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config,
            'total_timesteps': self.total_timesteps,
            'num_updates': self.num_updates,
            'metrics': self.metrics.get_all_data(),
        }

        torch.save(checkpoint, path)
        print(f"Checkpoint saved to {path}")

    def load(self, path: str):
        """
        Load model checkpoint.

        Args:
            path: Path to checkpoint
        """
        checkpoint = torch.load(path, map_location=self.device)

        self.policy.load_state_dict(checkpoint['policy_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.total_timesteps = checkpoint.get('total_timesteps', 0)
        self.num_updates = checkpoint.get('num_updates', 0)

        print(f"Checkpoint loaded from {path}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current training statistics.

        Returns:
            Dictionary of statistics
        """
        stats = self.metrics.get_recent_stats()
        stats.update({
            'total_timesteps': self.total_timesteps,
            'num_updates': self.num_updates,
        })

        return stats


class SafetyWrapper:
    """
    Wraps the RL agent with safety constraints.

    Provides emergency interventions to prevent dangerous actions.
    """

    def __init__(self, agent: PPOAgent, config: Dict[str, Any] = None):
        """
        Initialize safety wrapper.

        Args:
            agent: PPO agent to wrap
            config: Safety configuration
        """
        self.agent = agent
        self.config = config or {}

        # Safety parameters
        self.min_safe_distance = self.config.get('min_safe_distance', 3.0)  # meters
        self.emergency_brake_threshold = self.config.get('emergency_brake_threshold', 2.0)

    def select_action(
        self,
        sensor_data: Dict[str, Any],
        deterministic: bool = False
    ) -> Tuple[Dict[str, float], Dict[str, Any]]:
        """
        Select action with safety checks.

        Args:
            sensor_data: Sensor data
            deterministic: Use deterministic policy

        Returns:
            Tuple of (control_commands, debug_info)
        """
        # Get action from agent
        control, debug_info = self.agent.select_action(sensor_data, deterministic)

        # Safety checks
        sonar = sensor_data.get('sonar', {})
        telemetry = sensor_data.get('telemetry', {})
        speed = telemetry.get('speed', 0)

        # Emergency braking if obstacle too close
        front_distance = min(
            sonar.get('front_left', 10.0),
            sonar.get('front_center', 10.0),
            sonar.get('front_right', 10.0)
        )

        if front_distance < self.emergency_brake_threshold and speed > 5:
            # Emergency brake!
            control['throttle'] = 0.0
            control['brake'] = 1.0
            debug_info['safety_intervention'] = 'emergency_brake'

        # Limit speed in tight situations
        elif front_distance < self.min_safe_distance and speed > 20:
            control['throttle'] *= 0.5
            control['brake'] = max(control['brake'], 0.3)
            debug_info['safety_intervention'] = 'speed_limit'

        return control, debug_info


def create_default_agent(device: str = 'cpu') -> PPOAgent:
    """
    Create a PPO agent with default configuration.

    Args:
        device: Device to use ('cpu' or 'cuda')

    Returns:
        Configured PPO agent
    """
    config = {
        'device': device,
        'learning_rate': 3e-4,
        'gamma': 0.99,
        'gae_lambda': 0.95,
        'clip_epsilon': 0.2,
        'value_loss_coef': 0.5,
        'entropy_coef': 0.01,
        'max_grad_norm': 0.5,
        'n_epochs': 10,
        'batch_size': 64,
        'buffer_size': 2048,
        'hidden_dim': 256,
        'action_dim': 3,
    }

    return PPOAgent(config)
