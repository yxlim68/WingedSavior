import asyncio

import cv2
from djitellopy import Tello
from flask import Response

from drone.state import tello, app


@app.route("/video_feed", endpoint='_video_feed')
def video_feed():
    tello_connect_if_not()
    tello.streamon()

    # TODO: Send predicted image to all connected clients
    def generate():
        while True:
            frame = tello.get_frame_read().frame
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            success, jpeg = cv2.imencode('.jpg', frame)

            if not success:
                print('[video_feed] Frame Dropped')
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    return Response(generate(),  mimetype="multipart/x-mixed-replace;boundary=frame")

from controller.server import tello_connect_if_not
