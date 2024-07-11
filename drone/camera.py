import threading
import time
import cv2
import numpy as np
from djitellopy import Tello, TelloException
from ultralytics import YOLO
from plyer import notification
import os
import mysql.connector as connector
import platform
import subprocess
import sys
import hashlib

# Assuming a frame size of 960x720 (adjust according to your Tello camera resolution)
FRAME_WIDTH = 960
FRAME_HEIGHT = 720

# Check if XAMPP is running and start it if not
def check_and_start_xampp():
    if platform.system() == 'Windows':
        # Check if Apache is running
        apache_status = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq httpd.exe'], stdout=subprocess.PIPE)
        mysql_status = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'], stdout=subprocess.PIPE)

        if b'No tasks' in apache_status.stdout or b'No tasks' in mysql_status.stdout:
            print("Starting XAMPP...")
            subprocess.run(['C:\\xampp\\xampp_start.exe'])
            time.sleep(10)  # Wait for XAMPP to start
        else:
            print("XAMPP is already running.")
    else:
        print("Unsupported OS")
        sys.exit(1)

# Stop XAMPP after the script finishes
def stop_xampp():
    if platform.system() == 'Windows':
        print("Stopping XAMPP...")
        subprocess.run(['C:\\xampp\\xampp_stop.exe'])
    elif platform.system() == 'Linux':
        print("Stopping XAMPP...")
        subprocess.run(['/opt/lampp/lampp', 'stop'])

def white_balance(img):
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    return result

def adjust_color_balance(image, red_gain=1.0, green_gain=1.0, blue_gain=1.0):
    b, g, r = cv2.split(image)
    r = cv2.multiply(r, red_gain)
    g = cv2.multiply(g, green_gain)
    b = cv2.multiply(b, blue_gain)
    return cv2.merge((b, g, r))

def gamma_correction(image, gamma=1.0):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def enhance_contrast(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

def send_notification(message):
    notification.notify(
        title="Detection",
        message=message,
        timeout=5  # Duration in seconds
    )


def get_project_parameters(project_id):
    db_config = {
        'user': 'root',
        'password': 'root',
        'host': 'localhost',
        'database': 'drone',
        'raise_on_warnings': True
    }

    try:
        cnx = connector.connect(**db_config)
        cursor = cnx.cursor(dictionary=True)

        query = "SELECT coordinate FROM project WHERE id = %s"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()

        cursor.close()
        cnx.close()

        if result and 'coordinate' in result:
            coordinate_data = result['coordinate']
            if isinstance(coordinate_data, str):
                # Convert the string to a dictionary
                parameters = eval(coordinate_data)
            elif isinstance(coordinate_data, int):
                # Handle case where coordinates are simple integers
                parameters = {'fly_time': coordinate_data}
            else:
                print(f"Unexpected data type for coordinates: {type(coordinate_data)}")
                return None

            return parameters
        else:
            print(f"No parameters found for project ID {project_id}")
            return None
    except connector.Error as err:
        print(f"Error: {err}")
        return None


# Snap function to save image and save to database
def snap(frame, confidence, x, y, w, h):
    # Save image to a directory served by XAMPP (htdocs)
    snapshot_dir = 'C:\\xampp\\htdocs\\snapshots'  # Adjust the path if needed
    if not os.path.exists(snapshot_dir):
        os.makedirs(snapshot_dir)

    filename = f"human_detected_{time.strftime('%Y%m%d_%H%M%S')}_{confidence:.2f}.jpg"
    filepath = os.path.join(snapshot_dir, filename)
    cv2.imwrite(filepath, frame)
    print(f"Snapshot saved as {filepath}")

    # Encode image to bytes
    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()

    # Draw bounding box on the image
    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    save_to_database(confidence, image_bytes)

    # Generate download link
    download_url = f"http://localhost/snapshots/{filename}"
    print(f"Download URL: {download_url}")
    send_notification(f"Snapshot available at {download_url}")

def save_to_database(confidence, image_bytes):
    # Database connection details
    db_config = {
        'user': 'root',
        'password': '',
        'host': 'localhost',
        'database': 'drone',
        'raise_on_warnings': True
    }

    try:
        cnx = connector.connect(**db_config)
        cursor = cnx.cursor()

        add_detection = ("INSERT INTO img "
                         "(Confidence, SS) "
                         "VALUES (%s, %s)")
        data_detection = (confidence, image_bytes)

        cursor.execute(add_detection, data_detection)
        cnx.commit()

        cursor.close()
        cnx.close()
        print("Detection data saved to database.")
    except connector.Error as err:
        print(f"Error: {err}")

class TelloObstacleAvoidance:
    def __init__(self, tello ):
        self.tello = tello
        self.tello.connect()
        self.tello.streamon()

        # Define parameters for obstacle detection
        self.distance_threshold = 100  # Distance threshold in pixels
        self.movement_speed = 20  # Movement speed of the drone

    def get_frame(self):
        # Get the latest frame from the Tello camera
        frame = self.tello.get_frame_read().frame
        return frame

    def process_frame(self, frame):
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Use Canny edge detection
        edges = cv2.Canny(blur, 50, 150)

        return edges

    def detect_obstacles(self, edges):
        # Detect contours in the edges
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by area
        obstacles = [cnt for cnt in contours if cv2.contourArea(cnt) > 100]

        return obstacles

    def calculate_distance(self, obstacle):
        # Placeholder for distance calculation
        # This should ideally be replaced with a proper distance calculation using camera calibration data
        x, y, w, h = cv2.boundingRect(obstacle)
        distance = 1000 / w  # Simplified distance calculation: inverse of width
        return distance

    def avoid_obstacles(self, obstacles, frame):
        for obstacle in obstacles:
            # Get bounding box of obstacle
            x, y, w, h = cv2.boundingRect(obstacle)

            # Calculate the center of the obstacle
            center_x = x + w // 2
            center_y = y + h // 2

            # Calculate and print the distance of the obstacle
            distance = self.calculate_distance(obstacle)
            print(f"Detected obstacle at distance: {distance:.2f} cm")

            # Draw the bounding box and distance on the frame
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{distance:.2f} cm", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Avoid the obstacle if it is within the distance threshold
            if w > self.distance_threshold or h > self.distance_threshold:
                try:
                    if center_x < 320:
                        # Obstacle on the left, move right
                        self.tello.move_right(self.movement_speed)
                    elif center_x > 320:
                        # Obstacle on the right, move left
                        self.tello.move_left(self.movement_speed)

                    if center_y < 240:
                        # Obstacle above, move down
                        self.tello.move_down(self.movement_speed)
                    elif center_y > 240:
                        # Obstacle below, move up
                        self.tello.move_up(self.movement_speed)
                except TelloException as e:
                    print(f"Error moving drone: {e}")

    def run(self):
        while True:
            # Get the latest frame from the Tello camera
            frame = self.get_frame()

            # Process the frame to detect edges
            edges = self.process_frame(frame)

            # Detect obstacles based on edges
            obstacles = self.detect_obstacles(edges)

            # Avoid detected obstacles
            self.avoid_obstacles(obstacles, frame)

            # Display the frame and edges
            cv2.imshow('Tello Camera', frame)
            cv2.imshow('Edges', edges)

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.tello.end()
        cv2.destroyAllWindows()

def fly(tello, start_time, movements, parameters):
    forward_distance = int(parameters['fly_time'])  # Ensure integer division
    print(f"Navigating with parameter: Forward Distance={forward_distance}")

    planned_movements = [
        ('move_forward', forward_distance),
        ('rotate_clockwise', 90),
        ('move_forward', forward_distance),
        ('rotate_clockwise', 90),
        ('move_forward', forward_distance),
        ('rotate_clockwise', 90),
        ('move_forward', forward_distance),
        ('rotate_clockwise', 90),
    ]

    while True:
        for move, value in planned_movements:
            if move == 'move_forward':
                try:
                    response = tello.move_forward(int(value))
                    if response is None:
                        print(f"Move forward command failed. Retrying...")
                        response = tello.move_forward(int(value))  # Retry the command
                        if response is None:
                            print(f"Second attempt failed. Landing drone...")
                    elif response == 'ok':
                        movements.append(('move_back', value))
                    else:
                        print(f"Unexpected response: {response}. Retrying...")
                except TelloException as e:
                    print(f"TelloException: {e}")
                    tello.land()
                    sys.exit(1)
            elif move == 'rotate_clockwise':
                try:
                    response = tello.rotate_clockwise(value)
                    if response == 'ok':
                        movements.append(('rotate_counter_clockwise', value))
                    else:
                        print(f"Rotation failed with response: {response}. Retrying...")
                except TelloException as e:
                    print(f"TelloException: {e}")
                    tello.land()
                    sys.exit(1)

            elapsed_time = time.time() - start_time
            print(f"Total time flying: {elapsed_time:.2f} seconds")
            time.sleep(1)

def reverse_movements(tello, movements):
    movements.reverse()
    for move in movements:
        if 'forward' in move:
            tello.move_back(20)
        elif 'back' in move:
            tello.move_forward(20)
        elif 'right' in move:
            tello.move_left(20)
        elif 'left' in move:
            tello.move_right(20)
        time.sleep(1)

def start_drone(project_id):
    check_and_start_xampp()

    parameters = get_project_parameters(project_id)

    if parameters:
        tello = Tello()
        obstacle_avoidance = TelloObstacleAvoidance(tello)

        model = YOLO('yolov8n.pt')
        tello.connect()
        tello.takeoff()
        print("Battery:", tello.get_battery())
        tello.streamon()

        start_time = time.time()
        movements = []

        fly_thread = threading.Thread(target=fly, args=(tello, start_time, movements, parameters), daemon=True)
        fly_thread.start()

        seen_person_hashes = set()
        last_notification_time = time.time()  # Track the last notification time

        try:
            while True:
                frame = tello.get_frame_read().frame

                # Apply image processing functions
                frame = white_balance(frame)
                frame = adjust_color_balance(frame, red_gain=1.1, green_gain=1.1, blue_gain=1.0)
                frame = gamma_correction(frame, gamma=1.2)
                frame = enhance_contrast(frame)

                results = model(frame)

                predict_image = results[0].plot()

                current_time = time.time()

                cv2.imshow("Drone Camera", frame)
                cv2.imshow("Prediction", predict_image)

                # Process detection results
                for result in results[0].boxes:
                    if result.cls == 0:  # Assuming class 0 is 'person'
                        confidence = result.conf.item()
                        x1, y1, x2, y2 = map(int, result.xyxy[0])
                        x, y, w, h = x1, y1, x2 - x1, y2 - y1

                        bbox_hash = hashlib.md5(f"{x1}{y1}{x2}{y2}".encode()).hexdigest()

                        if bbox_hash not in seen_person_hashes and (current_time - last_notification_time) > 10:
                            seen_person_hashes.add(bbox_hash)
                            last_notification_time = current_time
                            send_notification(f"Human detected with confidence {confidence:.2f}")
                            snap(frame, confidence, x, y, w, h)

                # Run obstacle avoidance
                obstacle_avoidance.run()

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        except KeyboardInterrupt:
            print("Stopping drone...")
            stop_xampp()
            reverse_movements(tello, movements)

        cv2.destroyAllWindows()
        tello.land()
    else:
        print("Failed to get valid project parameters. Exiting.")
        stop_xampp()

def stop_drone(tello, movements):
    reverse_movements(tello, movements)
    tello.land()
    cv2.destroyAllWindows()
    stop_xampp()