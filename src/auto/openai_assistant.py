import openai
import json
import os
import time
from pymavlink import mavutil

from .function import (
    check_heartbeat,
    set_mode,
    arm_disarm,
    takeoff,
    condition_yaw,
    change_speed,
    move_local_ned,
    move_global_int,
    generate_waypoint_json,
    generate_dynamic_waypoints_from_command
)
from .cpp_function import generate_cross_coverage_path

def read_api_key():
    with open('.profile', 'r') as f:
        content = f.read().strip()
        if content.startswith('OPENAI_API_KEY='):
            return content.split('=')[1].strip()
        raise ValueError("Invalid .profile format. Expected 'OPENAI_API_KEY=<key>'")


api_key = read_api_key()
client = openai.OpenAI(api_key=api_key)


available_functions = [
    {
        "name": "set_mode",
        "description": "Sets the vehicle to the specified mode",
        "parameters": {
            "type": "object",
            "properties": {
                "mode_name": {"type": "string", "description": "The mode to set (e.g., 'GUIDED')"}
            },
            "required": ["mode_name"]
        }
    },
    {
        "name": "arm_disarm",
        "description": "Arms or disarms the vehicle",
        "parameters": {
            "type": "object",
            "properties": {
                "arm_command": {"type": "boolean", "description": "True to arm, False to disarm"}
            },
            "required": ["arm_command"]
        }
    },
    {
        "name": "takeoff",
        "description": "Commands the vehicle to takeoff to a specific altitude",
        "parameters": {
            "type": "object",
            "properties": {
                "altitude": {"type": "number", "description": "Altitude in meters"}
            },
            "required": ["altitude"]
        }
    },
    {
        "name": "move_local_ned",
        "description": "Moves the vehicle to a local NED position",
        "parameters": {
            "type": "object",
            "properties": {
                "x_m": {"type": "number", "description": "X position in meters (forward)"},
                "y_m": {"type": "number", "description": "Y position in meters (right)"},
                "z_m_down": {"type": "number", "description": "Z position in meters (down)"},
                "yaw_rad": {"type": "number", "description": "Yaw in radians"},
                "yaw_rate_rad_s": {"type": "number", "description": "Yaw rate in radians per second"}
            },
            "required": ["x_m", "y_m", "z_m_down"]
        }
    },
    {
        "name": "move_global_int",
        "description": "Moves the vehicle to a global lat/lon/alt position",
        "parameters": {
            "type": "object",
            "properties": {
                "lat_deg_e7": {"type": "number", "description": "Latitude (degrees * 1e7)"},
                "lon_deg_e7": {"type": "number", "description": "Longitude (degrees * 1e7)"},
                "alt_m": {"type": "number", "description": "Altitude in meters"},
                "yaw_rad": {"type": "number", "description": "Yaw in radians"},
                "yaw_rate_rad_s": {"type": "number", "description": "Yaw rate in radians per second"}
            },
            "required": ["lat_deg_e7", "lon_deg_e7", "alt_m"]
        }
    },
    {
        "name": "condition_yaw",
        "description": "Sets the vehicle's yaw",
        "parameters": {
            "type": "object",
            "properties": {
                "angle_deg": {"type": "number", "description": "Target angle in degrees"},
                "speed_deg_s": {"type": "number", "description": "Angular speed in degrees per second"},
                "direction": {"type": "number", "description": "Direction: -1 for counter-clockwise, 1 for clockwise"},
                "relative_offset": {"type": "boolean", "description": "If true, angle is relative to current heading"}
            },
            "required": ["angle_deg", "speed_deg_s", "direction", "relative_offset"]
        }
    },
    {
        "name": "change_speed",
        "description": "Changes the vehicle's speed",
        "parameters": {
            "type": "object",
            "properties": {
                "speed_type": {"type": "number", "description": "0=Airspeed, 1=Ground Speed, 2=Climb Speed, 3=Descent Speed"},
                "speed_m_s": {"type": "number", "description": "Speed in meters per second"},
                "throttle_pct": {"type": "number", "description": "Throttle percentage (-1 for no change)"},
                "relative": {"type": "boolean", "description": "If true, speed is relative to current speed"}
            },
            "required": ["speed_type", "speed_m_s", "throttle_pct", "relative"]
        }
    },
    {
        "name": "generate_cross_coverage_path",
        "description": "Generate cross coverage path from waypoints data with specified parameters",
        "parameters": {
            "type": "object",
            "properties": {
                "waypoints_data": {
                    "type": "array",
                    "description": "List of waypoint dictionaries containing coordinates and metadata",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "lat": {"type": "number"},
                                        "lon": {"type": "number"},
                                        "alt": {"type": "number"}
                                    }
                                }
                            },
                            "description": {"type": "string"},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "pointCount": {"type": "number"},
                                    "area": {"type": "number"},
                                    "perimeter": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "altitude": {"type": "number", "description": "Flight altitude in meters (default: 50)"},
                "line_spacing_in_meter": {"type": "number", "description": "Distance between parallel lines in meters (default: 20)"},
                "smooth_path_edges": {"type": "boolean", "description": "Whether to smooth path edges (default: True)"},
                "smooth_path_edge_intensity": {"type": "number", "description": "Smoothing intensity 0-100 (default: 50)"}
            },
            "required": ["waypoints_data"]
        }
    },
    {
        "name": "generate_waypoint_json",
        "description": "Generate waypoint JSON file in the format required by the frontend for 3D drone movement in Cesium",
        "parameters": {
            "type": "object",
            "properties": {
                "waypoints_data": {
                    "type": "array",
                    "description": "List of waypoint dictionaries containing coordinates and metadata",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "coordinates": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "lat": {"type": "number"},
                                        "lon": {"type": "number"},
                                        "alt": {"type": "number"}
                                    }
                                }
                            },
                            "description": {"type": "string"},
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "pointCount": {"type": "number"},
                                    "area": {"type": "number"},
                                    "perimeter": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "mission_name": {"type": "string", "description": "Name of the mission (default: 'Sky Loom Remote Mission')"},
                "location": {"type": "string", "description": "Location of the mission (default: 'Remote Location')"},
                "drone_name": {"type": "string", "description": "Name of the drone (default: 'Hovermax')"}
            },
            "required": ["waypoints_data"]
        }
    },
    {
        "name": "generate_dynamic_waypoints_from_command",
        "description": "Generate a waypoint JSON that mirrors the user's movement command so the Cesium 3D drone can move in sync.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The original natural language command issued by the user"},
                "current_position": {
                    "type": "object",
                    "description": "Optional current drone position if available",
                    "properties": {
                        "lon": {"type": "number"},
                        "lat": {"type": "number"},
                        "alt": {"type": "number"}
                    }
                }
            },
            "required": ["command"]
        }
    }
]

def execute_command(function_name, args, master_conn=None):
    
    # This function map is necessary to map function names from the API calls to their actual function implementations
    # Without it, we wouldn't be able to dynamically call the right drone control function based on the command name
    function_map = {
        "set_mode": set_mode,
        "arm_disarm": arm_disarm,
        "takeoff": takeoff,
        "condition_yaw": condition_yaw,
        "change_speed": change_speed,
        "move_local_ned": move_local_ned,
        "move_global_int": move_global_int,
        "generate_cross_coverage_path": generate_cross_coverage_path,
        "generate_waypoint_json": generate_waypoint_json,
        "generate_dynamic_waypoints_from_command": generate_dynamic_waypoints_from_command
    }
    
    # Keep track of executed functions for logging/debugging
    function_list = [{"name": function_name, "args": args}]
    
    #print(function_list)
    #print(f"Functions to execute: {[f['name'] for f in function_list]}")
    #print(f"With arguments: {[f['args'] for f in function_list]}")
    func = function_map.get(function_name)
    if func is None:
        #print(f"Error: Function {function_name} not found")
        return False
    
    # Call the function with master_conn and the provided arguments
    try:
        # Use a separate thread with a timeout to prevent hanging
        import threading
        import queue

        result_queue = queue.Queue()
        
        def run_with_timeout():
            try:
                # Special handling for non-MAVLink helper functions which should not receive master_conn
                if function_name in ["generate_cross_coverage_path", "generate_waypoint_json", "generate_dynamic_waypoints_from_command"]:
                    result = func(**args)  # Don't pass master_conn
                elif master_conn is not None:
                    result = func(master_conn, **args)
                else:
                    # For other functions when master_conn is None, just return success
                    result = True
                result_queue.put(("success", result))
            except Exception as e:
                result_queue.put(("error", str(e)))
        
        # Start the function in a separate thread
        thread = threading.Thread(target=run_with_timeout)
        thread.daemon = True
        thread.start()
        
        # Wait for the function to complete with timeout
        try:
            status, result = result_queue.get(timeout=5)  # 10 second timeout
            if status == "error":
                #print(f"Error executing {function_name}: {result}")
                return -1  # Return -1 for error
            else:
                #print(f"Result: {result}")
                return result if result is not None else -1  # Return ACK or -1 if None
        except queue.Empty:
            #print(f"Function {function_name} timed out after 10 seconds. Continuing...")
            return -1  # Return -1 for timeout
            
    except Exception as e:
        #print(f"Error executing {function_name}: {e}")
        return False

def get_and_execute_drone_commands(user_input, waypoints_data=None):
    try:
        # Check if this is a cross coverage command
        is_cross_coverage = ("cross coverage" in user_input.lower() or 
                           "cross cover" in user_input.lower() or 
                           "cpp" in user_input.lower())
        
        # Check if this is a surveillance command (should connect to drone)
        is_surveillance = user_input.startswith("[SURVEILLANCE]")
        
        # Only connect to drone if not a cross coverage command
        master = None
        if not is_cross_coverage:
            try:
                master = mavutil.mavlink_connection('udp:127.0.0.1:14550', source_system=255)
                # Use bounded wait to avoid stalling subsequent requests
                check_heartbeat(master, timeout_s=5.0)
            except Exception as e:
                print(f"Warning: Could not connect to drone: {e}")
                print("Continuing without drone connection for testing...")
                master = None
        
        # Call OpenAI with a bounded timeout using a worker thread
        import threading
        import queue

        def _call_openai(q: "queue.Queue"):
            try:
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You control a drone with functions. Convert natural language to drone control function calls. When you see commands about 'cross coverage', 'cross cover path', 'cpp path', or similar, you MUST call the generate_cross_coverage_path function with the appropriate parameters extracted from the command. After any movement-related command (e.g., takeoff, move_local_ned, move_global_int, condition_yaw, change_speed), you MUST also call generate_dynamic_waypoints_from_command with the original command so the frontend receives a full waypoint JSON for Cesium. If the user explicitly asks for a waypoint JSON from existing waypoints, you MAY call generate_waypoint_json. For commands starting with '[SURVEILLANCE]', extract the actual command after the bracket and process it normally (e.g., '[SURVEILLANCE] take off' -> 'take off')."},
                        {"role": "user", "content": user_input}
                    ],
                    tools=[{"type": "function", "function": func} for func in available_functions],
                    tool_choice="auto"
                )
                q.put(("success", resp))
            except Exception as e:
                q.put(("error", e))

        _q: "queue.Queue" = queue.Queue()
        _t = threading.Thread(target=_call_openai, args=(_q,))
        _t.daemon = True
        _t.start()

        try:
            status, payload = _q.get(timeout=10)
            if status == "error":
                print(f"OpenAI request error: {payload}")
                return False, [], None
            response = payload
        except queue.Empty:
            print("OpenAI request timed out")
            return False, [], None
        
        
        message = response.choices[0].message
        print(f"OpenAI response: {message.content}")
        print(f"Tool calls: {message.tool_calls}")
        if message.tool_calls:
            commands = []
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # If this is the generate_cross_coverage_path function and waypoints_data is provided,
                # replace the waypoints_data parameter with the actual waypoints
                if function_name == "generate_cross_coverage_path" and waypoints_data is not None:
                    function_args["waypoints_data"] = waypoints_data
                
                args_str = ", ".join([f"{k}={repr(v)}" for k, v in function_args.items()])

                function_call = f"{function_name}(master_conn, {args_str})"

                commands.append((function_name, function_args))

                #print(f"Queued command: {function_call}")

            # AUTOMATICALLY ADD DYNAMIC WAYPOINT GENERATION for any movement command
            movement_functions = ["takeoff", "move_local_ned", "move_global_int", "condition_yaw", "change_speed"]
            has_movement = any(cmd[0] in movement_functions for cmd in commands)
            
            if has_movement:
                print("Movement command detected - automatically adding dynamic waypoint generation")
                commands.append(("generate_dynamic_waypoints_from_command", {"command": user_input}))

            function_list = []
            
            waypoint_data = None
            for i, (function_name, function_args) in enumerate(commands):
                ack_value = execute_command(function_name, function_args, master)
                function_list.append([function_name, ack_value])
                
                # If this is a waypoint generation function, store the result
                if function_name in ["generate_waypoint_json", "generate_dynamic_waypoints_from_command"] and ack_value is not None:
                    waypoint_data = ack_value
                
                if ack_value is False or ack_value == "timeout":
                    return False, function_list, waypoint_data
                #print(function_list)
            return True, function_list, waypoint_data
        else:
            
            return False, [], None
            
    except Exception as e:
        #print(f"Error: {str(e)}")
        return False, [], None




