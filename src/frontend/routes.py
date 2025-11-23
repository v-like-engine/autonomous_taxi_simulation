"""
API routes for the autonomous taxi simulation frontend.
"""

from flask import render_template, jsonify, request, send_file
import json
import os
from pathlib import Path

# Get base directory
BASE_DIR = Path(__file__).parent.parent.parent

def register_routes(app, sim_state):
    """Register all routes with the Flask app"""

    @app.route('/')
    def index():
        """Main application page"""
        return render_template('index.html')

    @app.route('/editor')
    def editor():
        """Map editor page"""
        return render_template('editor.html')

    @app.route('/simulation')
    def simulation():
        """Simulation view page"""
        return render_template('simulation.html')

    @app.route('/api/maps/list', methods=['GET'])
    def list_maps():
        """List all available maps"""
        maps_dir = BASE_DIR / 'data' / 'maps'
        if not maps_dir.exists():
            return jsonify({'maps': []})

        maps = []
        for map_file in maps_dir.glob('*.png'):
            # Check for corresponding JSON metadata
            json_file = map_file.with_suffix('.json')
            metadata = {}
            if json_file.exists():
                with open(json_file, 'r') as f:
                    metadata = json.load(f)

            maps.append({
                'name': map_file.stem,
                'path': str(map_file.relative_to(BASE_DIR)),
                'metadata': metadata
            })

        return jsonify({'maps': maps})

    @app.route('/api/map/load/<map_name>', methods=['GET'])
    def load_map(map_name):
        """Load a specific map with all its data"""
        maps_dir = BASE_DIR / 'data' / 'maps'

        # Load map metadata
        json_file = maps_dir / f'{map_name}.json'
        if not json_file.exists():
            return jsonify({'error': 'Map not found'}), 404

        with open(json_file, 'r') as f:
            map_data = json.load(f)

        # Add image path
        map_data['image_path'] = f'/api/map/image/{map_name}'

        return jsonify(map_data)

    @app.route('/api/map/image/<map_name>', methods=['GET'])
    def get_map_image(map_name):
        """Serve map image"""
        maps_dir = BASE_DIR / 'data' / 'maps'
        image_file = maps_dir / f'{map_name}.png'

        if not image_file.exists():
            return jsonify({'error': 'Image not found'}), 404

        return send_file(image_file, mimetype='image/png')

    @app.route('/api/map/save', methods=['POST'])
    def save_map():
        """Save edited map data"""
        data = request.get_json()
        map_name = data.get('name')

        if not map_name:
            return jsonify({'error': 'Map name required'}), 400

        maps_dir = BASE_DIR / 'data' / 'maps'
        maps_dir.mkdir(parents=True, exist_ok=True)

        json_file = maps_dir / f'{map_name}.json'

        # Remove image_path before saving
        save_data = {k: v for k, v in data.items() if k != 'image_path'}

        with open(json_file, 'w') as f:
            json.dump(save_data, f, indent=2)

        return jsonify({'success': True, 'message': 'Map saved successfully'})

    @app.route('/api/simulation/state', methods=['GET'])
    def get_simulation_state():
        """Get current simulation state"""
        return jsonify(sim_state.to_dict())

    @app.route('/api/simulation/config', methods=['POST'])
    def update_simulation_config():
        """Update simulation configuration"""
        data = request.get_json()

        if 'speed' in data:
            sim_state.speed = float(data['speed'])
        if 'traffic_density' in data:
            sim_state.traffic_density = float(data['traffic_density'])
        if 'traffic_temperature' in data:
            sim_state.traffic_temperature = float(data['traffic_temperature'])
        if 'pedestrian_density' in data:
            sim_state.pedestrian_density = float(data['pedestrian_density'])

        return jsonify(sim_state.to_dict())

    @app.route('/api/entities', methods=['GET'])
    def get_entities():
        """Get current entities in the simulation"""
        return jsonify({'entities': sim_state.entities})

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'service': 'autonomous-taxi-frontend'})
