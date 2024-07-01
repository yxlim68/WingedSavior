from djitellopy import Tello
from drone.config import DEBUG_VIDEO, TELLO_HOST

# TODO: enable debug run caused tello cant instantiate repeatly with same port :(


if DEBUG_VIDEO:
    tello = None
else:
    tello = Tello(host=TELLO_HOST)