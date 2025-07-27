from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import json
import os

app = FastAPI(title="UAV Command API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class CommandRequest(BaseModel):
    command: str

class Waypoint(BaseModel):
    lat: float
    lon: float
    alt: float

class Mission(BaseModel):
    waypoints_name: str
    waypoints: List[Waypoint]

@app.get("/")
async def root():
    return {"message": "UAV Command API is running"}

@app.post("/execute-command")
async def execute_command(request: CommandRequest):
    """Print the received command"""
    print(f"Received command: {request.command}")
    return {"message": f"Command received: {request.command}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/waypoints")
def save_mission(mission: Mission):
    """Save mission waypoints to JSON file"""
    # Create missions directory if it doesn't exist
    os.makedirs("missions", exist_ok=True)
    
    with open(f"missions/{mission.waypoints_name}.json", "w") as f:
        json.dump(mission.dict(), f, indent=4)
    
    print(f"Mission saved: {mission.waypoints_name}")
    return {"status": "saved", "mission": mission.waypoints_name}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 