import json
import sys
from pymavlink import mavutil
import time

# Import with absolute path
from src.auto.openai_assistant import get_and_execute_drone_commands




def check_connection():
    master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
    master.wait_heartbeat()
    print("Heartbeat received from system (system %u component %u)" % (master.target_system, master.target_component))
    # Wait for a 'SYS_STATUS' message with the specified values.
    msg = master.recv_match(type='SYS_STATUS',blocking=True)
    print(msg)
    

def manual_mode(address):
    if check_connection() == True:
        print()

def autonomous_mode():
    while True:
        intput_str=input("Enter the command")
        get_and_execute_drone_commands(intput_str)
    
    

def click_to_go():
   print("Autonomous mode")

def use_joystick():
    print("Autonomous mode")