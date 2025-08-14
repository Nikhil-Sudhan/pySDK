import asyncio
import json
import time
import math
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import existing telemetry system
from src.telemetary import get_live_telemetry

app = FastAPI(title="Drone Position Delta WebSocket Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")
        
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
            
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                print(f"Error sending to client: {e}")
                disconnected.add(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

class DronePositionTracker:
    def __init__(self):
        self.previous_position = None
        self.last_update_time = 0
        
    def calculate_delta(self, current_position):
        """Calculate position delta from previous position"""
        if self.previous_position is None:
            # First measurement - no delta to calculate
            delta = {"lat": 0.0, "lon": 0.0, "alt": 0.0}
        else:
            # Calculate differences
            delta = {
                "lat": round(current_position["lat"] - self.previous_position["lat"], 8),
                "lon": round(current_position["long"] - self.previous_position["long"], 8),  # Note: using 'long' from telemetry
                "alt": round(current_position["alt"] - self.previous_position["alt"], 3)
            }
        
        # Update previous position
        self.previous_position = {
            "lat": current_position["lat"],
            "long": current_position["long"],
            "alt": current_position["alt"]
        }
        
        return delta

# Global tracker instance
position_tracker = DronePositionTracker()

async def drone_position_broadcaster():
    """Background task that continuously broadcasts drone position deltas"""
    print("Starting drone position broadcaster...")
    
    while True:
        try:
            # Get current telemetry data
            telemetry_data = get_live_telemetry()
            
            # Check if we have valid position data
            if (telemetry_data.get("lat", 0) != 0 or 
                telemetry_data.get("long", 0) != 0 or 
                telemetry_data.get("alt", 0) != 0):
                
                # Calculate position delta
                delta = position_tracker.calculate_delta(telemetry_data)
                
                # Prepare message for WebSocket clients
                message = {
                    "timestamp": time.time(),
                    "lat": delta["lat"],
                    "lon": delta["lon"],  # Convert 'long' to 'lon' for client
                    "alt": delta["alt"],
                    "drone_status": {
                        "mode": telemetry_data.get("mode", "UNKNOWN"),
                        "armed": telemetry_data.get("armed", False),
                        "current_position": {
                            "lat": telemetry_data.get("lat", 0),
                            "lon": telemetry_data.get("long", 0),
                            "alt": telemetry_data.get("alt", 0)
                        }
                    }
                }
                
                # Broadcast to all connected clients
                await manager.broadcast(message)
                
            else:
                # Send status message when no position data is available
                status_message = {
                    "timestamp": time.time(),
                    "lat": 0.0,
                    "lon": 0.0,
                    "alt": 0.0,
                    "status": "No position data available",
                    "drone_status": {
                        "mode": telemetry_data.get("mode", "UNKNOWN"),
                        "armed": telemetry_data.get("armed", False)
                    }
                }
                await manager.broadcast(status_message)
                
        except Exception as e:
            print(f"Error in position broadcaster: {e}")
            # Send error message to clients
            error_message = {
                "timestamp": time.time(),
                "lat": 0.0,
                "lon": 0.0,
                "alt": 0.0,
                "error": f"Telemetry error: {str(e)}"
            }
            await manager.broadcast(error_message)
        
        # Wait for 0.5 seconds before next update
        await asyncio.sleep(0.5)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep connection alive and handle any incoming messages
        while True:
            # Wait for any message from client (ping/pong, etc.)
            try:
                data = await websocket.receive_text()
                # Echo back received message for connection testing
                response = {
                    "type": "echo",
                    "message": f"Server received: {data}",
                    "timestamp": time.time()
                }
                await websocket.send_text(json.dumps(response))
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Error handling WebSocket message: {e}")
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {
        "message": "Drone Position Delta WebSocket Server",
        "websocket_endpoint": "ws://localhost:8000/ws",
        "active_connections": len(manager.active_connections),
        "description": "Connect to /ws to receive real-time drone position delta data"
    }

@app.get("/status")
async def get_status():
    """Get current server and drone status"""
    telemetry_data = get_live_telemetry()
    return {
        "server_status": "running",
        "active_connections": len(manager.active_connections),
        "drone_telemetry": telemetry_data,
        "websocket_url": "ws://localhost:8000/ws"
    }

# Startup event to begin broadcasting
@app.on_event("startup")
async def startup_event():
    # Start the background broadcaster task
    asyncio.create_task(drone_position_broadcaster())
    print("WebSocket server started - Broadcasting drone position deltas every 0.5 seconds")
    print("Connect to: ws://localhost:8000/ws")

if __name__ == "__main__":
    print("Starting Drone Position Delta WebSocket Server...")
    print("WebSocket endpoint: ws://localhost:8000/ws")
    print("Broadcasting position deltas every 0.5 seconds")
    
    # Start the continuous telemetry system
    from src.telemetary import start_continuous_telemetry
    start_continuous_telemetry()
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 