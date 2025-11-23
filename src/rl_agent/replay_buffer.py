"""
Rollout Buffer for PPO Agent

PPO uses on-policy learning, so it collects full trajectories (rollouts) and computes
advantages using Generalized Advantage Estimation (GAE).

Unlike DQN's replay buffer, this buffer stores a fixed number of recent transitions
and is cleared after each update.
"""

import numpy as np
import torch
from typing import Dict, Any, List, Tuple, Optional


class RolloutBuffer:
    """
    Stores trajectories for PPO training.

    Implements Generalized Advantage Estimation (GAE) for advantage calculation.
    """

    def __init__(
        self,
        buffer_size: int,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        device: str = 'cpu'
    ):
        """
        Initialize rollout buffer.

        Args:
            buffer_size: Maximum number of transitions to store
            gamma: Discount factor
            gae_lambda: GAE lambda parameter for advantage estimation
            device: Device to store tensors on
        """
        self.buffer_size = buffer_size
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.device = device

        # Storage
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []

        # Computed during finalize()
        self.advantages = None
        self.returns = None

        self.position = 0
        self.full = False

    def add(
        self,
        state: Dict[str, torch.Tensor],
        action: torch.Tensor,
        reward: float,
        value: float,
        log_prob: float,
        done: bool
    ):
        """
        Add a transition to the buffer.

        Args:
            state: State (sensor data)
            action: Action taken
            reward: Reward received
            value: Value estimate V(s)
            log_prob: Log probability of action
            done: Whether episode terminated
        """
        if len(self.states) < self.buffer_size:
            self.states.append(state)
            self.actions.append(action)
            self.rewards.append(reward)
            self.values.append(value)
            self.log_probs.append(log_prob)
            self.dones.append(done)
        else:
            # Buffer is full, overwrite oldest
            self.states[self.position] = state
            self.actions[self.position] = action
            self.rewards[self.position] = reward
            self.values[self.position] = value
            self.log_probs[self.position] = log_prob
            self.dones[self.position] = done

        self.position = (self.position + 1) % self.buffer_size
        if self.position == 0:
            self.full = True

    def compute_returns_and_advantages(self, last_value: float = 0.0):
        """
        Compute returns and advantages using GAE.

        This should be called at the end of each rollout (or when buffer is full).

        Args:
            last_value: Value estimate of the last state (for incomplete episodes)
        """
        # Convert lists to arrays
        rewards = np.array(self.rewards)
        values = np.array(self.values)
        dones = np.array(self.dones)

        # Add last value for bootstrapping
        values_with_last = np.append(values, last_value)

        # Compute advantages using GAE
        advantages = np.zeros_like(rewards)
        last_gae_lambda = 0

        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_non_terminal = 1.0 - dones[t]
                next_value = last_value
            else:
                next_non_terminal = 1.0 - dones[t]
                next_value = values[t + 1]

            delta = rewards[t] + self.gamma * next_value * next_non_terminal - values[t]
            advantages[t] = last_gae_lambda = delta + self.gamma * self.gae_lambda * next_non_terminal * last_gae_lambda

        # Returns are advantages + values
        returns = advantages + values

        # Normalize advantages (improves training stability)
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

        self.advantages = advantages
        self.returns = returns

    def get(self, batch_size: Optional[int] = None) -> List[Tuple[Dict[str, torch.Tensor], torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]]:
        """
        Get all data from the buffer in batches.

        Args:
            batch_size: Size of each batch (if None, return all data in one batch)

        Returns:
            List of batches, each containing (states, actions, old_log_probs, returns, advantages)
        """
        if self.advantages is None or self.returns is None:
            raise ValueError("Must call compute_returns_and_advantages() before get()")

        # Get all data
        n_samples = len(self.states)
        indices = np.arange(n_samples)

        if batch_size is None:
            batch_size = n_samples

        # Shuffle indices
        np.random.shuffle(indices)

        # Create batches
        batches = []
        for start in range(0, n_samples, batch_size):
            end = min(start + batch_size, n_samples)
            batch_indices = indices[start:end]

            # Collect batch data
            batch_states = self._collate_states([self.states[i] for i in batch_indices])
            batch_actions = torch.stack([self.actions[i] for i in batch_indices]).to(self.device)
            batch_log_probs = torch.FloatTensor([self.log_probs[i] for i in batch_indices]).to(self.device)
            batch_returns = torch.FloatTensor(self.returns[batch_indices]).to(self.device)
            batch_advantages = torch.FloatTensor(self.advantages[batch_indices]).to(self.device)

            batches.append((
                batch_states,
                batch_actions,
                batch_log_probs,
                batch_returns,
                batch_advantages
            ))

        return batches

    def _collate_states(self, states: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """
        Collate a list of state dictionaries into batched tensors.

        Args:
            states: List of state dictionaries

        Returns:
            Dictionary with batched tensors
        """
        batched = {}
        keys = states[0].keys()

        for key in keys:
            batched[key] = torch.stack([s[key] for s in states]).to(self.device)

        return batched

    def clear(self):
        """Clear the buffer."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.values = []
        self.log_probs = []
        self.dones = []
        self.advantages = None
        self.returns = None
        self.position = 0
        self.full = False

    def __len__(self) -> int:
        """Return number of transitions in buffer."""
        return len(self.states)

    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self.full or len(self.states) >= self.buffer_size


class EpisodeBuffer:
    """
    Stores data for a single episode.

    Useful for tracking episode-level statistics and debugging.
    """

    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.infos = []
        self.total_reward = 0.0
        self.length = 0

    def add(
        self,
        state: Dict[str, Any],
        action: np.ndarray,
        reward: float,
        info: Dict[str, Any]
    ):
        """
        Add a transition to the episode.

        Args:
            state: State
            action: Action
            reward: Reward
            info: Additional info
        """
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.infos.append(info)
        self.total_reward += reward
        self.length += 1

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for the episode.

        Returns:
            Dictionary of statistics
        """
        summary = {
            'total_reward': self.total_reward,
            'length': self.length,
            'mean_reward': self.total_reward / max(self.length, 1),
            'collision': any(info.get('collision_vehicle', False) or info.get('collision_pedestrian', False) for info in self.infos),
            'destination_reached': any(info.get('destination_reached', False) for info in self.infos),
            'off_road_count': sum(info.get('off_road', False) for info in self.infos),
            'speeding_count': sum(info.get('speeding', False) for info in self.infos),
        }

        return summary

    def clear(self):
        """Clear the episode buffer."""
        self.states = []
        self.actions = []
        self.rewards = []
        self.infos = []
        self.total_reward = 0.0
        self.length = 0


class MetricsTracker:
    """
    Tracks training metrics over time.
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize metrics tracker.

        Args:
            window_size: Number of recent episodes to track
        """
        self.window_size = window_size

        # Episode metrics
        self.episode_rewards = []
        self.episode_lengths = []
        self.success_rate = []
        self.collision_rate = []

        # Training metrics
        self.actor_losses = []
        self.critic_losses = []
        self.entropies = []

    def add_episode(self, episode_summary: Dict[str, Any]):
        """
        Add episode summary to tracker.

        Args:
            episode_summary: Episode statistics
        """
        self.episode_rewards.append(episode_summary['total_reward'])
        self.episode_lengths.append(episode_summary['length'])

        # Success/failure tracking
        success = episode_summary.get('destination_reached', False) and not episode_summary.get('collision', False)
        collision = episode_summary.get('collision', False)

        self.success_rate.append(1.0 if success else 0.0)
        self.collision_rate.append(1.0 if collision else 0.0)

    def add_training_step(self, actor_loss: float, critic_loss: float, entropy: float):
        """
        Add training step metrics.

        Args:
            actor_loss: Actor network loss
            critic_loss: Critic network loss
            entropy: Policy entropy
        """
        self.actor_losses.append(actor_loss)
        self.critic_losses.append(critic_loss)
        self.entropies.append(entropy)

    def get_recent_stats(self) -> Dict[str, float]:
        """
        Get statistics for recent episodes.

        Returns:
            Dictionary of recent statistics
        """
        recent_rewards = self.episode_rewards[-self.window_size:]
        recent_lengths = self.episode_lengths[-self.window_size:]
        recent_success = self.success_rate[-self.window_size:]
        recent_collision = self.collision_rate[-self.window_size:]

        stats = {
            'mean_reward': np.mean(recent_rewards) if recent_rewards else 0.0,
            'std_reward': np.std(recent_rewards) if recent_rewards else 0.0,
            'mean_length': np.mean(recent_lengths) if recent_lengths else 0.0,
            'success_rate': np.mean(recent_success) if recent_success else 0.0,
            'collision_rate': np.mean(recent_collision) if recent_collision else 0.0,
        }

        if len(self.actor_losses) > 0:
            recent_actor_loss = self.actor_losses[-self.window_size:]
            recent_critic_loss = self.critic_losses[-self.window_size:]
            recent_entropy = self.entropies[-self.window_size:]

            stats.update({
                'actor_loss': np.mean(recent_actor_loss),
                'critic_loss': np.mean(recent_critic_loss),
                'entropy': np.mean(recent_entropy),
            })

        return stats

    def get_all_data(self) -> Dict[str, List[float]]:
        """
        Get all tracked data.

        Returns:
            Dictionary of all metrics
        """
        return {
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths,
            'success_rate': self.success_rate,
            'collision_rate': self.collision_rate,
            'actor_losses': self.actor_losses,
            'critic_losses': self.critic_losses,
            'entropies': self.entropies,
        }
