from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn
import json
import os

# Import the OpenAI assistant
from src.auto.openai_assistant import get_and_execute_drone_commands

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
    """Process command through OpenAI and execute on drone in Gazebo"""
    print(f"Received command: {request.command}")
    
    try:
        # Send command to OpenAI assistant for processing and execution
        success, function_list = get_and_execute_drone_commands(request.command)
        
        if success:
            return {
                "message": f"Command executed successfully: {request.command}",
                "status": "success",
                "executed_functions": function_list
            }
        else:
            return {
                "message": f"Command failed: {request.command}",
                "status": "failed",
                "executed_functions": function_list if 'function_list' in locals() else []
            }
            
    except Exception as e:
        print(f"Error processing command: {str(e)}")
        return {
            "message": f"Error processing command: {request.command}",
            "status": "error",
            "error": str(e)
        }

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
    uvicorn.run(app, host="0.0.0.0", port=8001) 