"""
Neural Network Models for PPO Agent

This module implements the Actor-Critic architecture for Proximal Policy Optimization (PPO).
- Actor: Outputs action distribution (mean and std for continuous actions)
- Critic: Outputs state value estimate
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Dict, Any


class SensorEncoder(nn.Module):
    """
    Encodes raw sensor data into a feature representation.

    Processes multiple sensor modalities:
    - Lidar point cloud
    - Sonar readings
    - GPS/route information
    - Telemetry data
    - Camera detections (simplified)
    """

    def __init__(self, config: Dict[str, Any] = None):
        super(SensorEncoder, self).__init__()
        self.config = config or {}

        # Lidar encoder (processes 360 distance readings)
        self.lidar_dim = self.config.get('lidar_points', 360)
        self.lidar_encoder = nn.Sequential(
            nn.Linear(self.lidar_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU()
        )

        # Sonar encoder (8 sensors around the car)
        self.sonar_dim = 8
        self.sonar_encoder = nn.Sequential(
            nn.Linear(self.sonar_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU()
        )

        # GPS/Route encoder (position, heading, waypoints)
        # Input: [current_x, current_y, heading, next_waypoint_x, next_waypoint_y,
        #         distance_to_waypoint, angle_to_waypoint, speed_limit]
        self.gps_dim = 8
        self.gps_encoder = nn.Sequential(
            nn.Linear(self.gps_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU()
        )

        # Telemetry encoder (speed, acceleration, steering angle, gear)
        self.telemetry_dim = 4
        self.telemetry_encoder = nn.Sequential(
            nn.Linear(self.telemetry_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU()
        )

        # Camera encoder (simplified: nearby vehicles and pedestrians)
        # Input: [num_vehicles_front, avg_vehicle_distance, num_pedestrians, avg_ped_distance]
        self.camera_dim = 4
        self.camera_encoder = nn.Sequential(
            nn.Linear(self.camera_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU()
        )

        # Total feature dimension after encoding all sensors
        self.feature_dim = 64 + 16 + 32 + 16 + 16  # 144 total

    def forward(self, sensor_data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Encode sensor data into feature vector.

        Args:
            sensor_data: Dictionary containing sensor tensors

        Returns:
            Feature tensor of shape [batch_size, feature_dim]
        """
        lidar_features = self.lidar_encoder(sensor_data['lidar'])
        sonar_features = self.sonar_encoder(sensor_data['sonar'])
        gps_features = self.gps_encoder(sensor_data['gps'])
        telemetry_features = self.telemetry_encoder(sensor_data['telemetry'])
        camera_features = self.camera_encoder(sensor_data['camera'])

        # Concatenate all features
        features = torch.cat([
            lidar_features,
            sonar_features,
            gps_features,
            telemetry_features,
            camera_features
        ], dim=-1)

        return features


class Actor(nn.Module):
    """
    Actor network for PPO.

    Outputs a continuous action distribution (Gaussian) for:
    - Throttle (0 to 1)
    - Brake (0 to 1)
    - Steering (-1 to 1)
    """

    def __init__(self, feature_dim: int, hidden_dim: int = 256, action_dim: int = 3):
        super(Actor, self).__init__()

        self.feature_dim = feature_dim
        self.action_dim = action_dim

        # Shared layers
        self.shared = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )

        # Mean of action distribution
        self.action_mean = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Tanh()  # Output in [-1, 1], will be scaled appropriately
        )

        # Log standard deviation of action distribution (learnable)
        self.action_log_std = nn.Parameter(torch.zeros(1, action_dim))

    def forward(self, features: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through actor.

        Args:
            features: Encoded sensor features

        Returns:
            Tuple of (action_mean, action_std)
        """
        shared_output = self.shared(features)
        action_mean = self.action_mean(shared_output)

        # Expand log_std to match batch size
        action_log_std = self.action_log_std.expand_as(action_mean)
        action_std = torch.exp(action_log_std)

        return action_mean, action_std

    def get_action(self, features: torch.Tensor, deterministic: bool = False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Sample action from the policy.

        Args:
            features: Encoded sensor features
            deterministic: If True, return mean action (no noise)

        Returns:
            Tuple of (action, log_prob, entropy)
        """
        action_mean, action_std = self.forward(features)

        if deterministic:
            action = action_mean
            # For deterministic actions, log_prob and entropy are not meaningful
            dist = torch.distributions.Normal(action_mean, action_std)
            log_prob = dist.log_prob(action).sum(dim=-1)
            entropy = dist.entropy().sum(dim=-1)
        else:
            # Sample from Gaussian distribution
            dist = torch.distributions.Normal(action_mean, action_std)
            action = dist.sample()
            log_prob = dist.log_prob(action).sum(dim=-1)
            entropy = dist.entropy().sum(dim=-1)

        return action, log_prob, entropy

    def evaluate_actions(self, features: torch.Tensor, actions: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Evaluate log probability and entropy of given actions.

        Used during training to compute policy loss.

        Args:
            features: Encoded sensor features
            actions: Actions to evaluate

        Returns:
            Tuple of (log_prob, entropy)
        """
        action_mean, action_std = self.forward(features)
        dist = torch.distributions.Normal(action_mean, action_std)

        log_prob = dist.log_prob(actions).sum(dim=-1)
        entropy = dist.entropy().sum(dim=-1)

        return log_prob, entropy


class Critic(nn.Module):
    """
    Critic network for PPO.

    Outputs state value estimate V(s).
    """

    def __init__(self, feature_dim: int, hidden_dim: int = 256):
        super(Critic, self).__init__()

        self.network = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through critic.

        Args:
            features: Encoded sensor features

        Returns:
            State value estimate
        """
        return self.network(features).squeeze(-1)


class ActorCritic(nn.Module):
    """
    Combined Actor-Critic model for PPO.

    Includes sensor encoder, actor, and critic networks.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super(ActorCritic, self).__init__()
        self.config = config or {}

        # Sensor encoder
        self.encoder = SensorEncoder(self.config)

        # Actor and Critic networks
        feature_dim = self.encoder.feature_dim
        hidden_dim = self.config.get('hidden_dim', 256)
        action_dim = self.config.get('action_dim', 3)

        self.actor = Actor(feature_dim, hidden_dim, action_dim)
        self.critic = Critic(feature_dim, hidden_dim)

    def forward(self, sensor_data: Dict[str, torch.Tensor]) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Full forward pass through the model.

        Args:
            sensor_data: Dictionary of sensor tensors

        Returns:
            Tuple of (action, log_prob, entropy, value)
        """
        features = self.encoder(sensor_data)
        action, log_prob, entropy = self.actor.get_action(features)
        value = self.critic(features)

        return action, log_prob, entropy, value

    def get_action(self, sensor_data: Dict[str, torch.Tensor], deterministic: bool = False) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get action from the policy.

        Args:
            sensor_data: Dictionary of sensor tensors
            deterministic: If True, return mean action

        Returns:
            Tuple of (action, log_prob, entropy, value)
        """
        features = self.encoder(sensor_data)
        action, log_prob, entropy = self.actor.get_action(features, deterministic)
        value = self.critic(features)

        return action, log_prob, entropy, value

    def get_value(self, sensor_data: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Get state value estimate.

        Args:
            sensor_data: Dictionary of sensor tensors

        Returns:
            State value
        """
        features = self.encoder(sensor_data)
        value = self.critic(features)

        return value

    def evaluate_actions(self, sensor_data: Dict[str, torch.Tensor], actions: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Evaluate actions for training.

        Args:
            sensor_data: Dictionary of sensor tensors
            actions: Actions to evaluate

        Returns:
            Tuple of (log_prob, entropy, value)
        """
        features = self.encoder(sensor_data)
        log_prob, entropy = self.actor.evaluate_actions(features, actions)
        value = self.critic(features)

        return log_prob, entropy, value


def preprocess_sensor_data(raw_sensor_data: Dict[str, Any]) -> Dict[str, torch.Tensor]:
    """
    Preprocess raw sensor data into tensor format for the network.

    Args:
        raw_sensor_data: Raw sensor data from environment

    Returns:
        Dictionary of preprocessed tensors
    """
    processed = {}

    # Lidar: Extract distances from point cloud (360 points)
    lidar = raw_sensor_data.get('lidar', {})
    points = lidar.get('points', [])

    if len(points) > 0:
        # Extract distances at regular intervals
        distances = np.array([p.get('distance', 50.0) for p in points])
        # Normalize distances (max range ~50m)
        distances = np.clip(distances, 0, 50) / 50.0
    else:
        distances = np.ones(360) * 1.0  # Max distance if no data

    # Ensure we have exactly 360 points
    if len(distances) < 360:
        distances = np.pad(distances, (0, 360 - len(distances)), constant_values=1.0)
    elif len(distances) > 360:
        # Subsample to 360 points
        indices = np.linspace(0, len(distances) - 1, 360, dtype=int)
        distances = distances[indices]

    processed['lidar'] = torch.FloatTensor(distances)

    # Sonar: 8 directional distances
    sonar = raw_sensor_data.get('sonar', {})
    sonar_readings = np.array([
        sonar.get('front_left', 10.0),
        sonar.get('front_center', 10.0),
        sonar.get('front_right', 10.0),
        sonar.get('side_left', 10.0),
        sonar.get('side_right', 10.0),
        sonar.get('rear_left', 10.0),
        sonar.get('rear_center', 10.0),
        sonar.get('rear_right', 10.0),
    ])
    # Normalize (max range ~10m)
    sonar_readings = np.clip(sonar_readings, 0, 10) / 10.0
    processed['sonar'] = torch.FloatTensor(sonar_readings)

    # GPS: Position, heading, route
    gps = raw_sensor_data.get('gps', {})
    position = np.array(gps.get('position', [0, 0]))
    heading = gps.get('heading', 0.0)
    route = gps.get('route', [])
    speed_limit = gps.get('speed_limit', 60)

    if len(route) > 0:
        next_waypoint = np.array(route[0])
        distance_to_waypoint = np.linalg.norm(position - next_waypoint)
        angle_to_waypoint = np.arctan2(
            next_waypoint[1] - position[1],
            next_waypoint[0] - position[0]
        )
        # Convert to degrees
        angle_to_waypoint = np.degrees(angle_to_waypoint)
        # Relative angle to heading
        relative_angle = (angle_to_waypoint - heading + 180) % 360 - 180
    else:
        next_waypoint = position
        distance_to_waypoint = 0
        relative_angle = 0

    gps_vector = np.array([
        position[0] / 1000.0,  # Normalize position
        position[1] / 1000.0,
        np.sin(np.radians(heading)),
        np.cos(np.radians(heading)),
        next_waypoint[0] / 1000.0,
        next_waypoint[1] / 1000.0,
        np.clip(distance_to_waypoint / 100.0, 0, 1),  # Normalize distance
        np.sin(np.radians(relative_angle))
    ])
    processed['gps'] = torch.FloatTensor(gps_vector)

    # Telemetry: Speed, acceleration, steering, gear
    telemetry = raw_sensor_data.get('telemetry', {})
    speed = telemetry.get('speed', 0)  # km/h
    acceleration = telemetry.get('acceleration', 0)  # m/s^2
    steering_angle = telemetry.get('steering_angle', 0)  # degrees
    gear = telemetry.get('gear', 1)

    telemetry_vector = np.array([
        speed / 100.0,  # Normalize (max ~100 km/h)
        np.clip(acceleration / 5.0, -1, 1),  # Normalize acceleration
        steering_angle / 45.0,  # Normalize steering angle
        gear / 5.0  # Normalize gear
    ])
    processed['telemetry'] = torch.FloatTensor(telemetry_vector)

    # Camera: Simplified nearby vehicle/pedestrian info
    camera = raw_sensor_data.get('camera', {})
    vehicles = camera.get('vehicles', [])
    pedestrians = camera.get('pedestrians', [])

    # Count vehicles in front (within 30m)
    num_vehicles_front = sum(1 for v in vehicles if v.get('confidence', 0) > 0.5)
    # Average distance to vehicles
    if len(vehicles) > 0:
        vehicle_distances = [np.linalg.norm(np.array(v['position']) - position) for v in vehicles]
        avg_vehicle_distance = np.mean(vehicle_distances) if len(vehicle_distances) > 0 else 50
    else:
        avg_vehicle_distance = 50

    # Similar for pedestrians
    num_pedestrians = sum(1 for p in pedestrians if p.get('confidence', 0) > 0.5)
    if len(pedestrians) > 0:
        ped_distances = [np.linalg.norm(np.array(p['position']) - position) for p in pedestrians]
        avg_ped_distance = np.mean(ped_distances) if len(ped_distances) > 0 else 50
    else:
        avg_ped_distance = 50

    camera_vector = np.array([
        min(num_vehicles_front / 10.0, 1.0),  # Normalize count
        avg_vehicle_distance / 50.0,  # Normalize distance
        min(num_pedestrians / 5.0, 1.0),  # Normalize count
        avg_ped_distance / 50.0  # Normalize distance
    ])
    processed['camera'] = torch.FloatTensor(camera_vector)

    return processed


def postprocess_action(action: torch.Tensor) -> Dict[str, float]:
    """
    Convert network output to control commands.

    Args:
        action: Network output in [-1, 1] for each action dimension

    Returns:
        Dictionary of control commands
    """
    action = action.detach().cpu().numpy()

    # Action format: [throttle_brake, steering]
    # We'll use a single value for throttle/brake: positive = throttle, negative = brake
    throttle_brake = action[0]
    steering = action[2]

    if throttle_brake > 0:
        throttle = float(throttle_brake)
        brake = 0.0
    else:
        throttle = 0.0
        brake = float(-throttle_brake)

    control = {
        'throttle': np.clip(throttle, 0, 1),
        'brake': np.clip(brake, 0, 1),
        'steering': np.clip(steering, -1, 1),
        'gear': 1  # Always forward for now (can be made more complex)
    }

    return control
