import asyncio

import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import threading
from flask import Flask
from drone.tello import tello
from drone.camera import fly_thread
import controller.routes as routes
from drone.video import start_video_thread, video_bp
from drone.location import location_bp

from flask_cors import CORS


app = Flask(__name__)
app.register_blueprint(routes.routes_bp)
app.register_blueprint(video_bp)
app.register_blueprint(location_bp)

CORS(app)

@app.before_request
def init_components():
    app.before_request_funcs[None].remove(init_components)
    
    video_thread = threading.Thread(target=start_video_thread, daemon=True)
    video_thread.start()
    
    # asyncio.run(fly_thread())
    f_thread = threading.Thread(target=fly_thread,args=(tello,), daemon=True)
    f_thread.start()


def init_app():
    print(app.url_map)
    app.run(host="0.0.0.0", port=8766)    

    

if __name__ == '__main__':
    init_app()