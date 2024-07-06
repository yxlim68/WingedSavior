import time
import cv2
from djitellopy import Tello
import numpy as np

def detect_close_obstacle(frame, area_threshold=2000, proximity_threshold=100):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    height, width = frame.shape[:2]
    roi_top_left = (width // 4, height // 4)
    roi_bottom_right = (3 * width // 4, 3 * height // 4)

    cv2.rectangle(frame, roi_top_left, roi_bottom_right, (0, 255, 0), 2)

    for contour in contours:
        if cv2.contourArea(contour) > area_threshold:
            x, y, w, h = cv2.boundingRect(contour)
            if (roi_top_left[0] < x < roi_bottom_right[0] and
                roi_top_left[1] < y < roi_bottom_right[1]):
                if h > proximity_threshold or w > proximity_threshold:
                    return True
    return False

def execute_command(tello, command, retries=3):
    for _ in range(retries):
        try:
            response = command()
            if response == 'ok':
                return True
        except Exception as e:
            print(f"Command failed: {e}")
        time.sleep(2)
    return False

def avoid_obstacle(tello):
    print("Close obstacle detected! Moving back...")
    if execute_command(tello, lambda: tello.move_back(20)):
        print("Moved back successfully.")
        if execute_command(tello, lambda: tello.move_left(20)):
            print("Moved left successfully.")
        elif execute_command(tello, lambda: tello.move_right(20)):
            print("Moved right successfully.")
    else:
        print("Failed to move back.")

if __name__ == '__main__':
    tello = Tello()
    tello.connect()

    print(tello.get_battery())

    try:
        if execute_command(tello, tello.takeoff):
            print("Battery:", tello.get_battery())
            tello.streamon()

            while True:
                result_frame = tello.get_frame_read()
                frame = result_frame.frame

                cv2.imshow("Drone Camera", frame)

                if detect_close_obstacle(frame):
                    avoid_obstacle(tello)
                else:
                    print("No close obstacle detected. Moving forward...")
                    if execute_command(tello, lambda: tello.move_forward(20)):
                        print("Moved forward successfully.")
                    else:
                        print("Failed to move forward.")
                    time.sleep(2)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        else:
            print("Failed to take off.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cv2.destroyAllWindows()
        execute_command(tello, tello.land)
        tello.streamoff()
