import time
from pymavlink import mavutil

def wait_until_armed():
    print("Waiting for drone to be armed...")
    master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    
    # Set a timeout of 30 seconds
    start_time = time.time()
    timeout = 30
    
    while time.time() - start_time < timeout:
        msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1)
        if msg and (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
            print("Drone is armed.")
            return True
        print("Waiting for arm status...")
    
    print(f"Timeout: Drone not armed after {timeout} seconds")
    return False


def wait_until_altitude(master, target_alt, tolerance=0.5):
    print(f"Waiting to reach target altitude: {target_alt}m...")
    while True:
        msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=1)
        if msg:
            current_alt = msg.relative_alt / 1000.0  # Convert from mm to meters
            print(f"Current altitude: {current_alt:.2f}m")
            if abs(current_alt - target_alt) <= tolerance:
                print(f"Target altitude reached: {current_alt:.2f}m")
                return True
        else:
            print("Waiting for altitude data...")
    return False

