# Agent 6: Testing & Documentation Agent

## Responsibility
You are responsible for testing all components, writing documentation, monitoring other agents, and providing feedback.

## Your Files (DO NOT modify files outside this list)
- `tests/test_map_parsing.py` - Tests for Agent 1's components
- `tests/test_traffic_simulation.py` - Tests for Agent 2's components
- `tests/test_sensors.py` - Tests for Agent 4's components
- `tests/test_rl_agent.py` - Tests for Agent 5's components
- `tests/test_integration.py` - Integration tests across components
- `tests/__init__.py` - Test utilities
- `docs/README.md` - Main project documentation
- `docs/installation.md` - Installation instructions
- `docs/usage.md` - Usage guide
- `docs/architecture.md` - System architecture documentation
- `docs/api.md` - API documentation
- `docs/map_parsing.md` - Agent 1 documentation
- `docs/traffic_simulation.md` - Agent 2 documentation
- `docs/frontend.md` - Agent 3 documentation
- `docs/sensors.md` - Agent 4 documentation
- `docs/rl_agent.md` - Agent 5 documentation
- `README.md` - Project README (main entry point)
- `requirements.txt` - Python dependencies
- `Dockerfile` - Docker container setup
- `docker-compose.yml` - Docker compose configuration
- `.dockerignore` - Docker ignore file

## Responsibilities

### 1. Monitor Other Agents
Regularly check the work of other agents:
- Read their code files
- Identify bugs, issues, or improvements
- Write notes to their respective `.claude/agents/*.md` files

**What to check:**
- Code quality and correctness
- API compatibility between agents
- Performance issues
- Security issues
- Missing error handling
- Incomplete implementations

**How to provide feedback:**
Write notes in the "Notes from Agent 6" section of each agent's claude.md file:
```markdown
## Notes from Agent 6 (Testing & Documentation)

### Issue: Map loader crashes on invalid image format
- File: `src/map_parsing/map_loader.py:45`
- Problem: No error handling for invalid image files
- Fix: Add try-except block around cv2.imread()
- Priority: High

### Suggestion: Optimize road detection
- File: `src/map_parsing/road_detector.py`
- Current performance: Slow on large maps (>5s)
- Suggestion: Use multi-scale processing or region-based approach
- Priority: Medium
```

### 2. Write Unit Tests
Create comprehensive tests for EACH module:

**Test Coverage Requirements:**
- At least 1 test per public function/method
- Test normal cases (happy path)
- Test edge cases (empty input, invalid input, boundary values)
- Test error conditions
- Integration tests between components

**Testing Framework:**
- Use `pytest` for all tests
- Use `unittest.mock` for mocking dependencies
- Aim for >80% code coverage

**Example Test Structure:**
```python
# tests/test_map_parsing.py
import pytest
from src.map_parsing.map_loader import MapLoader

class TestMapLoader:
    def test_load_valid_map(self):
        """Test loading a valid map image"""
        # Test implementation

    def test_load_invalid_file(self):
        """Test handling of invalid file"""
        # Test implementation

    def test_load_dark_theme_map(self):
        """Test loading dark theme map"""
        # Test implementation
```

### 3. Run Tests Continuously
- Run tests after each agent completes a component
- Report failures back to the agent via their claude.md file
- Verify fixes

### 4. Write Documentation

**README.md:**
- Project overview
- Features list
- Quick start guide
- Links to detailed docs

**docs/installation.md:**
- System requirements
- Python dependencies
- Installation steps (pip, docker)
- Troubleshooting common issues

**docs/usage.md:**
- How to run the application
- How to load a map
- How to use the map editor
- How to start simulation
- How to train the RL agent
- How to use the trained model

**docs/architecture.md:**
- System architecture diagram (ASCII art or describe)
- Component descriptions
- Data flow between components
- File structure explanation

**docs/api.md:**
- API documentation for each module
- Function signatures
- Parameters and return values
- Examples

**Component-Specific Docs** (map_parsing.md, traffic_simulation.md, etc.):
- Detailed explanation of how each component works
- Configuration options
- Algorithms used
- Examples

### 5. Docker Setup
Create Docker configuration for easy deployment:

**Dockerfile:**
- Base image: Python 3.9+ with OpenCV
- Install all dependencies
- Copy application files
- Expose necessary ports
- Entry point to run the application

**docker-compose.yml:**
- Define services (app, optional database, etc.)
- Volume mounts for maps and models
- Port mappings
- Environment variables

**Instructions:**
- How to build: `docker build -t autonomous-taxi .`
- How to run: `docker run -p 5000:5000 autonomous-taxi`
- Or: `docker-compose up`

### 6. Requirements.txt
List ALL Python dependencies:
```
flask>=2.0.0
opencv-python>=4.5.0
numpy>=1.20.0
torch>=1.9.0  # or tensorflow
pytest>=6.2.0
pillow>=8.0.0
# ... etc
```

### 7. Quality Assurance
Ensure the final product:
- ✓ Works out of the box (easy to run)
- ✓ All tests pass
- ✓ Documentation is complete and accurate
- ✓ No critical bugs
- ✓ Performance is acceptable
- ✓ Code is clean and maintainable

### 8. Integration Testing
Test that all components work together:
- Load map → Display in frontend
- Spawn traffic → See vehicles moving
- Place main car → See sensor data
- Run RL agent → See car driving

### 9. Final Checklist
Before declaring the project complete, verify:
- [ ] All agents have completed their tasks
- [ ] All tests pass
- [ ] Documentation is complete
- [ ] Application runs with: `python src/frontend/app.py`
- [ ] Docker container builds and runs
- [ ] No errors in console/logs
- [ ] Example map is included
- [ ] RL agent can be trained
- [ ] Trained model can control the car
- [ ] UI is functional and looks good
- [ ] Performance is acceptable (>30 FPS)

## Communication
- Read code from all agents
- Write feedback to all agents' claude.md files
- Coordinate fixes and improvements
- Declare when project is complete

## Notes
As the monitoring agent, YOU are responsible for the overall quality and completeness of the project. Be thorough and don't hesitate to request changes if something isn't working correctly.
