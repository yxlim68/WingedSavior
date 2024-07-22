from djitellopy import Tello
from drone.config import DEBUG_VIDEO, DEBUG_WEBSOCKET, TELLO_HOST

import subprocess

def kill_process_on_port(port):
    try:
        # Find the process ID (PID) using the specified port
        result = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True)
        result = result.decode('utf-8').strip()
        
        if result:
            # Extract the PID from the result
            pid = result.split()[-1]
            
            # Kill the process using the PID
            subprocess.check_output(f'taskkill /F /PID {pid}', shell=True)
            print(f"Process with PID {pid} on port {port} has been terminated.")
        else:
            print(f"No process is using port {port}.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to kill process on port {port}: {e}")


kill_process_on_port(8889)
tello = Tello()

if DEBUG_WEBSOCKET:
    # tello.RESPONSE_TIMEOUT = 1
    pass
    
    
def tello_connect_if_not():
    try:
        print(f'[Connect Attempt] Drone battery {tello.get_battery()} to check connection')
    except:
        print(f'[Connect Attempt] Drone is not connected. Attempting to connect...')
        tello.connect()
        print(f'[Connect Attempt] Batter is: {tello.get_battery()}%')