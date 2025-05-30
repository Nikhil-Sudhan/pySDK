# Red Star UAV Aerial System SDK

A comprehensive drone control and telemetry monitoring system for PX4/ArduPilot using MAVLink protocol. Features autonomous AI-powered control, manual waypoint navigation, click-to-go interface, joystick control, and real-time telemetry monitoring with a clean terminal UI.

## Features

- **Autonomous Mode**: AI-powered drone control using OpenAI GPT integration for natural language commands
- **Manual Mode**: Waypoint-based navigation using GeoJSON files
- **Click-to-Go Mode**: Interactive point-and-click navigation
- **Joystick Control**: Direct manual control using joystick input
- **Real-time Telemetry**: Live monitoring of flight parameters
- **Terminal UI**: Clean curses-based interface for telemetry visualization

## Prerequisites

- Python 3.8+
- PX4 SITL Simulator or ArduPilot SITL
- Gazebo (for simulation)
- OpenAI API Key (for autonomous mode)
- Required Python packages (see Installation)

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd Red_Star
```

2. Install Python dependencies:
```bash
pip install pymavlink anyio openai
```

3. Set up OpenAI API Key (for autonomous mode):
Create a `.profile` file in the project root:
```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .profile
```

## Usage

The system provides multiple operation modes:

### Autonomous Mode (AI-Powered)
Control the drone using natural language commands:
```bash
python main.py -a
```
Example commands:
- "arm the drone"
- "takeoff to 10 meters"
- "move forward 5 meters"
- "land the drone"

### Manual Mode (Waypoint Navigation)
Navigate using predefined waypoints from a GeoJSON file:
```bash
python main.py -m waypoints.geojson
```

### Click-to-Go Mode
Interactive point-and-click navigation:
```bash
python main.py -c
```

### Joystick Control
Direct manual control using joystick:
```bash
python main.py -j
```

### Telemetry Monitor Only
View real-time telemetry data:
```bash
python terminal_ui.py
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

3. In another terminal, start the Red Star system:
```bash
# Choose your preferred mode
python main.py -a  # Autonomous mode
python main.py -c  # Click-to-go mode
python main.py -j  # Joystick control
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

## Project Structure

```
Red_Star/
├── main.py                 # Main entry point with argument parsing
├── terminal_ui.py          # Terminal user interface for telemetry
├── .profile               # OpenAI API key configuration
├── Commands.md            # Additional command documentation
├── src/
│   ├── main_functions.py  # Core mode implementations
│   ├── telemetary.py      # MAVLink communication and telemetry
│   ├── auto/              # Autonomous control modules
│   │   ├── openai_assistant.py  # OpenAI integration for AI commands
│   │   ├── function.py    # Core drone control functions
│   │   └── v_function.py  # Vehicle status and validation functions
│   └── manual/            # Manual control modules
│       └── manual.py      # Manual waypoint navigation
├── assets/                # Project assets
└── README.md
```

## Autonomous Mode Commands

The AI assistant can understand natural language commands for:

- **Mode Control**: "set mode to guided", "switch to auto mode"
- **Arming**: "arm the drone", "disarm the vehicle"
- **Takeoff/Landing**: "takeoff to 10 meters", "land the drone"
- **Movement**: "move forward 5 meters", "go to coordinates lat, lon"
- **Orientation**: "turn left 90 degrees", "face north"
- **Speed Control**: "set speed to 5 m/s", "slow down"

## Telemetry Monitor Features

The telemetry monitor displays:
- Flight mode and armed status
- GPS coordinates (latitude/longitude)
- Altitude and relative altitude
- Yaw angle and heading
- Ground speed and vertical speed
- Battery status and voltage
- Connection status

### Terminal UI Controls
- `q`: Quit the telemetry monitor
- Terminal resize is supported
- Real-time data updates

## API Integration

### OpenAI Assistant
The autonomous mode uses OpenAI's GPT model to translate natural language commands into drone control functions. The system includes:

- Function calling for precise drone control
- Error handling and timeout management
- Command acknowledgment tracking
- Natural language feedback

### MAVLink Protocol
All drone communication uses the MAVLink protocol supporting:
- Command acknowledgments
- Telemetry streaming
- Mission planning
- Parameter management

## Troubleshooting

### Connection Issues
1. **No data showing**:
   - Ensure Gazebo is running with PX4 SITL
   - Check if MAVLink port (14550) is available
   - Verify the drone is spawned in Gazebo

2. **Connection refused**:
   - Make sure Gazebo/SITL is running first
   - No other programs should use port 14550
   - Try restarting Gazebo and PX4 SITL

### Autonomous Mode Issues
1. **OpenAI API errors**:
   - Verify your API key in `.profile`
   - Check your OpenAI account credits
   - Ensure internet connectivity

2. **Command execution failures**:
   - Check drone mode (should be GUIDED for autonomous control)
   - Verify drone is armed when required
   - Monitor command acknowledgments in terminal output

### General Issues
- **Black screen**: Terminal window too small, resize it
- **Import errors**: Run from project root directory
- **No heartbeat**: Wait a few seconds, or restart SITL
- **Permission errors**: Check file permissions for `.profile`

## Development

### Core Components
- **main.py**: Entry point with argument parsing for different modes
- **main_functions.py**: Implementation of different operation modes
- **openai_assistant.py**: AI integration and natural language processing
- **function.py**: Low-level drone control functions
- **telemetary.py**: MAVLink communication and data processing
- **terminal_ui.py**: Real-time telemetry visualization

### Adding New Commands
To add new autonomous commands:
1. Add the function to `function.py`
2. Update the function list in `openai_assistant.py`
3. Test with natural language commands

### Extending Telemetry
To add new telemetry data:
1. Add MAVLink message handling in `telemetary.py`
2. Update the UI display in `terminal_ui.py`

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]

## Support

For issues and support, please check the troubleshooting section above or create an issue in the repository.

