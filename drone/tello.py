from djitellopy import Tello
from drone.config import DEBUG_VIDEO, TELLO_HOST

# TODO: enable debug run caused tello cant instantiate repeatly with same port :(


if DEBUG_VIDEO:
    tello = None
else:
    tello = Tello(host=TELLO_HOST)
    
    
def tello_connect_if_not():
    try:
        print(f'[Connect Attempt] Drone battery {tello.get_battery()} to check connection')
    except:
        print(f'f[Connect Attempt] Drone is not connected. Attempting to connect...')
        tello.connect()
        print(f'f[Connect Attempt] Batter is: {tello.get_battery()}%')