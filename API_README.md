# UAV Aerial System FastAPI

This FastAPI provides REST endpoints to control your UAV system through HTTP requests instead of command line arguments.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the API server:
```bash
python3 api.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Execute Command
**POST** `/execute-command`

Execute natural language commands for the drone.

**Request:**
```json
{
  "command": "Take off to 10 meters altitude"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command executed successfully",
  "result": [["takeoff", 0]]
}
```

### 2. Manual Mode
**POST** `/manual-mode`

Start manual mode with GeoJSON waypoints.

**Request:**
```json
{
  "geojson_file": "assets/test.geojson"
}
```

### 3. Click-to-Go Mode
**POST** `/click-to-go`

Start click-to-go mode.

**Request:**
```json
{}
```

### 4. Joystick Control
**POST** `/joystick`

Start joystick control mode.

**Request:**
```json
{}
```

### 5. Health Check
**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "UAV Aerial System API"
}
```

## Usage Examples

### Using curl:
```bash
# Execute a command
curl -X POST "http://localhost:8000/execute-command" \
     -H "Content-Type: application/json" \
     -d '{"command": "Take off to 10 meters"}'

# Start manual mode
curl -X POST "http://localhost:8000/manual-mode" \
     -H "Content-Type: application/json" \
     -d '{"geojson_file": "assets/test.geojson"}'
```

### Using Python:
```python
import requests

# Execute command
response = requests.post("http://localhost:8000/execute-command", 
                        json={"command": "Take off to 10 meters"})
print(response.json())
```

### Using the example client:
```bash
python3 api_client_example.py
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These provide interactive documentation for all endpoints. 