
import asyncio
import time
import hashlib
import json
import os
import socket
import sys
import threading
import websockets

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from drone.location import get_location
from controller.util import log as util_log
from drone.tello import tello

log = util_log('websocket')

MAX_STATE_LIFE = 5000

message = ''
client = None
status = {
    "is_connected": False,
    'is_flying': False,
    "project": 0,
    "drone_state": None,
    "location": None,
}
last_state_hash = (None, )

response_ev = threading.Event()
response_msg = ''

def consume():
    global message
    tmp = message
    message = ''
    
    return tmp

def send_response(msg):
    global response_msg, response_ev
    response_msg = msg
    response_ev.set()
    
def is_flying():
    global status
    return status['is_flying']
    
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


async def websocket_main():
    server = await websockets.serve(websocket_handler, host="0.0.0.0", port=8765)
    
    drone_thread = threading.Thread(target=lambda: asyncio.run(handle_drone_state()), daemon=True)
    drone_thread.start()
    status_thread = threading.Thread(target=lambda: asyncio.run(handle_status()), daemon=True)
    status_thread.start()
    response_thread = threading.Thread(target=lambda: asyncio.run(handle_response()), daemon=True)
    response_thread.start()

    print("Server started at:")
    local_ip = get_local_ip()
    print(f"Server started at {local_ip}:8765 and is accessible from local network devices")
    for sock in server.sockets:
        host, port = sock.getsockname()[:2]
        print(f"Host: {host}, Port: {port}")
    
    
    await server.wait_closed()

async def websocket_handler(websocket: websockets.WebSocketServerProtocol, path):
    global message, client
    log("New connection: ", websocket.id)
    if client:
        await websocket.send("error Another connection already established")
        await websocket.close()
        return
    
    client = websocket
    try:
        while True:
            data = await websocket.recv()
            message = data
            await asyncio.sleep(0.05)

    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(e)
    finally:
        client = None


async def handle_drone_state():
    global message, tello, status
    log = util_log('drone')
    log('Drone thread start')
    
    while True:
        try:
            # if message == "connect":
            #     log(f"{message} command received. Attempting to connect to drone")
            #     consume()
            #     # connect to drone
            #     try:
            #         tello.connect()
            #     except:
            #         pass
                
            #     if not tello.get_current_state():
            #         send_response(f'connect failed')
            #     else:
            #         status['is_connected'] = True
            #         send_response('connect success')
                    
            # elif message == 'takeoff':
            #     log(f'command {message}')
            #     msg = consume()
                
            #     if status['is_connected'] == False:
            #         send_response(f'{msg} failed Drone is connected yet!')
            #     else:
            #         tello.takeoff()
                    
            #         status['is_flying'] = tello.is_flying
            #         send_response(f'{msg} success')
                
            # elif message == 'up':
            #     msg = consume()
                
            #     if not is_flying():
            #         send_response(f'{msg} failed Drone is not flying')
            #     else:
            #         send_response(f'{msg} success')
            if message == "connect":
                log(f"{message} command received. Attempting to connect to drone")
                consume()
                # connect to drone
                try:
                    tello.connect()
                except Exception as e:
                    log(f"Error connecting to drone: {e}")
                    send_response(f'connect failed: {e}')
                    continue
                
                if not tello.get_current_state():
                    send_response(f'connect failed')
                else:
                    status['is_connected'] = True
                    send_response('connect success')
                    
            elif message == 'takeoff':
                log(f'command {message}')
                msg = consume()
                
                if status['is_connected'] == False:
                    send_response(f'{msg} failed: Drone is not connected yet!')
                else:
                    try:
                        tello.takeoff()
                        status['is_flying'] = tello.is_flying
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error during takeoff: {e}")
                        send_response(f'{msg} failed: {e}')
                
            elif message == 'land':
                log(f'command {message}')
                msg = consume()
                
                if not is_flying():
                    send_response(f'{msg} failed: Drone is not flying')
                else:
                    try:
                        tello.land()
                        status['is_flying'] = False
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error during landing: {e}")
                        send_response(f'{msg} failed: {e}')
                        
            elif message == "stop":
                log(f'command {message}')
                msg = consume()
                
                tello.send_command_with_return('stop')
                
                send_response(f"{msg} success ")
                
            elif message == 'up':
                msg = consume()
                
                if not is_flying():
                    send_response(f'{msg} failed: Drone is not flying')
                else:
                    try:
                        tello.move_up(20)
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error moving up: {e}")
                        send_response(f'{msg} failed: {e}')
                
            elif message == 'down':
                msg = consume()
                
                if not is_flying():
                    send_response(f'{msg} failed: Drone is not flying')
                else:
                    try:
                        tello.move_down(20)
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error moving down: {e}")
                        send_response(f'{msg} failed: {e}')
                
            elif message == 'forward':
                msg = consume()
                
                if not is_flying():
                    send_response(f'{msg} failed: Drone is not flying')
                else:
                    try:
                        tello.send_command_without_return("forward 500")
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error moving forward: {e}")
                        send_response(f'{msg} failed: {e}')
                
            elif message == 'back':
                msg = consume()
                
                if not is_flying():
                    send_response(f'{msg} failed: Drone is not flying')
                else:
                    try:
                        tello.move_back(100)
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error moving back: {e}")
                        send_response(f'{msg} failed: {e}')
                
            elif message == 'left':
                msg = consume()
                
                if not is_flying():
                    send_response(f'{msg} failed: Drone is not flying')
                else:
                    try:
                        tello.move_left(20)
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error moving left: {e}")
                        send_response(f'{msg} failed: {e}')
                
            elif message == 'right':
                msg = consume()
                
                if not is_flying():
                    send_response(f'{msg} failed: Drone is not flying')
                else:
                    try:
                        tello.move_right(20)
                        send_response(f'{msg} success')
                    except Exception as e:
                        log(f"Error moving right: {e}")
                        send_response(f'{msg} failed: {e}')
               
                
        except Exception as e:
            log(e)
        
        await asyncio.sleep(0.05)
        
async def handle_status():
    global message, client,status, last_state_hash
    log = util_log('status')
    log('Status thread started')
    while True:
        
        # get location
        curr_location = get_location()
        if curr_location is not None:
            curr_location = curr_location.decode('utf-8')
            curr_location = json.loads(curr_location)
            
            # check if value is 0            
            if curr_location['lat'] != 0 and curr_location['lng'] != 0:
                status['location'] = curr_location
                # log(curr_location)
            else:
                status['location'] = None
            
        else:
            status['location'] = None
                
                
                
        curr_drone_state = tello.get_current_state()
        
        if not curr_drone_state:
            curr_drone_state = None
        
        curr_hash = hashlib.md5(json.dumps(curr_drone_state, sort_keys=True).encode()).hexdigest()
        # log(curr_hash, last_state_hash[0])
        
        if curr_hash == last_state_hash[0]:
            if time.time()* 1000 - last_state_hash[1]  > MAX_STATE_LIFE:
                status['drone_state'] = None
        else:
            last_state_hash = (curr_hash, time.time() * 1000)
            status['drone_state'] = curr_drone_state
            
        
        # log(status)
        if client is not None:
            await client.send(f'status {json.dumps(status, sort_keys=True)}')
    
        
        await asyncio.sleep(1)
        
async def handle_response():
    
    global response_ev, response_msg, client
    log = util_log('response')
    
    while True:
        response_ev.wait()
        
        if client is None:
            log('[warn] No client is found. Skipping..!')
            continue
        
        log(f'sending "{response_msg}" to client')
        await client.send(response_msg)
        response_ev.clear()

if __name__ == '__main__':
    
    
    
    
    asyncio.run(websocket_main())