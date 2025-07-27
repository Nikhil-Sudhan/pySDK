import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def execute_drone_command(command):
    """Execute a natural language command for the drone"""
    url = f"{BASE_URL}/execute-command"
    payload = {"command": command}
    
    response = requests.post(url, json=payload)
    return response.json()

def start_manual_mode(geojson_file):
    """Start manual mode with GeoJSON waypoints"""
    url = f"{BASE_URL}/manual-mode"
    payload = {"geojson_file": geojson_file}
    
    response = requests.post(url, json=payload)
    return response.json()

def start_click_to_go():
    """Start click-to-go mode"""
    url = f"{BASE_URL}/click-to-go"
    payload = {}
    
    response = requests.post(url, json=payload)
    return response.json()

def start_joystick():
    """Start joystick control"""
    url = f"{BASE_URL}/joystick"
    payload = {}
    
    response = requests.post(url, json=payload)
    return response.json()

def check_health():
    """Check API health"""
    url = f"{BASE_URL}/health"
    response = requests.get(url)
    return response.json()

if __name__ == "__main__":
    # Example usage
    print("Checking API health...")
    health = check_health()
    print(f"Health: {health}")
    
    print("\nExecuting drone command...")
    result = execute_drone_command("Take off to 10 meters altitude")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\nStarting manual mode...")
    manual_result = start_manual_mode("assets/test.geojson")
    print(f"Manual mode: {json.dumps(manual_result, indent=2)}") 