import asyncio

import sys, os
import threading
from flask import Flask

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from controller.util import log

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


def init_app():
    print(app.url_map)
    app.run(host="0.0.0.0", port=8766, debug=True)    

    

if __name__ == '__main__':
    l = log('web')
    l('Starting server')
    init_app()