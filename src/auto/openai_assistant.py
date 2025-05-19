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
    move_global_int
)

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
    }
]

def execute_command(function_name, args, master_conn):
    
    # This function map is necessary to map function names from the API calls to their actual function implementations
    # Without it, we wouldn't be able to dynamically call the right drone control function based on the command name
    function_map = {
        "set_mode": set_mode,
        "arm_disarm": arm_disarm,
        "takeoff": takeoff,
        "condition_yaw": condition_yaw,
        "change_speed": change_speed,
        "move_local_ned": move_local_ned,
        "move_global_int": move_global_int
    }
    
    # Get the function from our map
    func = function_map.get(function_name)
    if func is None:
        print(f"Error: Function {function_name} not found")
        return False
    
    # Call the function with master_conn and the provided arguments
    try:
        # Use a separate thread with a timeout to prevent hanging
        import threading
        import queue

        result_queue = queue.Queue()
        
        def run_with_timeout():
            try:
                result = func(master_conn, **args)
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
                print(f"Error executing {function_name}: {result}")
                return False
            else:
                print(f"Result: {result}")
                return result
        except queue.Empty:
            print(f"Function {function_name} timed out after 10 seconds. Continuing...")
            return "timeout"  # Return a special value for timeout
            
    except Exception as e:
        print(f"Error executing {function_name}: {e}")
        return False

def get_and_execute_drone_commands():
    try:
        # Connect to the drone
        master = mavutil.mavlink_connection('udp:127.0.0.1:14550', source_system=255)
        
        # Check heartbeat first
        check_heartbeat(master)
        
        # Get custom message input from user
        user_input = input("Enter your command: ")
        
        # Make a call to OpenAI's GPT model with function calling
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You control a drone with functions. Convert natural language to drone control function calls."},
                {"role": "user", "content": user_input}
            ],
            tools=[{"type": "function", "function": func} for func in available_functions],
            tool_choice="auto"
        )
        
        # Extract and process the response
        message = response.choices[0].message
        
        # Check if the model wants to call functions
        if message.tool_calls:
            commands = []
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Format the function call for display
                args_str = ", ".join([f"{k}={repr(v)}" for k, v in function_args.items()])
                function_call = f"{function_name}(master_conn, {args_str})"
                commands.append((function_name, function_args))
                print(f"Queued command: {function_call}")
            
            # Execute each command with a delay
            print("\nExecuting commands:")
            for i, (function_name, function_args) in enumerate(commands):
                print(f"\nCommand {i+1}/{len(commands)}:")
                result = execute_command(function_name, function_args, master)
                
                # If a command fails or times out, stop execution
                if result is False or result == "timeout":
                    print(f"Command {function_name} failed or timed out. Stopping execution.")
                    return False
                
                # Proceed directly to the next command without sleep
                # Verification functions already ensure command completion
                if i < len(commands) - 1:  # Don't print after the last command
                    print(f"Proceeding to next command...")
            
            print("\nAll commands executed!")
            return True
        else:
            # Return the content if no function was called
            print(f"No executable commands found. Response: {message.content}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

