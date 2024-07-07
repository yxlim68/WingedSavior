import datetime
import time
import cv2
from flask import Blueprint, Response, request
from controller.db import db
from controller.util import log as util_log
from drone.config import DEBUG_VIDEO
from drone.detection import detect_person
from drone.location import get_location
from drone.yolo import model



video_bp = Blueprint("Video BP", __name__)

if DEBUG_VIDEO:
    cap = cv2.VideoCapture(0)

@video_bp.route("/video_feed")
def video_feed():
    global latest_frame, project
    project_id = request.args.get('project')
    
        
    if not project_id:
        return {"message": "Please provide project id"}, 400
    
    if not DEBUG_VIDEO:
        from drone.tello import tello, tello_connect_if_not
        
        tello_connect_if_not()
        tello.streamon()
        
       
    
    def get_frame():
        if DEBUG_VIDEO:
            _, frame = cap.read()
            return frame
        
        frame = tello.get_frame_read().frame
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # keep tracked objects ids to prevent spamming database with images
    tracked_objects = list()
    
    project = project_id

    # TODO: Send predicted image to all connected clients
    def generate():
        while True:
            
            if latest_frame is None:
                time.sleep(0.1)
                continue
            
            

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_frame.tobytes() + b'\r\n\r\n')

    return Response(generate(),  mimetype="multipart/x-mixed-replace;boundary=frame")


def upload_image( project_id: int, id: int, image_bytes, conf: float):
    
    current_location = get_location()
    
    img_query = "INSERT INTO img (project_id, SS, Confidence, location) VALUES (%s,%s, %s, %s)"
    noti_query = "INSERT INTO notification (project_id, img_id) VALUES (%s,%s)"
    
    try:
        _, cur = db()
        
        print("updating db")
        cur.execute(img_query, (project_id, image_bytes, conf,  current_location if current_location is not None else None))

        img_id = cur.lastrowid
        
        cur.execute(noti_query, (project_id, img_id))
        
        cur.execute('commit')
        
    except Exception as e:
        print(e)
        

latest_frame = None
tracked_objects = list()
project = None
video_start = False

def start_video_thread():
    global latest_frame, tracked_objects, project, video_start
    
    log = util_log('video')
    
    if DEBUG_VIDEO:
        cap = cv2.VideoCapture(0)
    
    if not DEBUG_VIDEO:
        from drone.tello import tello, tello_connect_if_not
        
        tello_connect_if_not()
        tello.streamon()
     
    def get_frame():
        if DEBUG_VIDEO:
            _, frame = cap.read()
            return frame
        
        frame = tello.get_frame_read().frame
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    while True:
        # log('frame: ', latest_frame)
        # log(f'project: {project}')
        frame = get_frame()
        
        results = model.track(frame, persist=True, classes=0, verbose=False)

        person_detected = detect_person(results[0])

        if person_detected:
            output = results[0].plot() 
        else:
            output = frame

        success, jpeg = cv2.imencode('.jpg', output)
        
        if person_detected:
            boxes = results[0].boxes
            print(tracked_objects)
            for box in boxes:
                if not box:
                    continue
                if box.id in tracked_objects:
                    continue
                
                tracked_objects.append(box.id.item())
                
                # send notification
                if project:
                    upload_image(project, box.id, jpeg.tobytes(), box.conf.item())


        if not success:
            print('[video_feed] Frame Dropped')
            continue
        latest_frame = jpeg
        video_start = True
