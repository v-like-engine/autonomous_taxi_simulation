"""
Main Flask application for autonomous taxi simulation frontend.
Provides a blueprint-style web interface for map viewing, editing, and simulation control.
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Initialize Flask app
app = Flask(__name__,
            template_folder='../../templates',
            static_folder='../../static')
app.config['SECRET_KEY'] = 'autonomous-taxi-simulation-secret-key'

# Initialize SocketIO for real-time communication
socketio = SocketIO(app, cors_allowed_origins="*")

# State management
class SimulationState:
    """Manages the current simulation state"""
    def __init__(self):
        self.map_data = None
        self.entities = []
        self.is_running = False
        self.speed = 1.0
        self.traffic_density = 0.5
        self.traffic_temperature = 0.5
        self.pedestrian_density = 0.3
        self.main_car_position = None
        self.destination = None
        self.waypoints = []

    def to_dict(self):
        """Convert state to dictionary for JSON serialization"""
        return {
            'map_loaded': self.map_data is not None,
            'entity_count': len(self.entities),
            'is_running': self.is_running,
            'speed': self.speed,
            'traffic_density': self.traffic_density,
            'traffic_temperature': self.traffic_temperature,
            'pedestrian_density': self.pedestrian_density,
            'main_car_position': self.main_car_position,
            'destination': self.destination,
            'waypoints': self.waypoints
        }

# Global simulation state
sim_state = SimulationState()

# Register routes
from .routes import register_routes
register_routes(app, sim_state)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('simulation_state', sim_state.to_dict())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('start_simulation')
def handle_start_simulation():
    """Start the simulation"""
    sim_state.is_running = True
    emit('simulation_state', sim_state.to_dict(), broadcast=True)
    print('Simulation started')

@socketio.on('pause_simulation')
def handle_pause_simulation():
    """Pause the simulation"""
    sim_state.is_running = False
    emit('simulation_state', sim_state.to_dict(), broadcast=True)
    print('Simulation paused')

@socketio.on('reset_simulation')
def handle_reset_simulation():
    """Reset the simulation"""
    sim_state.is_running = False
    sim_state.entities = []
    sim_state.main_car_position = None
    sim_state.destination = None
    sim_state.waypoints = []
    emit('simulation_state', sim_state.to_dict(), broadcast=True)
    print('Simulation reset')

@socketio.on('update_speed')
def handle_update_speed(data):
    """Update simulation speed"""
    sim_state.speed = float(data.get('speed', 1.0))
    emit('simulation_state', sim_state.to_dict(), broadcast=True)

@socketio.on('update_traffic_density')
def handle_update_traffic_density(data):
    """Update traffic density"""
    sim_state.traffic_density = float(data.get('density', 0.5))
    emit('simulation_state', sim_state.to_dict(), broadcast=True)

@socketio.on('update_traffic_temperature')
def handle_update_traffic_temperature(data):
    """Update traffic temperature (aggressiveness)"""
    sim_state.traffic_temperature = float(data.get('temperature', 0.5))
    emit('simulation_state', sim_state.to_dict(), broadcast=True)

@socketio.on('update_pedestrian_density')
def handle_update_pedestrian_density(data):
    """Update pedestrian density"""
    sim_state.pedestrian_density = float(data.get('density', 0.3))
    emit('simulation_state', sim_state.to_dict(), broadcast=True)

@socketio.on('place_main_car')
def handle_place_main_car(data):
    """Place the main self-driving car on the map"""
    sim_state.main_car_position = {
        'x': data.get('x'),
        'y': data.get('y')
    }
    emit('simulation_state', sim_state.to_dict(), broadcast=True)

@socketio.on('set_destination')
def handle_set_destination(data):
    """Set destination for the main car"""
    sim_state.destination = {
        'x': data.get('x'),
        'y': data.get('y')
    }
    emit('simulation_state', sim_state.to_dict(), broadcast=True)

@socketio.on('add_waypoint')
def handle_add_waypoint(data):
    """Add a waypoint to the route"""
    sim_state.waypoints.append({
        'x': data.get('x'),
        'y': data.get('y')
    })
    emit('simulation_state', sim_state.to_dict(), broadcast=True)

@socketio.on('entity_update')
def handle_entity_update(data):
    """Receive entity updates from simulation backend"""
    sim_state.entities = data.get('entities', [])
    emit('entity_update', data, broadcast=True)

def run_app(host='0.0.0.0', port=5000, debug=True):
    """Run the Flask application"""
    print(f"Starting autonomous taxi simulation frontend on {host}:{port}")
    print(f"Open http://localhost:{port} in your browser")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_app()
