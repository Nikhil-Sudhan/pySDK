import argparse
from anyio import sleep
from pymavlink import mavutil
import time
import math
import json
import os
import threading
import queue
from src.auto.openai_assistant import get_and_execute_drone_commands

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


# ============================================================================
# CONTINUOUS TELEMETRY MANAGEMENT SYSTEM
# ============================================================================

class ContinuousTelemetryManager:
    def __init__(self):
        # Priority queue: 0 = highest priority (user commands), 1 = telemetry
        self.task_queue = queue.PriorityQueue()
        self.telemetry_data = {
            'mode': "UNKNOWN",
            'armed': False,
            'lat': 0,
            'long': 0,
            'yaw': 0,
            'gs': 0,
            'vs': 0,
            'alt': 0,
            'battery': 0
        }
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        self.last_telemetry_update = 0
        self.telemetry_interval = 1.0  # Update telemetry every 1 second
        
    def start(self):
        """Start the continuous telemetry manager"""
        if self.running:
            return
            
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        # Schedule initial telemetry update
        self._schedule_telemetry()
    
    def stop(self):
        """Stop the continuous telemetry manager"""
        self.running = False
        if self.worker_thread:
            # Add a stop signal to wake up the worker
            self.task_queue.put((0, 'STOP', None))
            self.worker_thread.join(timeout=2)
    
    def execute_user_command(self, command):
        """Execute a user command with highest priority"""
        result_queue = queue.Queue()
        # Priority 0 = highest priority for user commands
        self.task_queue.put((0, 'USER_COMMAND', {'command': command, 'result_queue': result_queue}))
        
        try:
            # Wait for result with timeout
            result = result_queue.get(timeout=30)
            return result
        except queue.Empty:
            return "Command timed out"
    
    def execute_user_command_async(self, command, result_callback):
        """Execute a user command asynchronously"""
        # Priority 0 = highest priority for user commands
        self.task_queue.put((0, 'USER_COMMAND_ASYNC', {'command': command, 'callback': result_callback}))
    
    def get_telemetry_data(self):
        """Get the latest telemetry data"""
        with self.lock:
            return self.telemetry_data.copy()
    
    def _schedule_telemetry(self):
        """Schedule the next telemetry update"""
        if self.running:
            # Priority 1 = lower priority for telemetry
            self.task_queue.put((1, 'TELEMETRY', None))
    
    def _worker_loop(self):
        """Main worker loop that processes the priority queue"""
        while self.running:
            try:
                # Get next task (blocks until available)
                priority, task_type, task_data = self.task_queue.get(timeout=1.0)
                
                if task_type == 'STOP':
                    break
                    
                elif task_type == 'USER_COMMAND':
                    # Execute user command with highest priority
                    try:
                        result = get_and_execute_drone_commands(task_data['command'])
                        task_data['result_queue'].put(result)
                    except Exception as e:
                        task_data['result_queue'].put(f"Error: {str(e)}")
                
                elif task_type == 'USER_COMMAND_ASYNC':
                    # Execute user command asynchronously
                    try:
                        result = get_and_execute_drone_commands(task_data['command'])
                        task_data['callback'](result)
                    except Exception as e:
                        task_data['callback'](f"Error: {str(e)}")
                
                elif task_type == 'TELEMETRY':
                    # Update telemetry data
                    current_time = time.time()
                    if current_time - self.last_telemetry_update >= self.telemetry_interval:
                        try:
                            new_data = process_telemetry_direct()
                            with self.lock:
                                self.telemetry_data.update(new_data)
                            self.last_telemetry_update = current_time
                        except Exception as e:
                            print(f"Telemetry error: {e}")
                        
                        # Schedule next telemetry update
                        self._schedule_telemetry()
                    else:
                        # If called too early, reschedule for later
                        time.sleep(0.1)
                        self._schedule_telemetry()
                
                # Mark task as done
                self.task_queue.task_done()
                
            except queue.Empty:
                # Timeout - schedule telemetry update if needed
                current_time = time.time()
                if current_time - self.last_telemetry_update >= self.telemetry_interval:
                    self._schedule_telemetry()
                continue
            except Exception as e:
                print(f"Worker error: {e}")
                continue

# Global instance
telemetry_manager = ContinuousTelemetryManager()

def start_continuous_telemetry():
    """Start the continuous telemetry system"""
    telemetry_manager.start()

def stop_continuous_telemetry():
    """Stop the continuous telemetry system"""
    telemetry_manager.stop()

def get_live_telemetry():
    """Get current telemetry data"""
    return telemetry_manager.get_telemetry_data()

def execute_priority_command(command):
    """Execute a command with priority over telemetry"""
    return telemetry_manager.execute_user_command(command)

def execute_priority_command_async(command, callback):
    """Execute a command asynchronously with priority over telemetry"""
    telemetry_manager.execute_user_command_async(command, callback)

# For backward compatibility, keep the old call
if __name__ == "__main__":
    result = process_telemetry()
    print(f"Telemetry data: {result}")