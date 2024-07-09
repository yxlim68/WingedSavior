import os
import sys
import threading
import websockets
import asyncio


sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from controller.websocket import websocket_main
from controller.web import init_app
from drone.tello import tello, tello_connect_if_not
from drone.state import connected_clients

command = ''
is_flying = False


def get_connected_clients() -> set:
    return connected_clients


def flythread():
    global command

    print("[fly] Connecting to tello...")

    tello_connect_if_not()

    tello.takeoff()
    tello.move_forward(100)

    try:
        print('[fly] Waiting command')
        while True:
            if command == '':
                continue

            print('Command: ', command)
            if command == 'stop':
                print('stopping...')
                tello.send_command_with_return('stop')
                break  # exit loop after stop command

    except Exception as e:
        print(f"[fly] Exception in flythread: {e}")
    finally:
        tello.land()
        pass





if __name__ == '__main__':
    
    
    fly_thread = threading.Thread(target=flythread, daemon=True)

    web_thread = threading.Thread(target=init_app, daemon=True)

    web_thread.start()
    
    asyncio.run(websocket_main())

    
