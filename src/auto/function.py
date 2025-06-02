from pymavlink import mavutil
from time import sleep
import time

from src.auto.v_function import *



def check_heartbeat(master_conn):
  
    master_conn.wait_heartbeat()
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



