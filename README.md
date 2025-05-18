# UAV Aerial System SDK for Gazebo

This SDK provides an interface for controlling UAVs in the Gazebo simulation environment using MAVLink.

## Features

- **Manual Mode**: Navigate the drone through predefined waypoints loaded from a GeoJSON file
- **Autonomous Mode**: (In development) 
- **Click-to-Go Mode**: (In development) 
- **Joystick Control**: (In development)

## Prerequisites

- Python 3.6+
- Gazebo with SITL (Software In The Loop) running
- MAVLink compatible drone model in Gazebo (ArduPilot or PX4)

## Installation

```bash
pip install pymavlink
```

## Usage

### Manual Mode

In manual mode, the drone will follow waypoints defined in a GeoJSON file.

```bash
python3 main.py -m path/to/waypoints.geojson
```

The GeoJSON file should contain a FeatureCollection with LineString features. Each point in the LineString represents a waypoint with longitude, latitude, and altitude.

Example GeoJSON format:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {},
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [longitude1, latitude1, altitude1],
          [longitude2, latitude2, altitude2],
          ...
        ]
      }
    }
  ]
}
```

### Other Modes

```bash
# Autonomous mode (in development)
python3 main.py -a

# Click-to-go mode (in development)
python3 main.py -c

# Joystick control (in development)
python3 main.py -j
```

## Helper Scripts

The SDK includes two helpful scripts for setting up and troubleshooting Gazebo simulations:

### Setup Script

To quickly set up a Gazebo simulation environment with ArduPilot SITL:

```bash
./setup_gazebo.sh
```

This script:
- Checks for required dependencies
- Starts ArduPilot SITL with appropriate parameters
- Launches Gazebo with a compatible drone model

### Arming Troubleshooter

If you're experiencing issues with arming the drone in simulation, use:

```bash
./fix_arm_issues.py --fix
```

This script:
- Diagnoses common arming issues
- Sets optimal parameters for simulation
- Tests arming to ensure it works properly

## Connection Settings

The SDK currently connects to a local MAVLink instance at `udp:127.0.0.1:14550`. To use a different connection:

1. Modify the `check_connection()` function in `functions.py`
2. Change the connection string to your desired endpoint

## Simulation-Specific Features

### Enhanced Arming Process

When running in Gazebo simulation, the SDK includes:

- Automatic disabling of arming checks that may prevent arming in simulation
- Multiple arming attempts with proper error handling
- Proper mode transition verification
- Monitoring of drone armed state via MAVLink heartbeat messages

### Improved Mission Handling

- Uses MISSION_ITEM_INT messages instead of MISSION_ITEM for improved precision and compatibility
- Integer-based coordinates (multiplied by 1e7) for accurate waypoint positioning
- Detailed error reporting for mission upload failures
- Properly configured waypoint formats for ArduPilot/PX4 compatibility

### Troubleshooting Gazebo Simulation

If you encounter issues with the drone in simulation:

1. **Connection Problems**: Ensure the SITL instance is running and configured to output MAVLink on UDP port 14550

2. **Arming Issues**: 
   - Check if GPS is available in the simulation
   - The SDK automatically disables arming checks (ARMING_CHECK=0)
   - If still experiencing issues, try setting additional parameters like:
     - `EK3_ENABLE=0` to disable EKF3
     - `AHRS_EKF_TYPE=0` to use DCM instead of EKF

3. **Mission Upload Failures**:
   - Ensure waypoint coordinates are valid (reasonable latitude/longitude values)
   - If you see "GCS should send MISSION_ITEM_INT" error, this has been fixed in the current version
   - Mission upload failures may indicate that your simulation requires specific waypoint types

## License

[MIT](LICENSE) 


first you want to run the simulation(gazebo)

cd ardupilot_gazebo
gz sim -v4 -r iris_runway.sdf


then you want to run the ardupilot firmware

cd ardupilot
./Tools/autotest/sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --console --map


then you want to run the python script

