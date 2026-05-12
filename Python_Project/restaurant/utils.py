import math
import requests

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between restaurant and delivery address in km"""
    
    # radius of Earth in km
    R = 6371 
    
    # handles all 4 coordinates and converts from degrees to radians.  Trig functions work in radians, not degrees.
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Calculate difference(d) between two points in latitude and longitude
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # calculates how far apart the two points are on the surface of a sphere
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    
    # converts above result to angular distance in radians
    c = 2 * math.asin(math.sqrt(a))
    
    # take anuglar distance and multiplies it by Earth's radius to get distance in km
    return R * c


def geocode_address(address):
    """Converts an address from string to latitude and longitude using OpenStreetMap Nominatim"""
    
    url = 'https://nominatim.openstreetmap.org/search'
    
    # query parameters
    params = {
        'q': address,       # delivery address
        'format': 'json',   # response returned will be JSON
        'limit': 1          # return a single best match
    }
    # As per usage policy, we must identify our application. Without header the request is rejected
    headers = {
        'User-Agent': 'UrbanSparkRestaurant/1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        if data:
            return float(data[0]['lat']), float(data[0]['lon']) # if results come back, return the latitude and longitude of the first result as floats.
        return None
    
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None