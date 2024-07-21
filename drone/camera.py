import time
import cv2
import numpy as np
from djitellopy import Tello, TelloException
from plyer import notification
import os
import mysql.connector as connector

# Ensure class names from COCO datasets
CLASS_NAMES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
    14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
    20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe", 24: "backpack",
    25: "umbrella", 26: "handbag", 27: "tie", 28: "suitcase", 29: "frisbee",
    30: "skis", 31: "snowboard", 32: "sports ball", 33: "kite", 34: "baseball bat",
    35: "baseball glove", 36: "skateboard", 37: "surfboard", 38: "tennis racket",
    39: "bottle", 40: "wine glass", 41: "cup", 42: "fork", 43: "knife",
    44: "spoon", 45: "bowl", 46: "banana", 47: "apple", 48: "sandwich",
    49: "orange", 50: "broccoli", 51: "carrot", 52: "hot dog", 53: "pizza",
    54: "donut", 55: "cake", 56: "chair", 57: "couch", 58: "potted plant",
    59: "bed", 60: "dining table", 61: "toilet", 62: "tv", 63: "laptop",
    64: "mouse", 65: "remote", 66: "keyboard", 67: "cell phone", 68: "microwave",
    69: "oven", 70: "toaster", 71: "sink", 72: "refrigerator", 73: "book",
    74: "clock", 75: "vase", 76: "scissors", 77: "teddy bear", 78: "hair drier",
    79: "toothbrush"
}


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
        timeout=5
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

        query = "SELECT coordinate, detect FROM project WHERE id = %s"
        cursor.execute(query, (project_id,))
        result = cursor.fetchone()

        cursor.close()
        cnx.close()

        if result:
            parameters = {'coordinate': result.get('coordinate'), 'detect': result.get('detect')}
            return parameters
        else:
            print(f"No parameters found for project ID {project_id}")
            return None
    except connector.Error as err:
        print(f"Error: {err}")
        return None


def snap(frame, confidence, x, y, w, h):
    snapshot_dir = 'C:\\xampp\\htdocs\\snapshots'
    if not os.path.exists(snapshot_dir):
        os.makedirs(snapshot_dir)

    filename = f"detected_{time.strftime('%Y%m%d_%H%M%S')}_{confidence:.2f}.jpg"
    filepath = os.path.join(snapshot_dir, filename)
    cv2.imwrite(filepath, frame)
    print(f"Snapshot saved as {filepath}")

    _, buffer = cv2.imencode('.jpg', frame)
    image_bytes = buffer.tobytes()

    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    save_to_database(confidence, image_bytes)

    download_url = f"http://localhost/snapshots/{filename}"
    print(f"Download URL: {download_url}")
    send_notification(f"Snapshot available at {download_url}")


def save_to_database(confidence, image_bytes):
    db_config = {
        'user': 'root',
        'password': 'root',
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
        print("Detection saved to database")
    except connector.Error as err:
        print(f"Error: {err}")


class TelloObstacleAvoidance:
    def __init__(self, tello, distance_threshold=70, movement_speed=20):
        self.tello = tello
        self.distance_threshold = distance_threshold
        self.movement_speed = movement_speed
        self.cooldown_time = 25  # Cooldown period in seconds
        self.last_avoidance_time = 0

    def get_frame(self):
        frame = self.tello.get_frame_read().frame
        return cv2.resize(frame, (640, 480))

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        return edges

    def detect_obstacles(self, edges):
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def avoid_obstacles(self, obstacles, frame):
        global actions
        current_time = time.time()
        if current_time - self.last_avoidance_time < self.cooldown_time:
            return

        for obstacle in obstacles:
            x, y, w, h = cv2.boundingRect(obstacle)
            distance = self.distance_threshold * (640 - w) / 640

            center_x = x + w // 2
            center_y = y + h // 2

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{distance:.2f} cm", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if w > self.distance_threshold or h > self.distance_threshold:
                try:
                    if center_x < 100:
                        actions = [('right', self.movement_speed), *actions]
                    elif center_x > 540:
                        actions = [('left', self.movement_speed), *actions]
                    if center_y < 100:
                        actions = [('down', self.movement_speed), *actions]
                    elif center_y > 380:
                        actions = [('up', self.movement_speed), *actions]
                    self.last_avoidance_time = current_time
                except TelloException as e:
                    print(f"Error moving drone: {e}")

    def run(self):
        frame = self.get_frame()
        edges = self.process_frame(frame)
        obstacles = self.detect_obstacles(edges)
        self.avoid_obstacles(obstacles, frame)

        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.tello.end()
            cv2.destroyAllWindows()
            return False  # To stop the loop

        return True  # To continue the loop


def create_distance_chunks(distance):
    SIZE = 40  # maximum 20 size

    fit_chunk = distance // SIZE
    remainder = distance % SIZE

    result = [*[SIZE for i in range(fit_chunk)], remainder]

    # remove anything with 0
    result = list(filter(lambda c: c != 0, result))

    return result


def create_commands(cmd, values):
    result = list()
    for value in values:
        result.append((cmd, value))

    return result


def start_drone(tello, project_id):
    global actions
    global loopActions

    parameters = get_project_parameters(project_id)
    forward_distance = int(parameters['coordinate'])

    # create chunks of forward commands to prevent running into wall
    forward_chunks = create_distance_chunks(forward_distance)
    forward_distances = create_commands('forward', forward_chunks)

    print(f"Navigating with parameter: Forward Distance={forward_distance}")
    print(forward_distances)

    actions = [
        'connect',
        'takeoff',
        *forward_distances,
        ('ccw', 90),
        *forward_distances,
        ('ccw', 90),
        *forward_distances,
        ('ccw', 90),
        *forward_distances,
        ('ccw', 90),
    ]

    loopActions = [
        *forward_distances,
        ('ccw', 90),
        *forward_distances,
        ('ccw', 90),
        *forward_distances,
        ('ccw', 90),
        *forward_distances,
        ('ccw', 90),
    ]


def stop_drone(tello, movements):
    global actions
    actions = ['land']
    return


def add_actions(_actions, first=False):
    global actions

    if first:
        actions = [*_actions, *actions]
    else:
        actions = [*actions, *_actions]


actions = list()
loopActions = list()  # Add this line to define loopActions globally


def fly_thread(tello: Tello):
    global actions
    global loopActions
    last_no_command = None

    while True:
        try:
            if len(actions) == 0:
                if last_no_command is None:
                    last_no_command = time.time()

                if time.time() - last_no_command > 5:
                    last_no_command = None
                    actions = loopActions.copy()  # Reset actions to loopActions

                time.sleep(0.1)
                continue

            action = actions[0]
            actions = actions[1:]

            if action == 'connect':
                tello.connect()

            if action == 'takeoff':
                tello.takeoff()

            if action == 'land':
                tello.land()

            if action == 'streamon':
                tello.streamon()

            if action == 'motoron':
                tello.turn_motor_on()

            if type(action) is tuple:
                cmd, val = action
                tello.send_control_command(f'{cmd} {val}')
                time.sleep(2)  # Allow some time for the command to execute

        except Exception as e:
            print(f"Exception in fly_thread: {e}")
            time.sleep(0.1)
