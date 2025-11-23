# RL Agent Documentation

Documentation for the Reinforcement Learning Agent module (Agent 5).

## Overview

The RL Agent module implements a reinforcement learning algorithm to control the autonomous taxi safely and legally using only sensor data.

## Algorithm

**Recommended Algorithms:**
- **DQN (Deep Q-Network)**: Simple, proven, good for discrete actions
- **PPO (Proximal Policy Optimization)**: Advanced, handles continuous actions
- **SAC (Soft Actor-Critic)**: State-of-the-art continuous control
- **TD3 (Twin Delayed DDPG)**: Robust continuous control

**Implementation**: Choose ONE algorithm and implement it well.

## Components

### Agent (`agent.py`)

Main RL agent that processes sensor data and makes decisions.

**Key Methods:**
```python
class Agent:
    def __init__(self, state_dim, action_dim, config):
        # Initialize agent

    def select_action(self, state, explore=True):
        # Select action from state
        # explore=True: training mode (exploration)
        # explore=False: inference mode (exploitation)

    def update(self, batch):
        # Update model using experience batch

    def save(self, path):
        # Save model checkpoint

    def load(self, path):
        # Load model checkpoint
```

**Usage:**
```python
from src.rl_agent.agent import Agent

agent = Agent(state_dim=64, action_dim=3, config=config)

# Training
action = agent.select_action(state, explore=True)

# Inference
action = agent.select_action(state, explore=False)
```

### Model (`model.py`)

Neural network model for the agent.

**Architecture (Example for DQN):**
```python
Input Layer (state_dim) →
Hidden Layer 1 (256, ReLU) →
Hidden Layer 2 (256, ReLU) →
Hidden Layer 3 (128, ReLU) →
Output Layer (action_dim)
```

**For continuous actions (PPO/SAC):**
- Actor network: Outputs action distribution
- Critic network: Outputs state value

**Usage:**
```python
from src.rl_agent.model import Model

model = Model(state_dim=64, action_dim=3, hidden_dims=[256, 256, 128])
q_values = model(state)
```

### Training (`training.py`)

Training loop and logic.

**Key Functions:**
```python
def train(agent, env, num_episodes, config):
    for episode in range(num_episodes):
        state = env.reset()
        episode_reward = 0

        for step in range(max_steps):
            # Select action
            action = agent.select_action(state, explore=True)

            # Execute action
            next_state, reward, done, info = env.step(action)

            # Store experience
            replay_buffer.add(state, action, reward, next_state, done)

            # Update agent
            if len(replay_buffer) > batch_size:
                batch = replay_buffer.sample(batch_size)
                agent.update(batch)

            episode_reward += reward
            state = next_state

            if done:
                break

        # Save checkpoint
        if episode % save_interval == 0:
            agent.save(f'models/checkpoint_{episode}.pth')
```

**Usage:**
```bash
python src/rl_agent/training.py --episodes 1000 --batch-size 128
```

### Replay Buffer (`replay_buffer.py`)

Stores and samples experiences for training.

**Key Methods:**
```python
class ReplayBuffer:
    def __init__(self, capacity):
        # Initialize buffer

    def add(self, state, action, reward, next_state, done):
        # Add experience

    def sample(self, batch_size):
        # Sample random batch

    def __len__(self):
        # Return buffer size
```

**Usage:**
```python
from src.rl_agent.replay_buffer import ReplayBuffer

buffer = ReplayBuffer(capacity=100000)
buffer.add(state, action, reward, next_state, done)

if len(buffer) > batch_size:
    batch = buffer.sample(batch_size)
```

### Reward Function (`reward.py`)

Defines the reward structure for the agent.

**Reward Components:**

**Positive Rewards:**
- Progress toward destination: +1.0 per meter
- Maintaining speed: +0.5 for appropriate speed
- Lane keeping: +0.3 for staying in lane
- Reaching waypoint: +10.0
- Reaching destination: +100.0

**Negative Rewards (Penalties):**
- Collision with vehicle: -100.0 (CRITICAL)
- Hitting pedestrian: -200.0 (CRITICAL)
- Off-road: -5.0 per step
- Wrong direction: -10.0 per step
- Speeding (>limit+20): -10.0
- Too slow (blocking traffic): -2.0
- Prohibited zone: -20.0
- Harsh braking/acceleration: -1.0

**Implementation:**
```python
def calculate_reward(state, action, next_state, world):
    reward = 0

    # Progress reward
    progress = distance_to_destination(state) - distance_to_destination(next_state)
    reward += progress * 1.0

    # Speed reward
    if in_appropriate_speed_range(next_state):
        reward += 0.5

    # Penalties
    if collision_detected(next_state):
        reward -= 100.0
    if pedestrian_hit(next_state):
        reward -= 200.0
    if off_road(next_state):
        reward -= 5.0

    return reward
```

## State Space

The agent receives sensor data from Agent 4:

**Raw Sensor Data:**
- Lidar point cloud (360 points)
- Camera detections (variable number of objects)
- Sonar distances (8 sensors)
- GPS position and route
- Telemetry (speed, acceleration, etc.)

**State Representation Options:**

**Option 1: Feature Vector**
```python
state = [
    # Lidar (simplified to 36 bins)
    min_distance_per_sector[36],

    # Camera (simplified)
    nearest_vehicle_distance,
    nearest_vehicle_angle,
    nearest_pedestrian_distance,
    nearest_pedestrian_angle,

    # Sonar
    sonar_distances[8],

    # GPS & Telemetry
    distance_to_destination,
    angle_to_destination,
    current_speed,
    current_acceleration,
    steering_angle,
    current_zone_speed_limit,

    # Total: ~52 features
]
```

**Option 2: Image-based (for CNN)**
```python
state = multi_channel_image(
    channels=[
        lidar_visualization,
        camera_visualization,
        route_visualization
    ],
    size=(84, 84, 3)
)
```

## Action Space

**Continuous Action Space:**
```python
action = [
    throttle,   # 0.0 to 1.0
    brake,      # 0.0 to 1.0
    steering    # -1.0 to 1.0
]
```

**Discrete Action Space (simplified):**
```python
actions = [
    "accelerate",
    "brake",
    "coast",
    "turn_left",
    "turn_right",
    "turn_left_accelerate",
    "turn_right_accelerate",
    "turn_left_brake",
    "turn_right_brake"
]
```

## Training Process

### Hyperparameters

**Recommended Settings:**
```python
config = {
    "episodes": 2000,
    "max_steps_per_episode": 1000,
    "batch_size": 128,
    "learning_rate": 1e-4,
    "gamma": 0.99,  # discount factor
    "tau": 0.005,   # soft update rate
    "epsilon_start": 1.0,  # exploration
    "epsilon_end": 0.01,
    "epsilon_decay": 0.995,
    "replay_buffer_size": 100000,
    "update_frequency": 4,
    "save_interval": 100
}
```

### Training Metrics

Track these metrics:
- **Episode Reward**: Total reward per episode
- **Success Rate**: % of episodes reaching destination
- **Collision Rate**: % of episodes with collision
- **Average Speed**: Mean speed during episode
- **Traffic Violations**: Count of violations
- **Training Loss**: Model loss
- **Q-value**: Mean Q-value (for DQN)

### Training Tips

1. **Start Simple**: Begin with empty map or low traffic
2. **Curriculum Learning**: Gradually increase difficulty
3. **Reward Shaping**: Carefully balance reward components
4. **Exploration**: Start with high exploration, decay over time
5. **Checkpoints**: Save frequently to avoid losing progress
6. **Visualization**: Watch agent behavior to debug
7. **Metrics**: Monitor all metrics, not just reward

## Evaluation

### Evaluation Metrics

```python
metrics = {
    "success_rate": 0.85,        # 85% reached destination
    "collision_rate": 0.03,      # 3% had collisions
    "avg_reward": 145.2,
    "avg_time_to_dest": 120.5,   # seconds
    "avg_speed": 45.3,           # km/h
    "violations_per_episode": 0.5,
    "smoothness": 0.92           # 0-1, higher is smoother
}
```

### Testing Scenarios

Test the trained agent on:
1. **Empty roads**: Basic navigation
2. **Light traffic**: Normal conditions
3. **Heavy traffic**: Congestion handling
4. **Aggressive drivers**: Dealing with violations
5. **Complex routes**: Multiple waypoints
6. **Emergency stops**: Sudden pedestrians

## Inference

Using a trained model:

```python
from src.rl_agent.agent import Agent

# Load trained model
agent = Agent(state_dim=52, action_dim=3)
agent.load('models/best_model.pth')

# Inference loop
while not done:
    # Get sensor data
    sensor_data = get_sensor_data()

    # Process to state
    state = process_sensor_data(sensor_data)

    # Select action (no exploration)
    action = agent.select_action(state, explore=False)

    # Execute action
    execute_control(action)
```

## Configuration

```yaml
# config/rl_agent.yaml
training:
  episodes: 2000
  batch_size: 128
  learning_rate: 0.0001
  gamma: 0.99
  epsilon_start: 1.0
  epsilon_end: 0.01
  epsilon_decay: 0.995

model:
  hidden_layers: [256, 256, 128]
  activation: relu
  optimizer: adam

reward:
  progress_weight: 1.0
  speed_weight: 0.5
  lane_weight: 0.3
  collision_penalty: 100.0
  pedestrian_penalty: 200.0

environment:
  max_steps: 1000
  success_distance: 5.0  # meters to destination
  timeout: 300  # seconds
```

## Troubleshooting

**Issue: Agent doesn't learn (reward doesn't increase)**
- Check reward function balance
- Increase learning rate
- Increase exploration
- Simplify environment

**Issue: Agent learns to exploit reward**
- Fix reward function loopholes
- Add penalties for undesired behavior
- Use shaped rewards carefully

**Issue: Agent too cautious or too aggressive**
- Adjust penalty weights
- Modify temperature of behavior
- Change exploration strategy

**Issue: Training is slow**
- Reduce batch size
- Increase update frequency
- Use GPU if available
- Simplify state representation

## API Reference

See [API Documentation](api.md#rl-agent-api).
