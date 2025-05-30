import argparse
from anyio import sleep
from pymavlink import mavutil

#check heartbeat
master = mavutil.mavlink_connection('udp:127.0.0.1:14550')
master.wait_heartbeat()
print("Heartbeat received from system (system %u component %u)" % (master.target_system, master.target_component))

#changing mode to guided mode.

mode_id = master.mode_mapping().get("GUIDED")

# Send MAV_CMD_DO_SET_MODE (command ID: 176)
master.mav.command_long_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_CMD_DO_SET_MODE,
    0,  
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,  
    mode_id,  
    0, 0, 0, 0, 0  
)
msg = master.recv_match(type='COMMAND_ACK', blocking=True)
print(msg)

#to arm and disarm
#arm =1 disarm=0
master.mav.command_long_send(master.target_system, master.target_component,
                                        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0)

msg = master.recv_match(type='COMMAND_ACK', blocking=True)
print(msg)


#to takeoff
master.mav.command_long_send(master.target_system, master.target_component,
                                        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0,0, 10)

msg = master.recv_match(type='COMMAND_ACK', blocking=True)
print(msg)


#to change the yaw
master.mav.command_long_send(master.target_system, master.target_component,
                                        mavutil.mavlink.MAV_CMD_CONDITION_YAW, 0, 45, 25, -1, 0, 0, 0, 0)

msg = master.recv_match(type='COMMAND_ACK', blocking=True)
print(msg)
  
#to change the speed
master.mav.command_long_send(master.target_system, master.target_component,
                                        mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED, 0, 0, 25, 0, 0, 0, 0, 0)

msg = master.recv_match(type='COMMAND_ACK', blocking=True)
print(msg)

#to move with meters
master.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(10, master.target_system,
                         master.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED, int(0b010111111000), 60, 0, -10, 0, 0, 0, 0, 0, 0, 1.57, 0.5))

msg = master.recv_match(type='COMMAND_ACK', blocking=True)
print(msg)

#to move with lat and long
master.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_message(10, master.target_system,
                        master.target_component, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, int(0b110111111000), int(-35.3629849 * 10 ** 7), int(149.1649185 * 10 ** 7), 10, 0, 0, 0, 0, 0, 0, 1.57, 0.5))
msg = master.recv_match(type='COMMAND_ACK', blocking=True)
print(msg)



first you want to run the simulation(gazebo)

cd ardupilot_gazebo
gz sim -v4 -r iris_runway.sdf


then you want to run the ardupilot firmware

cd ardupilot
./Tools/autotest/sim_vehicle.py -v ArduCopter -f gazebo-iris --model JSON --console --map


then you want to run the python script
