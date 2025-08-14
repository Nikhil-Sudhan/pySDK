from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
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
    waypoint_file: str = None  # Optional waypoint file for cross coverage

class Waypoint(BaseModel):
    lat: float
    lon: float
    alt: float

class Mission(BaseModel):
    waypoints_name: str
    waypoints: List[Waypoint]

class CommandWithWaypointsRequest(BaseModel):
    command: str
    waypoints: List[Dict[str, Any]]

class CrossCoverageRequest(BaseModel):
    json_file: str
    altitude: float = 50
    line_spacing_in_meter: float = 20
    smooth_path_edges: bool = True
    smooth_path_edge_intensity: int = 50

@app.get("/")
async def root():
    return {"message": "UAV Command API is running"}

@app.post("/execute-command")
async def execute_command(request: CommandRequest):
    """Process command through OpenAI and execute on drone in Gazebo"""
    print(f"Received command: {request.command}")
    print(f"Waypoint file: {request.waypoint_file}")
    
    try:
        # Check if waypoint file is provided for cross coverage
        if request.waypoint_file and ("cross coverage" in request.command.lower() or "cross coverage path" in request.command.lower()):
            print("Generating cross coverage path from waypoint file")
            
            # Extract parameters from command if specified
            altitude = 50
            line_spacing = 20
            smooth_edges = True
            smooth_intensity = 50
            
            # Parse command for parameters
            if "altitude" in request.command.lower():
                import re
                alt_match = re.search(r'(\d+)\s*(?:meter|m)\s*altitude', request.command.lower())
                if alt_match:
                    altitude = float(alt_match.group(1))
            
            if "line spacing" in request.command.lower() or "spacing" in request.command.lower():
                import re
                spacing_match = re.search(r'(\d+)\s*(?:meter|m)\s*(?:line\s*)?spacing', request.command.lower())
                if spacing_match:
                    line_spacing = float(spacing_match.group(1))
            
            # Generate cross coverage path
            from src.auto.cpp_function import generate_cross_coverage_path
            
            result = generate_cross_coverage_path(
                waypoints_data=request.waypoint_file,
                altitude=altitude,
                line_spacing_in_meter=line_spacing,
                smooth_path_edges=smooth_edges,
                smooth_path_edge_intensity=smooth_intensity
            )
            
            if result:
                return {
                    "message": f"Cross coverage path generated successfully from {request.waypoint_file}",
                    "status": "success",
                    "command": request.command,
                    "cross_coverage_path": result,
                    "parameters": {
                        "altitude": altitude,
                        "line_spacing": line_spacing,
                        "smooth_edges": smooth_edges,
                        "smooth_intensity": smooth_intensity
                    }
                }
            else:
                return {
                    "message": f"Failed to generate cross coverage path from {request.waypoint_file}",
                    "status": "failed",
                    "command": request.command,
                    "error": "Function returned None"
                }
        
        # Regular command execution (no waypoint file or not cross coverage)
        else:
            print("Executing regular command")
            # Send command to OpenAI assistant for processing and execution
            success, function_list, waypoint_data = get_and_execute_drone_commands(request.command)
            
            if success:
                response_data = {
                    "message": f"Command executed successfully: {request.command}",
                    "status": "success",
                    "executed_functions": function_list
                }
                
                # Add waypoint data if generated
                if waypoint_data:
                    response_data["waypoint_data"] = waypoint_data
                    response_data["message"] += " - Waypoint data generated for frontend visualization"
                
                return response_data
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

@app.post("/execute-command-with-waypoints")
async def execute_command_with_waypoints(request: CommandWithWaypointsRequest):
    """Process command with waypoint data for cross coverage path generation"""
    print(f"Received command: {request.command}")
    print(f"Received waypoints: {request.waypoints}")
    
    try:
        # Send command to OpenAI assistant for processing and execution
        # The OpenAI assistant will detect cross coverage commands and call the generate_cross_coverage_path function
        success, function_list, waypoint_data = get_and_execute_drone_commands(request.command, request.waypoints)
        
        if success:
            # Check if cross coverage path was generated
            cross_coverage_result = None
            for func_name, result in function_list:
                if func_name == "generate_cross_coverage_path" and result is not None and result != -1:
                    cross_coverage_result = result
                    break
            
            response_data = {
                "message": f"Command processed successfully: {request.command}",
                "status": "success",
                "command": request.command,
                "waypoints": request.waypoints,
                "executed_functions": function_list
            }
            
            # Add cross coverage path data if generated
            if cross_coverage_result:
                response_data["cross_coverage_path"] = cross_coverage_result
            
            # Add waypoint data if generated
            if waypoint_data:
                response_data["waypoint_data"] = waypoint_data
                response_data["message"] += " - Waypoint data generated for frontend visualization"
            
            return response_data
        else:
            return {
                "message": f"Command failed: {request.command}",
                "status": "failed",
                "command": request.command,
                "waypoints": request.waypoints,
                "executed_functions": function_list if 'function_list' in locals() else []
            }
            
    except Exception as e:
        print(f"Error processing command with waypoints: {str(e)}")
        return {
            "message": f"Error processing command with waypoints",
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
    uvicorn.run(app, host="0.0.0.0", port=8000) 