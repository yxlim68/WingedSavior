from flask import Flask
import controller.routes as routes
import drone.video as video_route

from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(routes.routes_bp)
app.register_blueprint(video_route.video_bp)

print(app.url_map)

CORS(app)


def log(msg, prefix="web"):
    print(f'[{prefix}] ' + msg)


def init_app():
    app.run(host="0.0.0.0", port=8766)
    
if __name__ == '__main__':
    log('Starting server')
    init_app()