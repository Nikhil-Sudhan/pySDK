import argparse
from anyio import sleep
from pymavlink import mavutil
import time
import math

def connect_vehicle():
    """Connect to the vehicle and return the connection object"""
    master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    print("Heartbeat received from system (system %u component %u)" % (master.target_system, master.target_component))
    return master

def setup_guided_mode(master):
    """Set up guided mode and arm the vehicle"""
    mode_id = master.mode_mapping().get("GUIDED")

    # Send MAV_CMD_DO_SET_MODE (command ID: 176)
    master.mav.command_long_send(
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_MODE,
        0,  # Confirmation
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,  # param1: mode flag
        mode_id,  # param2: custom_mode (e.g., GUIDED)
        0, 0, 0, 0, 0  # param3-7: not used
    )
    msg = master.recv_match(type='COMMAND_ACK', blocking=True)
    print(msg)

    # Arm the vehicle
    master.mav.command_long_send(master.target_system, master.target_component,
                                            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)
    msg = master.recv_match(type='COMMAND_ACK', blocking=True)
    print(msg)

    # Command takeoff
    master.mav.command_long_send(master.target_system, master.target_component,
                                            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 10)
    msg = master.recv_match(type='COMMAND_ACK', blocking=True)
    print(msg)

def request_message_interval(master, message_id, frequency_hz):
    """Request MAVLink message in a desired frequency"""
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

def print_telemetry(mode, armed, lat, lon, yaw_deg, ground_speed, vertical_speed):
    """Print telemetry data in the specified format"""
    print(f"Mode: {mode} {'ARMED' if armed else 'DISARMED'}\t", end='')
    print(f"Lat: {lat:.7f}\t", end='')
    print(f"Lon: {lon:.7f}")
    print(f"Yaw: {yaw_deg:.1f}°\t", end='')
    print(f"Ground Speed: {ground_speed:.1f} m/s\t", end='')
    print(f"Vertical Speed: {vertical_speed:.1f} m/s")
    print("-" * 80)  # Separator line

def start_telemetry_monitor():
    """Main function to start telemetry monitoring"""
    # Connect to vehicle
    master = connect_vehicle()
    
    # Setup vehicle
    setup_guided_mode(master)
    setup_data_streams(master)

    print("\n--- Starting Telemetry Monitor ---\n")

    # Initialize variables to store telemetry data
    mode = "UNKNOWN"
    armed = False
    lat = 0
    lon = 0
    yaw_deg = 0
    ground_speed = 0
    vertical_speed = 0

    try:
        while True:
            # Wait for a message
            msg = master.recv_match(blocking=True, timeout=1.0)
            
            if not msg:
                continue
                
            # Filter out unwanted messages
            if msg.get_type() == 'BAD_DATA':
                continue
                
            # Update telemetry data based on message type
            msg_type = msg.get_type()
            
            if msg_type == "ATTITUDE":
                yaw_deg = math.degrees(msg.yaw)
            
            elif msg_type == "GLOBAL_POSITION_INT":
                lat = msg.lat / 1e7  # Convert from int32 to degrees
                lon = msg.lon / 1e7  # Convert from int32 to degrees
                vertical_speed = -msg.vz / 100.0  # Convert cm/s to m/s (note: positive up)
                
            elif msg_type == "VFR_HUD":
                ground_speed = msg.groundspeed
                
            elif msg_type == "HEARTBEAT":
                mode = master.flightmode
                armed = msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
                
            # Print updated telemetry
            print_telemetry(mode, armed, lat, lon, yaw_deg, ground_speed, vertical_speed)
            time.sleep(0.1)  # Small delay to prevent flooding the terminal
            
    except KeyboardInterrupt:
        print("\n--- Telemetry Monitor Stopped ---")

if __name__ == "__main__":
    start_telemetry_monitor()