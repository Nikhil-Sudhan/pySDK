from pymavlink import mavutil
from time import sleep
import time

from src.auto.v_function import *



def check_heartbeat(master_conn, timeout_s: float = 5.0):
    """Wait for a MAVLink heartbeat with a timeout to avoid indefinite blocking.

    Raises TimeoutError if no heartbeat is received within the timeout.
    """
    msg = master_conn.wait_heartbeat(timeout=timeout_s)
    if not msg:
        raise TimeoutError("No MAVLink heartbeat received within timeout")
    # print("Heartbeat received from system (system %u component %u)" % (master_conn.target_system, master_conn.target_component))

def set_mode(master_conn, mode_name):
    
    mode_id = master_conn.mode_mapping().get(mode_name.upper())
    

    master_conn.mav.command_long_send(
        master_conn.target_system,
        master_conn.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        0,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id,
        0, 0, 0, 0, 0
    )
    msg = master_conn.recv_match(type='COMMAND_ACK', blocking=True)
    #print(msg.result)
    return msg.result if msg else None

def arm_disarm(master_conn, arm_command):
    
    master_conn.mav.command_long_send(
        master_conn.target_system,
        master_conn.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1 if arm_command else 0,
        0, 0, 0, 0, 0, 0
    )
    action = "Arm" if arm_command else "Disarm"
    msg = master_conn.recv_match(type='COMMAND_ACK', blocking=True)
    #print(f"{action} command: {msg}")
    
    # For arm command, wait until armed status is confirmed
    if arm_command:
        if wait_until_armed():
            return msg.result if msg else None
        else:
            #print("Failed to confirm armed status")
            return None
    # For disarm command, just check command acknowledgment
    else:
        return msg.result if msg else None

def takeoff(master_conn, altitude):
    # Send takeoff command
    master_conn.mav.command_long_send(
        master_conn.target_system,
        master_conn.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        altitude
    )
    
    # Wait for command acknowledgment
    msg = master_conn.recv_match(type='COMMAND_ACK', blocking=True)
    #print(f"Takeoff to {altitude}m: {msg}")
    
    # Verify command was accepted
    return msg.result if msg else None

def condition_yaw(master_conn, angle_deg, speed_deg_s, direction, relative_offset):
    
    master_conn.mav.command_long_send(
        master_conn.target_system,
        master_conn.target_component,
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,
        0,
        angle_deg,
        speed_deg_s,
        direction,
        1 if relative_offset else 0,
        0, 0, 0
    )
    msg = master_conn.recv_match(type='COMMAND_ACK', blocking=True)
    #print(f"Condition Yaw (angle: {angle_deg}, speed: {speed_deg_s}, dir: {direction}): {msg}")
    return msg.result if msg else None

def change_speed(master_conn, speed_type, speed_m_s, throttle_pct, relative):
    
    master_conn.mav.command_long_send(
        master_conn.target_system,
        master_conn.target_component,
        mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,
        0,
        speed_type,
        speed_m_s,
        throttle_pct,
        1 if relative else 0,
        0, 0, 0
    )
    msg = master_conn.recv_match(type='COMMAND_ACK', blocking=True)
    #print(f"Change speed (type: {speed_type}, speed: {speed_m_s}m/s): {msg}")
    return msg.result if msg else None

def move_local_ned(master_conn, x_m, y_m, z_m_down, yaw_rad=0, yaw_rate_rad_s=0):
    
    # Calculate movement time (assuming 2 m/s movement speed)
    movement_speed = 2.0  # m/s
    distance = (x_m**2 + y_m**2 + z_m_down**2)**0.5
    movement_time = distance / movement_speed if distance > 0 else 0
    
    if movement_time > 0:
        # Calculate velocity components
        vx = x_m / movement_time
        vy = y_m / movement_time
        vz = z_m_down / movement_time
        
        # Send velocity command
        master_conn.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
            0,
            master_conn.target_system,
            master_conn.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            int(0b110111000111),  # Use velocity, ignore position
            0, 0, 0,  # Position (ignored)
            vx, vy, vz,  # Velocity
            0, 0, 0,  # Acceleration (ignored)
            yaw_rad, 0
        ))
        
        # Move for calculated time
        time.sleep(movement_time)
    
    # Stop movement by sending zero velocities
    for _ in range(3):
        master_conn.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
            0,
            master_conn.target_system,
            master_conn.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            int(0b110111000111),  # Use velocity
            0, 0, 0,  # Position (ignored)
            0, 0, 0,  # Zero velocity = stop and hover
            0, 0, 0,  # Acceleration (ignored)
            yaw_rad, 0
        ))
        time.sleep(0.1)
    
    return True

def move_global_int(master_conn, lat_deg_e7, lon_deg_e7, alt_m, yaw_rad=0, yaw_rate_rad_s=0):
    master_conn.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(
        0,
        master_conn.target_system,
        master_conn.target_component,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        int(0b110111111000),
        lat_deg_e7,
        lon_deg_e7,
        alt_m,
        0, 0, 0,
        0, 0, 0,
        yaw_rad, yaw_rate_rad_s
    ))
    #print(f"Sent move_global_int command (lat:{lat_deg_e7}, lon:{lon_deg_e7}, alt:{alt_m}, yaw:{yaw_rad})")






def generate_dynamic_waypoints_from_command(command, current_position=None):
    """
    Generate dynamic waypoints based on the actual drone command
    
    Args:
        command: The drone command that was executed
        current_position: Current drone position (optional)
    
    Returns:
        dict: Waypoint JSON with dynamic waypoints based on command
    """
    import json
    import re
    from datetime import datetime
    
    # Default home base coordinates
    home_lon = 77.7243
    home_lat = 9.6212
    home_alt = 0
    
    # Parse command for movement parameters
    command_lower = command.lower()
    waypoints = []
    
    # Start with home position
    current_lon = home_lon
    current_lat = home_lat
    current_alt = home_alt
    
    # Parse takeoff command
    if "take off" in command_lower or "takeoff" in command_lower:
        # Extract altitude from command
        alt_match = re.search(r'(\d+)\s*(?:meter|m)', command_lower)
        takeoff_alt = int(alt_match.group(1)) if alt_match else 150
        
        waypoints.append({
            "id": "waypoint_1",
            "name": "Takeoff Point",
            "longitude": current_lon,
            "latitude": current_lat,
            "altitude": takeoff_alt,
            "description": f"Takeoff to {takeoff_alt}m altitude"
        })
        current_alt = takeoff_alt
    
    # Parse movement commands
    if "move" in command_lower:
        # Parse distance and direction
        distance_match = re.search(r'(\d+)\s*(?:meter|m)', command_lower)
        distance = int(distance_match.group(1)) if distance_match else 20
        
        # Convert meters to coordinate offset (approximate)
        # 1 meter ≈ 0.00001 degrees (rough approximation)
        coord_offset = distance * 0.00001
        
        if "left" in command_lower:
            current_lon -= coord_offset
            direction = "left"
        elif "right" in command_lower:
            current_lon += coord_offset
            direction = "right"
        elif "forward" in command_lower or "ahead" in command_lower:
            current_lat += coord_offset
            direction = "forward"
        elif "backward" in command_lower or "back" in command_lower:
            current_lat -= coord_offset
            direction = "backward"
        elif "up" in command_lower:
            current_alt += distance
            direction = "up"
        elif "down" in command_lower:
            current_alt -= distance
            direction = "down"
        else:
            # Default to forward movement
            current_lat += coord_offset
            direction = "forward"
        
        waypoints.append({
            "id": f"waypoint_{len(waypoints) + 1}",
            "name": f"Move {direction.title()}",
            "longitude": current_lon,
            "latitude": current_lat,
            "altitude": current_alt,
            "description": f"Move {distance}m {direction}"
        })
    
    # Parse yaw/rotation commands
    if "yaw" in command_lower or "rotate" in command_lower or "turn" in command_lower:
        angle_match = re.search(r'(\d+)\s*(?:degree|deg)', command_lower)
        angle = int(angle_match.group(1)) if angle_match else 90
        
        waypoints.append({
            "id": f"waypoint_{len(waypoints) + 1}",
            "name": f"Yaw {angle}°",
            "longitude": current_lon,
            "latitude": current_lat,
            "altitude": current_alt,
            "description": f"Rotate {angle} degrees"
        })
    
    # Parse speed changes
    if "speed" in command_lower:
        speed_match = re.search(r'(\d+)\s*(?:m/s|mps)', command_lower)
        speed = int(speed_match.group(1)) if speed_match else 10
        
        waypoints.append({
            "id": f"waypoint_{len(waypoints) + 1}",
            "name": f"Speed Change",
            "longitude": current_lon,
            "latitude": current_lat,
            "altitude": current_alt,
            "description": f"Change speed to {speed} m/s"
        })
    
    # If no waypoints were generated, create a basic one
    if not waypoints:
        waypoints.append({
            "id": "waypoint_1",
            "name": "Command Execution",
            "longitude": current_lon,
            "latitude": current_lat,
            "altitude": current_alt,
            "description": f"Execute command: {command}"
        })
    
    # Create the waypoint JSON response
    waypoint_json = {
        "mission": {
            "name": f"Dynamic Mission - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "location": "Dynamic Location",
            "droneName": "Hovermax",
            "homeBase": {
                "longitude": home_lon,
                "latitude": home_lat,
                "altitude": home_alt,
                "name": "HOME BASE",
                "description": "Starting position"
            },
            "drone": {
                "longitude": current_lon,
                "latitude": current_lat,
                "altitude": current_alt,
                "name": "Dynamic Drone",
                "description": f"Current position after: {command}"
            },
            "waypoints": waypoints,
            "flightPath": {
                "width": 4,
                "color": "YELLOW",
                "glowPower": 0.4
            }
        }
    }
    
    return waypoint_json



