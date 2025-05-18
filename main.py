import argparse
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from src.main_functions import manual_mode, autonomous_mode, click_to_go, use_joystick


def parse_arguments():
    parser = argparse.ArgumentParser(description='UAV Aerial System SDK for Gazebo')
    
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-m', '--manual', metavar='GEOJSON_FILE',
                           help='Run in manual mode with GeoJSON waypoints')
    mode_group.add_argument('-a', '--auto', action='store_true',
                           help='Run in autonomous mode')
    mode_group.add_argument('-c', '--click-to-go', action='store_true',
                           help='Run in click-to-go mode')
    mode_group.add_argument('-j', '--joystick', action='store_true',
                           help='Run with joystick control')
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
   
    
    try:
        if args.manual:
            manual_mode(args.manual)
        elif args.auto:
            print("Starting in Autonomous Mode")
            autonomous_mode()
        elif args.click_to_go:
            print("Starting in Click-to-Go Mode")
            click_to_go()
        elif args.joystick:
            print("Starting with Joystick Control")
            use_joystick()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


