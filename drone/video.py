import cv2
from flask import Blueprint, Response
from drone.config import DEBUG_VIDEO

video_bp = Blueprint("Video BP", __name__)

if DEBUG_VIDEO:
    cap = cv2.VideoCapture(0)

@video_bp.route("/video_feed", endpoint='_video_feed')
def video_feed():
    if not DEBUG_VIDEO:
        from drone.tello import tello
        
        tello_connect_if_not()
        tello.streamon()
    
    def get_frame():
        if DEBUG_VIDEO:
            _, frame = cap.read()
            return frame
        
        frame = tello.get_frame_read().frame
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # TODO: Send predicted image to all connected clients
    def generate():
        while True:
            frame = get_frame()

            success, jpeg = cv2.imencode('.jpg', frame)

            if not success:
                print('[video_feed] Frame Dropped')
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    return Response(generate(),  mimetype="multipart/x-mixed-replace;boundary=frame")

from controller.server import tello_connect_if_not



    