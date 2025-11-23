# RL Agent - Proximal Policy Optimization for Autonomous Driving

This module implements a complete PPO (Proximal Policy Optimization) reinforcement learning agent for safe, legal, and efficient autonomous driving.

## Overview

The RL agent learns to control a self-driving car using only sensor data (camera, lidar, sonar, GPS, telemetry). It is trained using the PPO algorithm to maximize a reward function that encourages safe, legal, and efficient driving behavior.

## Architecture

### Algorithm: Proximal Policy Optimization (PPO)

PPO is an on-policy reinforcement learning algorithm that:
- Uses clipped surrogate objective for stable learning
- Employs Generalized Advantage Estimation (GAE) for variance reduction
- Includes value function clipping to prevent large updates
- Adds entropy bonus for exploration

**Why PPO?**
- Stable and sample-efficient
- Handles continuous action spaces well
- State-of-the-art for robotic control tasks
- Proven effective for autonomous driving

## Components

### 1. Model (`model.py`)

**ActorCritic Neural Network:**
- **Sensor Encoder**: Processes multi-modal sensor data
  - Lidar encoder (360 distance readings → 64 features)
  - Sonar encoder (8 directional distances → 16 features)
  - GPS encoder (position, heading, waypoints → 32 features)
  - Telemetry encoder (speed, acceleration, etc. → 16 features)
  - Camera encoder (nearby vehicles/pedestrians → 16 features)
  - Total: 144 feature dimensions

- **Actor Network**: Outputs action distribution
  - Input: 144 features
  - Hidden layers: 256 units (configurable)
  - Output: Gaussian distribution over 3 actions (throttle/brake, steering)
  - Outputs mean and std for continuous control

- **Critic Network**: Estimates state value V(s)
  - Input: 144 features
  - Hidden layers: 256 units
  - Output: Single value estimate

**Key Functions:**
- `preprocess_sensor_data()`: Converts raw sensor data to neural network input
- `postprocess_action()`: Converts network output to control commands

### 2. Reward Function (`reward.py`)

Carefully designed reward function that balances multiple objectives:

**Positive Rewards:**
- Progress toward destination (+1.0 per meter)
- Maintaining appropriate speed (+0.5)
- Lane keeping (+0.3)
- Reaching waypoints (+10.0)
- Reaching destination (+100.0)

**Negative Rewards (Penalties):**
- Collision with vehicle (-100.0) **TERMINAL**
- Collision with pedestrian (-200.0) **TERMINAL**
- Off-road driving (-20.0)
- Wrong direction (-10.0)
- Speeding (-10.0)
- Too slow/blocking traffic (-5.0)
- Prohibited zone (-30.0)
- Harsh acceleration/braking (-1.0)
- Time penalty (-0.01 per step)

**Terminal Conditions:**
- Collision (failure)
- Destination reached (success)
- Timeout (neutral)

### 3. Rollout Buffer (`replay_buffer.py`)

**RolloutBuffer:**
- Stores trajectories for on-policy learning
- Computes advantages using GAE (Generalized Advantage Estimation)
- Returns are normalized for stability
- Buffer is cleared after each update

**Supporting Classes:**
- `EpisodeBuffer`: Tracks single episode statistics
- `MetricsTracker`: Tracks training metrics over time

### 4. PPO Agent (`agent.py`)

**Main PPO Implementation:**

**Hyperparameters (default):**
```python
learning_rate = 3e-4
gamma = 0.99  # Discount factor
gae_lambda = 0.95  # GAE parameter
clip_epsilon = 0.2  # PPO clipping
value_loss_coef = 0.5  # Value loss weight
entropy_coef = 0.01  # Entropy bonus
n_epochs = 10  # Update epochs
batch_size = 64
buffer_size = 2048  # Steps before update
```

**Training Process:**
1. Collect 2048 steps of experience
2. Compute advantages using GAE
3. Update policy for 10 epochs using mini-batches
4. Clip policy ratio to prevent large updates
5. Clear buffer and repeat

**Safety Wrapper:**
- Emergency braking if obstacle too close
- Speed limiting in tight situations
- Provides safety intervention when needed

### 5. Training (`training.py`)

**Trainer Class:**
- Manages training loop
- Handles evaluation, checkpointing, and logging
- Plots training curves
- Saves best model based on evaluation

**Training Parameters:**
```python
max_episodes = 1000
max_steps_per_episode = 2000
eval_frequency = 50  # Evaluate every N episodes
save_frequency = 100  # Save checkpoint every N episodes
```

## Usage

### Basic Usage

```python
from rl_agent import create_default_agent, train_agent

# Create agent
agent = create_default_agent(device='cpu')

# Train agent (with your environment)
train_agent(agent, env)
```

### Custom Configuration

```python
from rl_agent import PPOAgent, Trainer

# Custom config
config = {
    'learning_rate': 1e-4,
    'gamma': 0.99,
    'hidden_dim': 512,
    'batch_size': 128,
    'buffer_size': 4096,
}

# Create agent
agent = PPOAgent(config)

# Create trainer
trainer = Trainer(agent, env, config={
    'max_episodes': 2000,
    'eval_frequency': 25,
})

# Train
trainer.train()
```

### Inference (Deployment)

```python
from rl_agent import create_default_agent

# Load trained agent
agent = create_default_agent()
agent.load('checkpoints/rl_agent/best_model.pt')

# Use in real-time
while True:
    sensor_data = env.get_sensor_data()
    control, debug_info = agent.select_action(sensor_data, deterministic=True)
    env.step(control)
```

### With Safety Wrapper

```python
from rl_agent import SafetyWrapper, create_default_agent

agent = create_default_agent()
safe_agent = SafetyWrapper(agent, config={
    'min_safe_distance': 3.0,
    'emergency_brake_threshold': 2.0
})

# Use safely
control, debug = safe_agent.select_action(sensor_data)
```

## Expected Sensor Data Format

The agent expects sensor data in this format:

```python
sensor_data = {
    'lidar': {
        'points': [
            {'angle': 0, 'distance': 30.5, 'intensity': 0.8},
            {'angle': 1, 'distance': 31.2, 'intensity': 0.7},
            # ... 360 points total
        ]
    },
    'sonar': {
        'front_left': 5.2,
        'front_center': 6.0,
        'front_right': 5.8,
        'rear_left': 4.0,
        'rear_center': 4.5,
        'rear_right': 4.2,
        'side_left': 3.0,
        'side_right': 3.2,
    },
    'gps': {
        'position': [x, y],
        'heading': 45.0,  # degrees
        'route': [[x1, y1], [x2, y2], ...],  # waypoints
        'speed_limit': 60,  # km/h
        'current_zone': 'urban',
    },
    'telemetry': {
        'speed': 30.0,  # km/h
        'acceleration': 1.0,  # m/s^2
        'steering_angle': 5.0,  # degrees
        'gear': 1,
    },
    'camera': {
        'vehicles': [
            {'type': 'car', 'position': [x, y], 'confidence': 0.9},
        ],
        'pedestrians': [
            {'position': [x, y], 'confidence': 0.8},
        ],
    }
}
```

## Output Control Format

The agent outputs control commands:

```python
control = {
    'throttle': 0.5,  # 0.0-1.0
    'brake': 0.0,     # 0.0-1.0
    'steering': 0.1,  # -1.0 to 1.0
    'gear': 1,        # Forward gear
}
```

## Training Metrics

The agent tracks:
- **Episode reward**: Cumulative reward per episode
- **Success rate**: % of episodes reaching destination without collision
- **Collision rate**: % of episodes with collisions
- **Average episode length**: Steps per episode
- **Actor loss**: Policy network loss
- **Critic loss**: Value network loss
- **Policy entropy**: Exploration measure

## File Structure

```
src/rl_agent/
├── __init__.py           # Module exports
├── agent.py              # PPO agent implementation
├── model.py              # Neural network architecture
├── reward.py             # Reward function
├── replay_buffer.py      # Rollout buffer and metrics
├── training.py           # Training loop
├── test_agent.py         # Test suite
└── README.md            # This file
```

## Requirements

```
torch>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
```

Install with:
```bash
pip install -r requirements_rl.txt
```

## Testing

Run the test suite:

```bash
python -m src.rl_agent.test_agent
```

This tests:
- Model architecture and forward pass
- Reward function calculation
- Rollout buffer operations
- Agent action selection
- Integration with mock environment

## Integration with Other Agents

**Receives from:**
- **Agent 1 (Map Parser)**: Road network and zone information (via GPS)
- **Agent 2 (Traffic Simulation)**: Vehicle and pedestrian positions (via Camera)
- **Agent 4 (Sensors)**: All sensor data (lidar, sonar, GPS, camera, telemetry)

**Sends to:**
- **Agent 4 (Sensors)**: Control commands (throttle, brake, steering, gear)
- **Agent 3 (Frontend)**: Visualization data (position, actions, rewards)

**Works with:**
- **Agent 6 (Testing)**: Provides evaluation metrics and logs

## Performance Expectations

With default hyperparameters:

**Early Training (Episodes 0-200):**
- Success rate: ~5-10%
- Collision rate: ~40-60%
- Average reward: -50 to 0

**Mid Training (Episodes 200-500):**
- Success rate: ~30-50%
- Collision rate: ~20-30%
- Average reward: 0 to 50

**Late Training (Episodes 500-1000+):**
- Success rate: ~70-90%
- Collision rate: ~5-15%
- Average reward: 50 to 150

## Safety Features

1. **Emergency Braking**: Automatic brake when obstacle < 2m
2. **Speed Limiting**: Reduces speed in tight situations
3. **Reward Shaping**: Heavily penalizes dangerous actions
4. **Collision Avoidance**: Large negative rewards for collisions
5. **Traffic Law Compliance**: Penalties for speeding, wrong direction, etc.

## Future Improvements

- [ ] Curriculum learning (start with simple scenarios)
- [ ] Multi-task learning (different destinations/weather)
- [ ] Transfer learning from simulation to real world
- [ ] Model-based planning for long-horizon decisions
- [ ] Attention mechanisms for better sensor fusion
- [ ] Recurrent networks (LSTM/GRU) for temporal reasoning

## References

- **PPO Paper**: [Proximal Policy Optimization Algorithms](https://arxiv.org/abs/1707.06347)
- **GAE Paper**: [High-Dimensional Continuous Control Using Generalized Advantage Estimation](https://arxiv.org/abs/1506.02438)
- **Autonomous Driving RL**: Various research papers on deep RL for self-driving cars

## Contact

Agent 5 - RL Agent
Part of the Autonomous Taxi Simulation multi-agent system
