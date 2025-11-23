"""
Reinforcement Learning Agent Module

This module provides a complete PPO-based RL agent for autonomous driving.

Main Components:
- PPOAgent: Main RL agent
- ActorCritic: Neural network model
- RewardFunction: Reward shaping for safe driving
- Trainer: Training infrastructure

Usage:
    from rl_agent import PPOAgent, train_agent

    # Create agent
    agent = PPOAgent()

    # Train agent
    train_agent(agent, env)

    # Use trained agent
    control = agent.select_action(sensor_data, deterministic=True)
"""

from .agent import PPOAgent, SafetyWrapper, create_default_agent
from .model import ActorCritic, preprocess_sensor_data, postprocess_action
from .reward import RewardFunction, create_default_reward_function
from .replay_buffer import RolloutBuffer, EpisodeBuffer, MetricsTracker
from .training import Trainer, train_agent, MockEnvironment

__all__ = [
    # Agent
    'PPOAgent',
    'SafetyWrapper',
    'create_default_agent',

    # Model
    'ActorCritic',
    'preprocess_sensor_data',
    'postprocess_action',

    # Reward
    'RewardFunction',
    'create_default_reward_function',

    # Buffer
    'RolloutBuffer',
    'EpisodeBuffer',
    'MetricsTracker',

    # Training
    'Trainer',
    'train_agent',
    'MockEnvironment',
]

__version__ = '1.0.0'
__author__ = 'Agent 5 - RL Agent'
