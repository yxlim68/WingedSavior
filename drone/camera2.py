import tello
import math

# Initialize Tello drone
drone = tello.Tello()
drone.connect()
drone.streamon()


def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Distance in meters


def calculate_bearing(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    return (math.degrees(math.atan2(y, x)) + 360) % 360  # Bearing in degrees


def move_to_gps_coordinate(current_lat, current_lon, target_lat, target_lon):
    distance = haversine(current_lat, current_lon, target_lat, target_lon)
    bearing = calculate_bearing(current_lat, current_lon, target_lat, target_lon)

    # Move drone according to calculated distance and bearing
    # Here, you'll need to convert bearing and distance to Tello commands
    if bearing < 45 or bearing >= 315:
        drone.move_forward(distance)  # Simplified; requires distance and bearing adjustments
    elif bearing < 135:
        drone.move_right(distance)
    elif bearing < 225:
        drone.move_back(distance)
    else:
        drone.move_left(distance)


# Example usage
current_lat, current_lon = 40.712776, -74.005974  # New York City (example)
target_lat, target_lon = 40.758896, -73.985130  # Times Square (example)

move_to_gps_coordinate(current_lat, current_lon, target_lat, target_lon)

drone.land()
drone.streamoff()
