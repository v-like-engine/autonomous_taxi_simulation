# Agent 5: Reinforcement Learning Agent

## Responsibility
You are responsible for implementing the reinforcement learning algorithm that controls the self-driving car safely and legally.

## Your Files (DO NOT modify files outside this list)
- `src/rl_agent/agent.py` - Main RL agent implementation
- `src/rl_agent/model.py` - Neural network model
- `src/rl_agent/training.py` - Training loop and logic
- `src/rl_agent/replay_buffer.py` - Experience replay buffer
- `src/rl_agent/reward.py` - Reward function design
- `src/rl_agent/__init__.py` - Module exports

## Requirements

### RL Algorithm
Implement a reinforcement learning algorithm. Recommended approaches:
- **Deep Q-Network (DQN)** - Simple, proven, good for discrete actions
- **Proximal Policy Optimization (PPO)** - More advanced, handles continuous actions well
- **Soft Actor-Critic (SAC)** - State-of-the-art for continuous control
- **TD3 (Twin Delayed DDPG)** - Robust continuous control

**Choose ONE algorithm** and implement it well. DQN or PPO recommended for this project.

### State Space (Input from Agent 4)
The agent receives sensor data from Agent 4:
- **Camera data**: Ambiguous vehicle/pedestrian positions
- **Lidar data**: Accurate point cloud (limited range)
- **Sonar data**: Close-range distances
- **GPS data**: Position, heading, route, speed limit
- **Telemetry**: Speed, acceleration, steering angle

**State Representation:**
Process raw sensor data into a usable state vector or image:
- Option 1: Feature vector (concatenate processed sensor data)
- Option 2: Multi-channel image (render sensors as images for CNN)
- Option 3: Hybrid approach

### Action Space (Output to Agent 4)
Control the car through Agent 4's control interface:
- **Throttle**: 0.0-1.0 (continuous)
- **Brake**: 0.0-1.0 (continuous)
- **Steering**: -1.0-1.0 (continuous)
- **Gear**: -1, 0, 1, 2, 3, 4, 5 (discrete) - Can be simplified to just forward/reverse/neutral

**Simplified Action Space:**
For easier learning, you can discretize or simplify:
- Discrete: {accelerate, brake, turn_left, turn_right, coast, ...}
- Continuous: {throttle, brake, steering} (gear can be automatic)

### Reward Function
Design a reward function that encourages safe, legal, efficient driving:

**Positive Rewards:**
- +reward for moving toward destination
- +reward for maintaining appropriate speed
- +reward for staying in lane
- +reward for reaching waypoints
- +large reward for reaching final destination

**Negative Rewards (Penalties):**
- -large penalty for collision with vehicle (CRITICAL)
- -large penalty for hitting pedestrian (CRITICAL)
- -penalty for going off-road
- -penalty for driving in opposite direction
- -penalty for speeding (over speed_limit + 20 km/h)
- -penalty for driving too slow (blocking traffic)
- -penalty for entering prohibited zones
- -penalty for harsh braking/acceleration (comfort)
- -small penalty for time (encourages efficiency)

**Terminal Conditions:**
- Episode ends on collision (negative reward)
- Episode ends on reaching destination (positive reward)
- Episode ends on timeout (neutral/small negative)
- Episode ends if car gets stuck

**Reward Shaping:**
Carefully balance rewards to encourage desired behavior:
```python
reward = (
    progress_reward * 1.0 +
    speed_reward * 0.5 +
    lane_keeping_reward * 0.3 +
    collision_penalty * -100.0 +
    pedestrian_penalty * -200.0 +
    speeding_penalty * -10.0 +
    ...
)
```

### Safety Constraints
The car MUST:
- ✓ Not hit other vehicles
- ✓ Not hit pedestrians
- ✓ Not exceed speed_limit + 20 km/h
- ✓ Not drive off roads
- ✓ Not drive in opposite direction
- ✓ Not enter prohibited zones
- ✓ Follow traffic rules

### Route Following
- Use GPS route from Agent 4
- Navigate to waypoints in sequence
- If waypoint is unreachable (blocked, prohibited), approach as close as possible
- Stop at closest legal stopping point if destination unreachable

### Training
Implement training loop:
- Collect experiences from simulation
- Store in replay buffer
- Sample mini-batches and update model
- Track performance metrics (reward, success rate, collision rate)
- Save model checkpoints

**Training Parameters:**
- Episodes: 1000+ (or until convergence)
- Steps per episode: 1000-5000
- Batch size: 32-256
- Learning rate: 1e-4 to 1e-3
- Discount factor (gamma): 0.95-0.99

### Inference (Deployment)
- Load trained model
- Process sensor data in real-time
- Output control actions
- Handle edge cases gracefully

### Model Architecture
If using neural network (DQN/PPO/SAC):
- **Input Layer**: Process sensor data
- **Hidden Layers**: 2-4 layers, 256-512 units each
- **Output Layer**: Action values or action distribution
- Activation: ReLU or Tanh
- Optional: CNN layers if using image-based state

### Evaluation Metrics
Track and report:
- Success rate (reached destination without collision)
- Average reward per episode
- Collision rate (collisions per episode)
- Traffic violations (speeding, wrong direction, etc.)
- Average time to destination
- Smoothness (acceleration/braking variance)

## Technical Stack
- **Framework**: PyTorch or TensorFlow
- **RL Library**: Stable-Baselines3 (recommended) or implement from scratch
- **Numpy**: For numerical operations

## Deliverables
1. Trained RL agent that can navigate safely
2. Training script with hyperparameters
3. Inference script for real-time control
4. Model checkpoints
5. Training curves and metrics

## Communication
- Receive sensor data from Agent 4
- Send control actions to Agent 4
- Use traffic simulation from Agent 2 as environment
- Provide status/metrics to Agent 3 for visualization
- Monitor `.claude/agents/rl_agent.md` for notes from Agent 6

## Notes from Agent 6 (Testing & Documentation)
<!-- Agent 6 will write notes here -->
