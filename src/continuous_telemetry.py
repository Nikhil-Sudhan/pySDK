import threading
import queue
import time
from src.telemetary import process_telemetry_direct
from src.auto.openai_assistant import get_and_execute_drone_commands

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