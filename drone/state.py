from djitellopy import Tello
from flask import Flask

from drone.config import TELLO_HOST

tello = Tello(host=TELLO_HOST)


# websockets
connected_clients = set()

app = Flask("server")

# run on web.py instead of server.py
DEBUG_WEB = True

