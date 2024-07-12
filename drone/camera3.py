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
from controller.util import log as util_log
from drone.tello import tello
from tello_asyncio import Tello as TelloIO

# Ensure class names from COCO datasets
CLASS_NAMES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "airplane",
    5: "bus",
    6: "train",
    7: "truck",
    8: "boat",
    9: "traffic light",
    10: "fire hydrant",
    11: "stop sign",
    12: "parking meter",
    13: "bench",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    27: "tie",
    28: "suitcase",
    29: "frisbee",
    30: "skis",
    31: "snowboard",
    32: "sports ball",
    33: "kite",
    34: "baseball bat",
    35: "baseball glove",
    36: "skateboard",
    37: "surfboard",
    38: "tennis racket",
    39: "bottle",
    40: "wine glass",
    41: "cup",
    42: "fork",
    43: "knife",
    44: "spoon",
    45: "bowl",
    46: "banana",
    47: "apple",
    48: "sandwich",
    49: "orange",
    50: "broccoli",
    51: "carrot",
    52: "hot dog",
    53: "pizza",
    54: "donut",
    55: "cake",
    56: "chair",
    57: "couch",
    58: "potted plant",
    59: "bed",
    60: "dining table",
    61: "toilet",
    62: "tv",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "cell phone",
    68: "microwave",
    69: "oven",
    70: "toaster",
    71: "sink",
    72: "refrigerator",
    73: "book",
    74: "clock",
    75: "vase",
    76: "scissors",
    77: "teddy bear",
    78: "hair drier",
    79: "toothbrush"
}


def check_and_start_xampp():
    if platform.system() == 'Windows':
        apache_status = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq httpd.exe'], stdout=subprocess.PIPE)
        mysql_status = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq mysqld.exe'], stdout=subprocess.PIPE)

        if b'No tasks' in apache_status.stdout or b'No tasks' in mysql_status.stdout:
            print("Starting XAMPP...")
            subprocess.run(['C:\\xampp\\xampp_start.exe'])
            time.sleep(10)
        else:
            print("XAMPP is already running.")
    else:
        print("Unsupported OS")
        sys.exit(1)


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
        timeout=5
    )


def get_project_parameters(project_id):
    db_config = {
        'user': 'root',
        'password': '',
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
        print("Detection saved to database")
    except connector.Error as err:
        print(f"Error: {err}")


class TelloObstacleAvoidance:
    def __init__(self, tello, distance_threshold=5, movement_speed=20):
        self.tello = tello
        self.distance_threshold = distance_threshold
        self.movement_speed = movement_speed

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
        for obstacle in obstacles:
            x, y, w, h = cv2.boundingRect(obstacle)
            distance = self.distance_threshold * (640 - w) / 640

            center_x = x + w // 2
            center_y = y + h // 2

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{distance:.2f} cm", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            if w > self.distance_threshold or h > self.distance_threshold:
                try:
                    if center_x < 320:
                        time.sleep(1)
                        self.tello.move_right(self.movement_speed)
                    elif center_x > 320:
                        time.sleep(1)
                        self.tello.move_left(self.movement_speed)

                    if center_y < 240:
                        time.sleep(1)
                        self.tello.move_down(self.movement_speed)
                    elif center_y > 240:
                        time.sleep(1)
                        self.tello.move_up(self.movement_speed)
                except TelloException as e:
                    print(f"Error moving drone: {e}")

    def run(self):
        while True:
            frame = self.get_frame()
            edges = self.process_frame(frame)
            obstacles = self.detect_obstacles(edges)
            self.avoid_obstacles(obstacles, frame)

            # cv2.imshow('Tello Camera', frame)
            # cv2.imshow('Edges', edges)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            # time.sleep(1)

        cv2.destroyAllWindows()


def fly(tello, start_time, movements, parameters):
    forward_distance = int(parameters['coordinate'])
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
                        time.sleep(1)
                        print(f"Move forward command failed. Retrying...")
                        response = tello.move_forward(int(value))
                        if response is None:
                            time.sleep(1)
                            print(f"Second attempt failed. Landing drone...")
                    elif response == 'ok':
                        time.sleep(1)
                        movements.append(('move_back', value))
                    else:
                        time.sleep(1)
                        print(f"Unexpected response: {response}. Retrying...")
                except TelloException as e:
                    time.sleep(1)
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
        

def main(tello,model,parameters):
    seen_person_hashes = set()
    last_notification_time = time.time()
    obstacle_avoidance = TelloObstacleAvoidance(tello,distance_threshold=5, movement_speed=20)
    
    try:
        while True:
            frame = tello.get_frame_read().frame

            frame = white_balance(frame)
            frame = adjust_color_balance(frame, red_gain=1.1, green_gain=1.1, blue_gain=1.0)
            frame = gamma_correction(frame, gamma=1.2)
            frame = enhance_contrast(frame)

            results = model(frame)
            predict_image = results[0].plot()
            current_time = time.time()

            cv2.imshow("Drone Camera", frame)
            cv2.imshow("Prediction", predict_image)

            for result in results[0].boxes:
                class_name = CLASS_NAMES[result.cls.item()]

                if parameters['detect'] == 'anything' or parameters['detect'] == class_name:
                    confidence = result.conf.item()
                    x1, y1, x2, y2 = map(int, result.xyxy[0])
                    x, y, w, h = x1, y1, x2 - x1, y2 - y1

                    bbox_hash = hashlib.md5(f"{x1}{y1}{x2}{y2}".encode()).hexdigest()

                    if bbox_hash not in seen_person_hashes and (current_time - last_notification_time) > 10:
                        seen_person_hashes.add(bbox_hash)
                        last_notification_time = current_time
                        send_notification(f"{class_name.capitalize()} detected with confidence {confidence:.2f}")
                        snap(frame, confidence, x, y, w, h)

            obstacle_avoidance.run()
            time.sleep(0.5)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("Stopping drone...")
        
            


def start_drone(tello,project_id):
    global is_flying, is_started,actions
    
    is_started = True
    actions.append('connect')
    actions.append('takeoff')
    actions.append(('forward', 100))
    actions.append( ('cw', 90))
    actions.append(('forward', 100))
    actions.append( ('cw', 90))
    actions.append(('forward', 100))
    actions.append( ('cw', 90))
    actions.append(('forward', 100))
    actions.append( ('cw', 90))

    return
    parameters = get_project_parameters(project_id)

    if parameters:

        model = YOLO('yolov8n.pt')
        # tello.connect()
        # tello.takeoff()
        # print("Battery:", tello.get_battery())
        # tello.streamon()

        start_time = time.time()
        movements = []

        # fly_thread = threading.Thread(target=fly, args=(tello, start_time, movements, parameters), daemon=True)
        # fly_thread.start()

        
        # main_thread = threading.Thread(target=main,args=(tello,model,parameters), daemon=True)
        # main_thread.start()
        

    else:
        print("Failed to get valid project parameters. Exiting.")




def stop_drone(tello, movements, retries=3, delay=5):
    """
    Stop the drone safely with retries.
    """
    
    global is_flying, is_started, actions
    is_started = False
    actions = []
    actions.append('land')
    return
    try:
        tello.send_command_with_return('stop')
        # Stop video stream
        tello.streamoff()
    except TelloException as e:
        print(f"Error stopping video stream: {e}")

    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1} to land the drone.")
            tello.land()
            print('Drone landed successfully.')
            return
        except TelloException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("All attempts to land the drone failed.")
                raise
            

actions = []
planned_movements = [
        ('move_forward', 30),
        ('rotate_clockwise', 90),
        ('move_forward', 30),
        ('rotate_clockwise', 90),
        ('move_forward', 30),
        ('rotate_clockwise', 90),
        ('move_forward', 30),
        ('rotate_clockwise', 90),
    ]

is_started = False
is_flying = False

async def fly_thread():
    global is_flying,actions
    log = util_log('fly')
    tello = TelloIO()
    while True:
        try:
            log('is started: ', is_started, ' | is flying: ', is_flying)
            if len(actions) == 0:
                time.sleep(1)
                continue
            action = actions[0]
            actions = actions[1::]
            log(action, actions)
            
            if action == 'connect':
                await tello.connect()
            
            if action == 'takeoff':
                await tello.takeoff()
                
            if action == 'land':
                await tello.land()
                
            if type(action) is tuple:
                cmd, val = action
                
                log(f'cmd {cmd} {val}')
                
                # send command
                # tello.send_command_with_return(f'{cmd} {val}')
                if cmd == 'forward':
                    await tello.move_forward(val)
                if cmd == 'cw':
                    await tello.turn_clockwise(val)
                pass
            
            
            time.sleep(0.1)
        except Exception as e:
            log('ERROR',e)
            time.sleep(1)