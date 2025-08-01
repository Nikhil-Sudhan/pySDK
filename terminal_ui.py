import curses
import time
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from src.auto.openai_assistant import get_and_execute_drone_commands
from src.continuous_telemetry import start_continuous_telemetry, stop_continuous_telemetry, get_live_telemetry, execute_priority_command_async

def format_value(value, precision=2):
    """Format numeric values with specified precision"""
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}"
    return str(value)

def main(stdscr):
    # Setup screen
    curses.curs_set(1)  # Show cursor for input
    stdscr.nodelay(True)
    stdscr.keypad(True)  # Enable special key handling
    stdscr.clear()
    
    # Get initial screen dimensions
    max_y, max_x = stdscr.getmaxyx()
    
    # Check minimum screen size
    if max_y < 10 or max_x < 40:
        raise curses.error("Terminal too small. Minimum size required: 40x10")

    logs = []   
    input_str = ""
    MAX_LOGS = 500

    # Start continuous telemetry system
    start_continuous_telemetry()

    # Simplified command processing 
    processing_command = False
    current_command = ""
    command_start_time = 0

    # Fixed telemetry section height
    telem_height = 6  # Increased by 1 for status line
    
    # Calculate window sizes ensuring they're at least 1 line high
    log_height = max(1, max_y - telem_height - 3)  # -3 for header, separator, and input
    log_win = curses.newwin(log_height, max_x, telem_height + 1, 0)
    input_win = curses.newwin(1, max_x, max_y - 1, 0)
    input_win.keypad(True)  # Enable special key handling in input window

    # Color setup
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Normal values
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warnings
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)    # Errors/Critical
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)    # For processing status
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)  # For progress

    # Initialize telemetry_data with defaults
    telemetry_data = {
        'alt': 0, 'lat': 0, 'long': 0, 'mode': 'UNKNOWN', 'gs': 0, 'vs': 0, 'yaw': 0, 'battery': 0
    }
    
    # Timing variables
    last_ui_update = 0
    ui_update_interval = 0.05  # Even faster UI updates (20 FPS)

    def command_result_callback(result):
        """Callback for when command completes"""
        nonlocal processing_command, current_command
        processing_command = False
        current_command = ""
        
        if result:
            logs.append(f"<console> {result}")
        else:
            logs.append(f"<console> Command executed successfully")
        
        if len(logs) > MAX_LOGS:
            logs[:] = logs[-MAX_LOGS:]

    while True:
        try:
            # Check if terminal was resized
            new_y, new_x = stdscr.getmaxyx()
            if new_y != max_y or new_x != max_x:
                # Resize windows
                max_y, max_x = new_y, new_x
                if max_y < 10 or max_x < 40:
                    raise curses.error("Terminal too small. Minimum size required: 40x10")
                
                log_height = max(1, max_y - telem_height - 3)
                log_win = curses.newwin(log_height, max_x, telem_height + 1, 0)
                input_win = curses.newwin(1, max_x, max_y - 1, 0)
                input_win.keypad(True)  # Re-enable keypad after resize
                stdscr.clear()

            current_time = time.time()
            
            # Get live telemetry data (always fresh from continuous system)
            telemetry_data = get_live_telemetry()

            # Update UI more frequently
            if current_time - last_ui_update >= ui_update_interval:
                # Draw telemetry
                try:
                    stdscr.addstr(0, 0, "Red Star Autonomy".center(max_x), curses.A_REVERSE)
                    stdscr.addstr(1, 0, "-" * max_x)
                    alt_str = f"ALT: {format_value(telemetry_data['alt'])}m"
                    pos_str = f"LAT: {format_value(telemetry_data['lat'], 6)}° LONG: {format_value(telemetry_data['long'], 6)}°"
                    mode_str = f"MODE: {telemetry_data['mode']}"
                    speed_str = f"GS: {format_value(telemetry_data['gs'])}m/s VS: {format_value(telemetry_data['vs'])}m/s"
                    yaw_str = f"YAW: {format_value(telemetry_data['yaw'])}°"
                    batt_str = f"BATT: {format_value(telemetry_data['battery'])}%"
                    batt_color = curses.color_pair(1)
                    if telemetry_data['battery'] <= 20:
                        batt_color = curses.color_pair(3)
                    elif telemetry_data['battery'] <= 50:
                        batt_color = curses.color_pair(2)
                    stdscr.addstr(2, 2, alt_str[:max_x-2])
                    stdscr.addstr(2, min(max_x // 3, max_x-len(pos_str)), pos_str[:max_x-max_x//3])
                    stdscr.addstr(3, 2, mode_str[:max_x-2])
                    stdscr.addstr(3, min(max_x // 3, max_x-len(speed_str)), speed_str[:max_x-max_x//3])
                    stdscr.addstr(4, 2, yaw_str[:max_x-2])
                    stdscr.addstr(4, min(max_x // 3, max_x-len(batt_str)), batt_str[:max_x-max_x//3], batt_color)
                    
                    # Enhanced status line with progress
                    if processing_command:
                        elapsed = current_time - command_start_time
                        status_str = f"Processing: {current_command} [{elapsed:.1f}s] (Ctrl+C to cancel)"
                        stdscr.addstr(5, 2, status_str[:max_x-4], curses.color_pair(5) | curses.A_BLINK)
                    else:
                        stdscr.addstr(5, 2, " " * (max_x-4))
                    
                    stdscr.addstr(6, 0, "-" * max_x)
                except curses.error:
                    pass

                # Show logs with better performance
                log_win.erase()
                visible_logs = logs[-(log_height):]
                for i, log in enumerate(visible_logs):
                    try:
                        if log.startswith("<user>"):
                            log_win.addstr(i, 0, log[:max_x], curses.color_pair(2))
                        elif log.startswith("<console>"):
                            log_win.addstr(i, 0, log[:max_x], curses.color_pair(1))
                        else:
                            log_win.addstr(i, 0, log[:max_x], curses.color_pair(3))
                    except curses.error:
                        break  # Stop if we can't draw more
                log_win.refresh()
                
                last_ui_update = current_time

            # Input handling
            input_win.erase()
            cursor_pos = len(input_str) + 2
            
            try:
                if processing_command:
                    elapsed = current_time - command_start_time
                    input_win.addstr(0, 0, f"> {input_str} (processing {elapsed:.1f}s...)")
                else:
                    input_win.addstr(0, 0, f"> {input_str}")
                input_win.move(0, min(cursor_pos, max_x-1))
            except curses.error:
                pass
                
            input_win.refresh()

            # Get input
            input_win.nodelay(True)
            ch = input_win.getch()
            
            if ch != -1:
                if ch == 3:  # Ctrl+C
                    if processing_command:
                        logs.append("<user> Command cancelled")
                        processing_command = False
                        current_command = ""
                    else:
                        break  # Exit if no command running
                elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
                    if input_str.strip() and not processing_command:
                        logs.append(f"<user> {input_str}")
                        processing_command = True
                        current_command = input_str
                        command_start_time = current_time
                        
                        # Execute command with priority using the queue system
                        execute_priority_command_async(input_str, command_result_callback)
                        
                        input_str = ""
                        if len(logs) > MAX_LOGS:
                            logs[:] = logs[-MAX_LOGS:]
                elif ch == curses.KEY_BACKSPACE or ch == 127 or ch == 8:
                    if input_str and not processing_command:
                        input_str = input_str[:-1]
                elif ch == curses.KEY_DC:
                    if input_str and not processing_command:
                        input_str = input_str[:-1]
                elif 32 <= ch <= 126 and not processing_command:
                    if len(input_str) < max_x - 3:
                        input_str += chr(ch)
            
            stdscr.refresh()
            
            # Minimal delay for high responsiveness
            time.sleep(0.005)  # 5ms delay for 200 FPS
            
        except KeyboardInterrupt:
            if processing_command:
                logs.append("<user> Command cancelled")
                processing_command = False
                current_command = ""
            else:
                break
        except curses.error as e:
            if "Terminal too small" in str(e):
                raise e
            logs.append(f"UI Error: {str(e)}")
        except Exception as e:
            logs.append(f"Error: {str(e)}")
    
    # Cleanup
    stop_continuous_telemetry()

def start_console():
    try:
        return curses.wrapper(main)
    except curses.error as e:
        print(f"Terminal Error: {str(e)}")
        print("Please resize your terminal to at least 40x10 characters.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    start_console()

def message():
    list_of_messages = [
    {"value": 0, "name": "MAV_RESULT_ACCEPTED", "description": "Command is valid (is supported and has valid parameters), and was executed."},
    {"value": 1, "name": "MAV_RESULT_TEMPORARILY_REJECTED", "description": "Command is valid, but cannot be executed at this time. Retry later may work."},
    {"value": 2, "name": "MAV_RESULT_DENIED", "description": "Command is invalid (supported but has invalid parameters). Retrying won't work."},
    {"value": 3, "name": "MAV_RESULT_UNSUPPORTED", "description": "Command is not supported (unknown)."},
    {"value": 4, "name": "MAV_RESULT_FAILED", "description": "Command is valid, but execution failed due to a non-temporary error."},
    {"value": 5, "name": "MAV_RESULT_IN_PROGRESS", "description": "Command is valid and being executed. Final result will follow."},
    {"value": 6, "name": "MAV_RESULT_CANCELLED", "description": "Command has been cancelled by a COMMAND_CANCEL message."},
    {"value": 7, "name": "MAV_RESULT_COMMAND_LONG_ONLY", "description": "Command is only accepted as COMMAND_LONG."},
    {"value": 8, "name": "MAV_RESULT_COMMAND_INT_ONLY", "description": "Command is only accepted as COMMAND_INT."},
    {"value": 9, "name": "MAV_RESULT_COMMAND_UNSUPPORTED_MAV_FRAME", "description": "Invalid command due to unsupported MAV_FRAME."}
]
    for i in range(list_of_messages):
        print(i)

    