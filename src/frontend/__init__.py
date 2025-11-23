"""
Frontend module for the autonomous taxi simulation.
Provides web interface with blueprint-style design.
"""

from .app import app, socketio

__all__ = ['app', 'socketio']
