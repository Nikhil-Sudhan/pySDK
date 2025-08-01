import argparse
from anyio import sleep
from pymavlink import mavutil
import time
import math
import json
import os

def read_telemetry_from_service(data_file="/tmp/redstar_telemetry.json"):
    """Read telemetry data from the background service"""
    try:
        # Check if file exists and is recent (less than 5 seconds old)
        if os.path.exists(data_file):
            file_age = time.time() - os.path.getmtime(data_file)
            if file_age < 5.0:  # File is recent
                with open(data_file, 'r') as f:
                    data = json.load(f)
                    # Ensure we have all required fields
                    required_fields = ['mode', 'armed', 'lat', 'long', 'yaw', 'gs', 'vs', 'alt', 'battery']
                    if all(field in data for field in required_fields):
                        return data
        return None
    except Exception:
        return None

def connect_vehicle():
    master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    return master

def request_message_interval(master, message_id, frequency_hz):
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
        message_id,  # The MAVLink message ID
        1e6 / frequency_hz,  # The interval between two messages in microseconds
        0, 0, 0, 0,  # Unused parameters
        0  # Target address of message stream (0: all systems)
    )

def setup_data_streams(master):
    """Set up all required data streams"""
    request_message_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, 10)
    request_message_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT, 5)
    request_message_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_SYS_STATUS, 1)
    request_message_interval(master, mavutil.mavlink.MAVLINK_MSG_ID_VFR_HUD, 5)

def process_telemetry_direct():
    """Direct telemetry collection (fallback method)"""
    try:
        # Connect and setup
        master = connect_vehicle()
        setup_data_streams(master)
        
        # Initialize variables
        telemetry_data = {
            'mode': "UNKNOWN",
            'armed': False,
            'lat': 0,
            'long': 0,  # Changed to match UI
            'yaw': 0,
            'gs': 0,
            'vs': 0,
            'alt': 0,
            'battery': 0
        }
        
        # Try to get initial data
        attempts = 0
        max_attempts = 10
        
        while attempts < max_attempts:
            msg = master.recv_match(blocking=True, timeout=1.0)
            
            if not msg:
                attempts += 1
                continue
                
            msg_type = msg.get_type()
            if msg_type == 'BAD_DATA':
                attempts += 1
                continue
                
            # Update telemetry data based on message type
            if msg_type == "ATTITUDE":
                telemetry_data['yaw'] = math.degrees(msg.yaw)
            elif msg_type == "GLOBAL_POSITION_INT":
                telemetry_data['lat'] = msg.lat / 1e7
                telemetry_data['long'] = msg.lon / 1e7  # Changed to match UI
                telemetry_data['alt'] = msg.relative_alt / 1000.0  # Convert mm to meters
                telemetry_data['vs'] = -msg.vz / 100.0  # Convert cm/s to m/s
            elif msg_type == "VFR_HUD":
                telemetry_data['gs'] = msg.groundspeed
            elif msg_type == "HEARTBEAT":
                telemetry_data['mode'] = master.flightmode
                telemetry_data['armed'] = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
            elif msg_type == "SYS_STATUS":
                telemetry_data['battery'] = msg.battery_remaining if hasattr(msg, 'battery_remaining') else 0
            
            attempts += 1
            
        return telemetry_data
        
    except Exception as e:
        print(f"Error in direct telemetry processing: {e}")
        return {
            'mode': "ERROR",
            'armed': False,
            'lat': 0,
            'long': 0,
            'yaw': 0,
            'gs': 0,
            'vs': 0,
            'alt': 0,
            'battery': 0
        }

def process_telemetry():
    """Main telemetry function - tries service first, falls back to direct"""
    # First try to read from the background service
    service_data = read_telemetry_from_service()
    if service_data:
        return service_data
    
    # If service data not available, fall back to direct connection
    return process_telemetry_direct()

# For backward compatibility, keep the old call
if __name__ == "__main__":
    result = process_telemetry()
    print(f"Telemetry data: {result}")