"""
Reward Function for Self-Driving Car RL Agent

This module implements the reward function that encourages safe, legal, and efficient driving.
The reward function is critical for shaping the agent's behavior.
"""

import numpy as np
from typing import Dict, Any, Tuple


class RewardFunction:
    """
    Calculates rewards for the RL agent based on driving behavior.

    Rewards are designed to encourage:
    - Safe driving (no collisions)
    - Legal driving (follow traffic laws)
    - Efficient driving (reach destination quickly)
    - Comfortable driving (smooth acceleration/braking)
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize reward function with configurable weights.

        Args:
            config: Dictionary containing reward weights and parameters
        """
        self.config = config or {}

        # Reward weights (can be tuned)
        self.weights = {
            # Positive rewards
            'progress': self.config.get('progress_weight', 1.0),
            'speed': self.config.get('speed_weight', 0.5),
            'lane_keeping': self.config.get('lane_keeping_weight', 0.3),
            'waypoint_reached': self.config.get('waypoint_weight', 10.0),
            'destination_reached': self.config.get('destination_weight', 100.0),

            # Negative rewards (penalties)
            'collision_vehicle': self.config.get('collision_vehicle_penalty', -100.0),
            'collision_pedestrian': self.config.get('collision_pedestrian_penalty', -200.0),
            'off_road': self.config.get('off_road_penalty', -20.0),
            'wrong_direction': self.config.get('wrong_direction_penalty', -10.0),
            'speeding': self.config.get('speeding_penalty', -10.0),
            'too_slow': self.config.get('too_slow_penalty', -5.0),
            'prohibited_zone': self.config.get('prohibited_zone_penalty', -30.0),
            'harsh_action': self.config.get('harsh_action_penalty', -1.0),
            'time_penalty': self.config.get('time_penalty', -0.01),
        }

        # State tracking for progress calculation
        self.previous_distance_to_goal = None
        self.previous_waypoint_index = 0
        self.total_distance_traveled = 0.0

    def reset(self):
        """Reset internal state for a new episode."""
        self.previous_distance_to_goal = None
        self.previous_waypoint_index = 0
        self.total_distance_traveled = 0.0

    def calculate_reward(
        self,
        state: Dict[str, Any],
        action: np.ndarray,
        next_state: Dict[str, Any],
        info: Dict[str, Any]
    ) -> Tuple[float, bool, Dict[str, float]]:
        """
        Calculate reward for the current transition.

        Args:
            state: Current state (sensor data)
            action: Action taken [throttle, brake, steering]
            next_state: Next state after action
            info: Additional information (collisions, violations, etc.)

        Returns:
            Tuple of (total_reward, done, reward_components)
        """
        reward_components = {}
        done = False

        # Extract information
        gps = next_state.get('gps', {})
        telemetry = next_state.get('telemetry', {})

        current_pos = np.array(gps.get('position', [0, 0]))
        route = gps.get('route', [])
        speed_limit = gps.get('speed_limit', 60)
        current_speed = telemetry.get('speed', 0)

        # 1. CRITICAL: Collision penalties (terminal)
        if info.get('collision_vehicle', False):
            reward_components['collision_vehicle'] = self.weights['collision_vehicle']
            done = True

        if info.get('collision_pedestrian', False):
            reward_components['collision_pedestrian'] = self.weights['collision_pedestrian']
            done = True

        # 2. Progress reward (moving toward destination)
        if len(route) > 0:
            next_waypoint = np.array(route[0])
            distance_to_goal = np.linalg.norm(current_pos - next_waypoint)

            if self.previous_distance_to_goal is not None:
                progress = self.previous_distance_to_goal - distance_to_goal
                reward_components['progress'] = self.weights['progress'] * progress

            self.previous_distance_to_goal = distance_to_goal

        # 3. Speed reward (maintaining appropriate speed)
        target_speed = min(speed_limit, 80)  # Don't go too fast even if limit is high
        speed_error = abs(current_speed - target_speed)

        if current_speed > speed_limit + 20:
            # Speeding violation
            reward_components['speeding'] = self.weights['speeding']
        elif current_speed < 10 and speed_limit > 30:
            # Too slow (blocking traffic)
            reward_components['too_slow'] = self.weights['too_slow']
        else:
            # Reward for being near target speed
            speed_reward = np.exp(-speed_error / 20.0)  # Exponential decay
            reward_components['speed'] = self.weights['speed'] * speed_reward

        # 4. Lane keeping reward
        if 'distance_from_lane_center' in info:
            lane_distance = info['distance_from_lane_center']
            lane_reward = np.exp(-lane_distance)  # Exponential decay
            reward_components['lane_keeping'] = self.weights['lane_keeping'] * lane_reward

        # 5. Waypoint reached bonus
        if info.get('waypoint_reached', False):
            reward_components['waypoint_reached'] = self.weights['waypoint_reached']

        # 6. Destination reached (terminal - success!)
        if info.get('destination_reached', False):
            reward_components['destination_reached'] = self.weights['destination_reached']
            done = True

        # 7. Off-road penalty
        if info.get('off_road', False):
            reward_components['off_road'] = self.weights['off_road']

        # 8. Wrong direction penalty
        if info.get('wrong_direction', False):
            reward_components['wrong_direction'] = self.weights['wrong_direction']

        # 9. Prohibited zone penalty
        if info.get('in_prohibited_zone', False):
            reward_components['prohibited_zone'] = self.weights['prohibited_zone']

        # 10. Harsh action penalty (comfort)
        throttle, brake, steering = action[0], action[1], action[2]

        # Penalize harsh braking or acceleration
        if abs(brake) > 0.8 or abs(throttle) > 0.9:
            harshness = max(abs(brake), abs(throttle))
            reward_components['harsh_action'] = self.weights['harsh_action'] * harshness

        # Penalize harsh steering
        if abs(steering) > 0.8:
            reward_components['harsh_action'] = self.weights['harsh_action'] * abs(steering)

        # 11. Time penalty (encourages efficiency)
        reward_components['time_penalty'] = self.weights['time_penalty']

        # 12. Timeout check
        if info.get('timeout', False):
            done = True

        # Calculate total reward
        total_reward = sum(reward_components.values())

        return total_reward, done, reward_components

    def get_reward_summary(self, reward_components: Dict[str, float]) -> str:
        """
        Get a human-readable summary of reward components.

        Args:
            reward_components: Dictionary of reward components

        Returns:
            String summary
        """
        lines = ["Reward Components:"]
        for key, value in sorted(reward_components.items(), key=lambda x: abs(x[1]), reverse=True):
            if value != 0:
                lines.append(f"  {key}: {value:.3f}")
        lines.append(f"  TOTAL: {sum(reward_components.values()):.3f}")
        return "\n".join(lines)


class RewardShaper:
    """
    Advanced reward shaping techniques for better learning.
    """

    @staticmethod
    def potential_based_shaping(
        state: Dict[str, Any],
        next_state: Dict[str, Any],
        gamma: float = 0.99
    ) -> float:
        """
        Potential-based reward shaping to guide the agent.

        This maintains optimal policy invariance while providing denser rewards.

        Args:
            state: Current state
            next_state: Next state
            gamma: Discount factor

        Returns:
            Shaping reward
        """
        def potential(s):
            """Potential function based on distance to goal."""
            gps = s.get('gps', {})
            pos = np.array(gps.get('position', [0, 0]))
            route = gps.get('route', [])

            if len(route) == 0:
                return 0.0

            next_waypoint = np.array(route[0])
            distance = np.linalg.norm(pos - next_waypoint)

            # Negative distance as potential (closer = higher potential)
            return -distance

        phi_current = potential(state)
        phi_next = potential(next_state)

        # Shaping reward: F = gamma * phi(s') - phi(s)
        return gamma * phi_next - phi_current

    @staticmethod
    def curiosity_bonus(state_features: np.ndarray, novelty_threshold: float = 0.1) -> float:
        """
        Curiosity-driven exploration bonus.

        Rewards the agent for exploring novel states.

        Args:
            state_features: Feature representation of state
            novelty_threshold: Threshold for novelty detection

        Returns:
            Curiosity bonus
        """
        # This would require maintaining a state visitation count or embedding
        # For now, return 0 (can be implemented with proper state tracking)
        return 0.0


def create_default_reward_function() -> RewardFunction:
    """
    Create a reward function with default parameters.

    Returns:
        Configured RewardFunction instance
    """
    return RewardFunction({
        'progress_weight': 1.0,
        'speed_weight': 0.5,
        'lane_keeping_weight': 0.3,
        'waypoint_weight': 10.0,
        'destination_weight': 100.0,
        'collision_vehicle_penalty': -100.0,
        'collision_pedestrian_penalty': -200.0,
        'off_road_penalty': -20.0,
        'wrong_direction_penalty': -10.0,
        'speeding_penalty': -10.0,
        'too_slow_penalty': -5.0,
        'prohibited_zone_penalty': -30.0,
        'harsh_action_penalty': -1.0,
        'time_penalty': -0.01,
    })
