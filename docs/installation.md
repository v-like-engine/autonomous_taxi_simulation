# Installation Guide

This guide will help you install and set up the Autonomous Taxi Simulation on your system.

## System Requirements

### Hardware Requirements
- CPU: Modern multi-core processor (Intel i5/AMD Ryzen 5 or better recommended)
- RAM: 8 GB minimum, 16 GB recommended
- GPU: Optional, but recommended for faster RL training (CUDA-compatible NVIDIA GPU)
- Storage: 2 GB free space for application and dependencies
- Display: 1920x1080 or higher resolution recommended

### Software Requirements
- Operating System: Linux, macOS, or Windows 10/11
- Python: 3.9 or higher
- pip: Latest version
- Git: For cloning the repository
- Docker (optional): For containerized deployment

## Installation Methods

### Method 1: Local Installation (Recommended for Development)

#### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd autonomous_taxi_simulation
```

#### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

#### Step 4: Verify Installation

```bash
# Test imports
python -c "import cv2, numpy, torch, flask; print('All dependencies installed successfully!')"

# Run tests
pytest tests/ -v
```

#### Step 5: Run the Application

```bash
python src/frontend/app.py
```

Open your browser and navigate to `http://localhost:5000`

### Method 2: Docker Installation (Recommended for Production)

#### Step 1: Install Docker

Follow the official Docker installation guide for your operating system:
- [Docker for Linux](https://docs.docker.com/engine/install/)
- [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

#### Step 2: Clone the Repository

```bash
git clone <repository-url>
cd autonomous_taxi_simulation
```

#### Step 3: Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

The application will be available at `http://localhost:5000`

#### Step 4: Stop the Container

```bash
# Stop the container
docker-compose down
```

### Method 3: Manual Docker Build

```bash
# Build the image
docker build -t autonomous-taxi .

# Run the container
docker run -p 5000:5000 \
  -v $(pwd)/maps:/app/maps \
  -v $(pwd)/models:/app/models \
  autonomous-taxi
```

## Post-Installation Setup

### Creating Required Directories

The application will automatically create these directories if they don't exist:
- `maps/` - Store your map images here
- `models/` - Trained RL models will be saved here
- `logs/` - Application logs
- `data/` - Temporary data and cache

### Testing the Installation

Run the test suite to ensure everything is working:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html
```

### GPU Support (Optional)

If you have an NVIDIA GPU and want to use it for RL training:

#### CUDA Setup

1. Install NVIDIA drivers
2. Install CUDA Toolkit (version compatible with PyTorch)
3. Verify GPU is available:

```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

#### For Docker with GPU

Use the `nvidia-docker` runtime:

```bash
docker run --gpus all -p 5000:5000 autonomous-taxi
```

## Troubleshooting

### Common Issues

#### Issue: OpenCV fails to import

**Solution:**
```bash
# Uninstall conflicting packages
pip uninstall opencv-python opencv-contrib-python opencv-python-headless

# Reinstall OpenCV
pip install opencv-python==4.5.0
```

#### Issue: PyTorch installation fails

**Solution:**
```bash
# Install PyTorch separately with appropriate CUDA version
# CPU only:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# CUDA 11.8:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### Issue: Flask application won't start

**Solution:**
```bash
# Check if port 5000 is already in use
# On Linux/macOS:
lsof -i :5000

# On Windows:
netstat -ano | findstr :5000

# Kill the process or use a different port:
export FLASK_PORT=5001
python src/frontend/app.py
```

#### Issue: Permission denied errors

**Solution:**
```bash
# Ensure you have write permissions for the project directory
chmod -R u+w .

# Or run with appropriate permissions
```

#### Issue: Docker build fails

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Performance Issues

If the application is running slowly:

1. **Reduce traffic density**: Lower the number of vehicles/pedestrians
2. **Disable sensor visualization**: Turn off visual overlays
3. **Use GPU**: Enable GPU acceleration for RL training
4. **Lower resolution**: Use smaller map images
5. **Close other applications**: Free up system resources

### Getting Help

If you encounter issues not covered here:

1. Check the [documentation](../README.md)
2. Review the [API documentation](api.md)
3. Check existing issues on GitHub
4. Open a new issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce the problem

## Updating the Application

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run migrations if any
python scripts/migrate.py  # (if applicable)
```

For Docker:

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose up --build
```

## Uninstallation

### Local Installation

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv

# Remove application directory
cd ..
rm -rf autonomous_taxi_simulation
```

### Docker Installation

```bash
# Stop and remove containers
docker-compose down

# Remove image
docker rmi autonomous-taxi

# Remove application directory
cd ..
rm -rf autonomous_taxi_simulation
```

## Next Steps

After successful installation:

1. Read the [Usage Guide](usage.md) to learn how to use the application
2. Review the [Architecture Documentation](architecture.md) to understand the system
3. Check the [API Documentation](api.md) for integration details
4. Start with a simple map to test the system

---

**Installation Complete!** You're ready to start using the Autonomous Taxi Simulation.
