# Drone Position Delta WebSocket Server

A FastAPI-based WebSocket server that continuously streams drone position delta data to connected clients at 0.5-second intervals.

## Features

- **Real-time Position Deltas**: Calculates and broadcasts position changes (lat, lon, alt) every 0.5 seconds
- **Multiple Client Support**: Handles multiple WebSocket connections simultaneously using asyncio
- **Integration with Existing Telemetry**: Uses your existing MAVLink telemetry system
- **CORS Enabled**: Allows connections from localhost frontend applications
- **Error Handling**: Graceful handling of connection errors and telemetry failures
- **Status Monitoring**: Provides drone status information alongside position data

## Prerequisites

1. **Gazebo Simulation**: Must be running with PX4 SITL
2. **MAVLink Connection**: Drone must be connected via UDP on port 14550
3. **Dependencies**: Install required packages

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Start Gazebo and PX4 SITL

```bash
# In PX4 directory
make px4_sitl gazebo
```

### 2. Start the WebSocket Server

```bash
python websocket_server.py
```

The server will:
- Start on `localhost:8000`
- Begin broadcasting position deltas at `/ws`
- Automatically initialize the telemetry system

### 3. Connect a Client

Open `websocket_test_client.html` in your browser or connect programmatically:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Position Delta:', data.lat, data.lon, data.alt);
};
```

## Message Format

The server sends JSON messages in this format:

```json
{
  "timestamp": 1703123456.789,
  "lat": 0.00000125,
  "lon": 0.00000087,
  "alt": 0.05,
  "drone_status": {
    "mode": "OFFBOARD",
    "armed": true,
    "current_position": {
      "lat": 47.3977419,
      "lon": 8.5455938,
      "alt": 10.5
    }
  }
}
```

### Fields Explanation

- `lat`: Latitude delta (change since last measurement)
- `lon`: Longitude delta (change since last measurement)  
- `alt`: Altitude delta in meters (change since last measurement)
- `timestamp`: Unix timestamp of the measurement
- `drone_status`: Current drone state and absolute position

## API Endpoints

### WebSocket
- `ws://localhost:8000/ws` - Main WebSocket endpoint for position deltas

### HTTP Endpoints
- `GET /` - Server information and status
- `GET /status` - Current server and drone status

## Integration Notes

### Coordinate System
- The system uses the coordinates directly from your MAVLink telemetry
- Coordinates are already in latitude/longitude format from the GPS
- No conversion needed as the telemetry system handles GPS data

### Delta Calculation
- Position deltas are calculated as: `current_position - previous_position`
- First measurement always returns `{lat: 0, lon: 0, alt: 0}` (no previous reference)
- Precision: 8 decimal places for lat/lon, 3 for altitude

### Connection Management
- Automatically handles client connections and disconnections
- Broadcasts to all connected clients simultaneously
- Removes failed connections automatically

## Testing

### Using the Test Client
1. Open `websocket_test_client.html` in a web browser
2. Click "Connect" to establish WebSocket connection
3. Monitor real-time position deltas and drone status
4. Use "Send Test Message" to test bidirectional communication

### Command Line Testing
```bash
# Install wscat for testing
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws
```

## Troubleshooting

### No Position Data
- Ensure Gazebo is running with PX4 SITL
- Check MAVLink connection on UDP port 14550
- Verify drone is armed and has GPS lock

### Connection Issues
- Check if port 8000 is available
- Ensure CORS is not blocked by browser
- Verify WebSocket URL is correct

### Telemetry Errors
- Check console output for error messages
- Ensure `src/continuous_telemetry.py` is accessible
- Verify MAVLink messages are being received

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gazebo/PX4    │────│  MAVLink/UDP     │────│  Telemetry      │
│   Simulation    │    │  Port 14550      │    │  System         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         │
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  WebSocket      │────│  FastAPI         │────│  Position       │
│  Clients        │    │  Server          │    │  Tracker        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

The system integrates seamlessly with your existing drone control infrastructure while providing real-time position delta streaming to web clients. 