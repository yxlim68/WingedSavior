import asyncio

import sys, os
from flask import Flask

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from controller.util import log

import controller.routes as routes
from drone.video import video_bp
from drone.location import location_bp

from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(routes.routes_bp)
app.register_blueprint(video_bp)
app.register_blueprint(location_bp)

CORS(app)

def init_app():
    print(app.url_map)
    app.run(host="0.0.0.0", port=8766, debug=True)    
    

if __name__ == '__main__':
    l = log('web')
    l('Starting server')
    init_app()