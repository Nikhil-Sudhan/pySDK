# Red Star Autonomy Telemetry Monitor

A real-time telemetry monitoring system for drones using MAVLink protocol, with a clean curses-based terminal user interface.

## Prerequisites

- Python 3.8+
- PX4 SITL Simulator
- Gazebo
- MAVLink (pymavlink)
- Curses (usually comes with Python)

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Red_Star
```

2. Install Python dependencies:
```bash
pip install pymavlink anyio
```

## Running the Simulation

1. First, start PX4 SITL with Gazebo:
```bash
cd PX4-Autopilot
make px4_sitl gazebo
```

2. In a new terminal, start QGroundControl (optional but recommended):
```bash
./QGroundControl.AppImage
```

3. In another terminal, start the telemetry monitor:
```bash
# Run the terminal UI (recommended)
python terminal_ui.py

# Or run the basic telemetry monitor
python src/telemetary.py
```

## Gazebo Commands

### Basic Commands
- Start Gazebo with PX4 SITL:
```bash
make px4_sitl gazebo
```

- Start with a specific world:
```bash
make px4_sitl gazebo_iris__<world>
# Example: make px4_sitl gazebo_iris__empty
```

### Vehicle Control in Gazebo
- Takeoff command:
```bash
commander takeoff
```

- Land command:
```bash
commander land
```

- Arm the vehicle:
```bash
commander arm
```

- Disarm the vehicle:
```bash
commander disarm
```

### Common Worlds Available
- Empty world: `make px4_sitl gazebo_iris__empty`
- Baylands: `make px4_sitl gazebo_iris__baylands`
- Warehouse: `make px4_sitl gazebo_iris__warehouse`
- KSQL Airport: `make px4_sitl gazebo_iris__ksql_airport`

## Telemetry Monitor Features

The telemetry monitor displays:
- Flight mode and armed status
- Latitude and longitude
- Yaw angle
- Ground speed
- Vertical speed

### Controls
- `q`: Quit the telemetry monitor
- Terminal resize is supported

## Project Structure

```
Red_Star/
├── src/
│   ├── __init__.py
│   └── telemetary.py    # MAVLink communication
├── terminal_ui.py       # Terminal user interface
└── README.md
```

## Troubleshooting

1. If no data is showing:
   - Ensure Gazebo is running with PX4 SITL
   - Check if MAVLink port (14550) is not blocked
   - Verify the drone is spawned in Gazebo

2. If connection fails:
   - Ensure no other programs are using port 14550
   - Try restarting Gazebo and PX4 SITL

3. Common issues:
   - "Connection refused": Make sure Gazebo/SITL is running
   - "No heartbeat": Wait a few seconds, or restart SITL
   - Black screen: Terminal window too small, resize it
   - Import error: Make sure you're running from the project root directory

## Development

The project consists of two main components:
- `telemetary.py`: Handles MAVLink communication
- `terminal_ui.py`: Provides the terminal UI

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

