import threading
import time

import cv2
from djitellopy import Tello
from ultralytics import YOLO


def adjust_color_balance(image, red_gain, green_gain, blue_gain):
    # Split the image into its component channels
    b, g, r = cv2.split(image)

    # Apply the gain factors
    r = cv2.multiply(r, red_gain)
    g = cv2.multiply(g, green_gain)
    b = cv2.multiply(b, blue_gain)

    # Merge the channels back together
    return cv2.merge((b, g, r))


if __name__ == '__main__':
    tello = Tello()
    model = YOLO('yolov8n.pt')
    tello.connect()

    tello.takeoff()

    print(tello.get_battery())
    tello.streamon()

    def fly():

        while True:
            tello.move_forward(100)
            tello.rotate_clockwise(90)
            time.sleep(1)
        pass

    fly_thread = threading.Thread(target=fly, daemon=True)
    fly_thread.start()

    while True:
        result_frame = tello.get_frame_read()
        frame = result_frame.frame

        # adjusted_image = adjust_color_balance(frame, red_gain=1, green_gain=1.1, blue_gain=0.5)
        adjusted_image = frame

        results = model.track(adjusted_image,persist=True, verbose=True)

        predict_image = results[0].plot()

        print(result_frame.frame)
        cv2.imshow("Drone Camera", adjusted_image)
        cv2.imshow("Prediction", predict_image)

        # print(result)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
