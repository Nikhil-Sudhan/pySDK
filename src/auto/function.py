from pymavlink import mavutil
from time import sleep
import time

from src.auto.verify_fun import *



def check_heartbeat(master_conn):
  
    master_conn.wait_heartbeat()
    print("Heartbeat received from system (system %u component %u)" % (master_conn.target_system, master_conn.target_component))

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
    print(f"Set mode to {mode_name}: {msg}")

    return msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED

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
    print(f"{action} command: {msg}")
    
    # For arm command, wait until armed status is confirmed
    if arm_command:
        if wait_until_armed():
            return msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED
        else:
            print("Failed to confirm armed status")
            return False
    # For disarm command, just check command acknowledgment
    else:
        return msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED

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
    print(f"Takeoff to {altitude}m: {msg}")
    
    # Verify command was accepted
    if msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED:
        # Wait until target altitude is reached
        if wait_until_altitude(master_conn, altitude, tolerance=0.5):
            print("Successfully reached target altitude")
            return True
        else:
            print("Failed to reach target altitude")
            return False
    else:
        print("Takeoff command was not accepted")
        return False

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
    print(f"Condition Yaw (angle: {angle_deg}, speed: {speed_deg_s}, dir: {direction}): {msg}")
    return msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED

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
    print(f"Change speed (type: {speed_type}, speed: {speed_m_s}m/s): {msg}")
    return msg and msg.result == mavutil.mavlink.MAV_RESULT_ACCEPTED

def move_local_ned(master_conn, x_m, y_m, z_m_down, yaw_rad=0, yaw_rate_rad_s=0):
    
    master_conn.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(
        0,
        master_conn.target_system,
        master_conn.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        int(0b010111111000),
        x_m, y_m, z_m_down,
        0, 0, 0,
        0, 0, 0,
        yaw_rad, yaw_rate_rad_s
    ))
    print(f"Sent move_local_ned command (x:{x_m}, y:{y_m}, z:{z_m_down}, yaw:{yaw_rad})")

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
    print(f"Sent move_global_int command (lat:{lat_deg_e7}, lon:{lon_deg_e7}, alt:{alt_m}, yaw:{yaw_rad})")



