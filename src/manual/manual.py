import json

# Load the GeoJSON file
with open('assets/test.geojson', 'r') as f:
    geojson_data = json.load(f)

# Extract the coordinates from the LineString geometry
features = geojson_data['features']
for feature in features:
    if feature['geometry']['type'] == 'LineString':
        coordinates = feature['geometry']['coordinates']
        
        print("Longitude, Latitude, Altitude:")
        for coord in coordinates:
            longitude = coord[0]
            latitude = coord[1]
            altitude = coord[2]
            
          

