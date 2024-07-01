

import sys, os
from flask import Flask

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import controller.routes as routes
from drone.video import video_bp

from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(routes.routes_bp)
app.register_blueprint(video_bp)


CORS(app)


def log(msg, prefix="web"):
    print(f'[{prefix}] ' + msg)


def init_app():
    app.run(host="0.0.0.0", port=8766, debug=True)
    
if __name__ == '__main__':
    log('Starting server')
    init_app()