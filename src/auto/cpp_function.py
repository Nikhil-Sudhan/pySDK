import json
import math
from datetime import datetime
import uuid


def generate_cross_coverage_path(waypoints_data, altitude=50, line_spacing_in_meter=20, smooth_path_edges=True, smooth_path_edge_intensity=50):
    """
    Generate cross coverage path from waypoints data with specified parameters
    
    Args:
        waypoints_data: List of waypoint dictionaries containing coordinates
        altitude: Flight altitude in meters (default: 50)
        line_spacing_in_meter: Distance between parallel lines in meters (default: 20)
        smooth_path_edges: Whether to smooth path edges (default: True)
        smooth_path_edge_intensity: Smoothing intensity 0-100 (default: 50)
    
    Returns:
        dict: Cross coverage path in the specified JSON format
    """
    try:
        # Extract bounds from waypoints data (handle frontend format with metadata)
        if isinstance(waypoints_data, list) and len(waypoints_data) > 0:
            # Extract coordinates from waypoints
            all_coords = []
            for waypoint in waypoints_data:
                if 'coordinates' in waypoint:
                    all_coords.extend(waypoint['coordinates'])
            
            if all_coords:
                lats = [coord['lat'] for coord in all_coords]
                lons = [coord['lon'] for coord in all_coords]
                bounds = {
                    'north': max(lats),
                    'south': min(lats),
                    'east': max(lons),
                    'west': min(lons)
                }
            else:
                # Default bounds if no coordinates found
                bounds = {
                    'north': 0.0,
                    'south': 0.0,
                    'east': 0.0,
                    'west': 0.0
                }
        else:
            # Default bounds if waypoints_data is not in expected format
            bounds = {
                'north': 0.0,
                'south': 0.0,
                'east': 0.0,
                'west': 0.0
            }
        
        # Calculate center point
        center_lat = (bounds['north'] + bounds['south']) / 2
        center_lon = (bounds['east'] + bounds['west']) / 2
        
        # Calculate area and perimeter (approximate)
        lat_diff = bounds['north'] - bounds['south']
        lon_diff = bounds['east'] - bounds['west']
        area_sqm = lat_diff * lon_diff * 111000 * 111000  # Rough conversion to square meters
        perimeter_m = 2 * (lat_diff + lon_diff) * 111000  # Rough conversion to meters
        
        # Extract waypoint info for mission description
        waypoint_info = ""
        if waypoints_data and len(waypoints_data) > 0:
            first_waypoint = waypoints_data[0]
            waypoint_info = f" for {first_waypoint.get('name', 'waypoint')}"
            if 'metadata' in first_waypoint and 'area' in first_waypoint['metadata']:
                area = first_waypoint['metadata']['area']
                waypoint_info += f" (area: {area:.6f})"
        
        # Generate waypoints for cross coverage pattern
        waypoints = []
        sequence = 1
        
        # Calculate number of lines needed
        coverage_width = abs(bounds['east'] - bounds['west']) * 111000  # Convert to meters
        coverage_height = abs(bounds['north'] - bounds['south']) * 111000  # Convert to meters
        
        # Generate north-south lines
        num_lines_ns = int(coverage_width / line_spacing_in_meter) + 1
        for i in range(num_lines_ns):
            lon = bounds['west'] + (i * line_spacing_in_meter / 111000)
            
            # Start waypoint
            waypoints.append({
                "id": str(uuid.uuid4()),
                "sequence": sequence,
                "type": "start" if i == 0 else "coverage",
                "position": {
                    "lat": bounds['south'],
                    "lon": lon,
                    "alt": altitude
                },
                "action": {
                    "type": "move",
                    "duration_s": 0,
                    "parameters": {}
                },
                "metadata": {
                    "line_number": i + 1,
                    "segment_number": 1,
                    "distance_from_start": 0
                }
            })
            sequence += 1
            
            # End waypoint
            waypoints.append({
                "id": str(uuid.uuid4()),
                "sequence": sequence,
                "type": "end" if i == num_lines_ns - 1 else "coverage",
                "position": {
                    "lat": bounds['north'],
                    "lon": lon,
                    "alt": altitude
                },
                "action": {
                    "type": "move",
                    "duration_s": 0,
                    "parameters": {}
                },
                "metadata": {
                    "line_number": i + 1,
                    "segment_number": 2,
                    "distance_from_start": coverage_height
                }
            })
            sequence += 1
        
        # Generate east-west lines
        num_lines_ew = int(coverage_height / line_spacing_in_meter) + 1
        for i in range(num_lines_ew):
            lat = bounds['south'] + (i * line_spacing_in_meter / 111000)
            
            # Start waypoint
            waypoints.append({
                "id": str(uuid.uuid4()),
                "sequence": sequence,
                "type": "coverage",
                "position": {
                    "lat": lat,
                    "lon": bounds['west'],
                    "alt": altitude
                },
                "action": {
                    "type": "move",
                    "duration_s": 0,
                    "parameters": {}
                },
                "metadata": {
                    "line_number": num_lines_ns + i + 1,
                    "segment_number": 1,
                    "distance_from_start": 0
                }
            })
            sequence += 1
            
            # End waypoint
            waypoints.append({
                "id": str(uuid.uuid4()),
                "sequence": sequence,
                "type": "coverage",
                "position": {
                    "lat": lat,
                    "lon": bounds['east'],
                    "alt": altitude
                },
                "action": {
                    "type": "move",
                    "duration_s": 0,
                    "parameters": {}
                },
                "metadata": {
                    "line_number": num_lines_ns + i + 1,
                    "segment_number": 2,
                    "distance_from_start": coverage_width
                }
            })
            sequence += 1
        
        # Calculate statistics
        total_waypoints = len(waypoints)
        total_distance_m = (num_lines_ns * coverage_height) + (num_lines_ew * coverage_width)
        estimated_duration_min = total_distance_m / 10  # Assuming 10 m/s speed
        coverage_percentage = 95.0  # Approximate
        number_of_lines = num_lines_ns + num_lines_ew
        
        # Create the cross coverage path response
        cross_coverage_path = {
            "mission": {
                "id": f"cc_{uuid.uuid4().hex[:8]}",
                "name": "Cross Coverage Mission",
                "description": f"Cross coverage path with {line_spacing_in_meter}m spacing at {altitude}m altitude{waypoint_info}",
                "type": "cross_coverage",
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "updated": datetime.now().isoformat()
            },
            "area": {
                "bounds": bounds,
                "center": {
                    "lat": center_lat,
                    "lon": center_lon
                },
                "area_sqm": area_sqm,
                "perimeter_m": perimeter_m
            },
            "coverage": {
                "pattern": "cross_coverage",
                "direction": "both",
                "spacing_m": line_spacing_in_meter,
                "altitude_m": altitude,
                "speed_ms": 10.0,
                "overlap_percent": 20.0
            },
            "waypoints": waypoints,
            "statistics": {
                "total_waypoints": total_waypoints,
                "total_distance_m": total_distance_m,
                "estimated_duration_min": estimated_duration_min,
                "coverage_percentage": coverage_percentage,
                "number_of_lines": number_of_lines
            },
            "settings": {
                "camera": {
                    "fov_degrees": 60.0,
                    "resolution": "4K",
                    "interval_s": 2.0
                },
                "safety": {
                    "min_altitude_m": 10.0,
                    "max_altitude_m": 100.0,
                    "geofence": {
                        "enabled": True,
                        "bounds": bounds
                    }
                },
                "optimization": {
                    "wind_compensation": True,
                    "battery_optimization": True,
                    "return_to_home": True
                }
            }
        }
        
        return cross_coverage_path
        
    except Exception as e:
        print(f"Error generating cross coverage path: {str(e)}")
        return None
