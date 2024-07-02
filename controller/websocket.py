
import asyncio
import os
import socket
import sys
import threading
from typing import Dict
import websockets

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from controller.util import log
from drone.state import connected_clients

message = ""
client = None

async def websocket_handler(websocket: websockets.WebSocketServerProtocol, path):
    global command, message, client
    connected_clients.add(websocket)
    print("[main] New connection: ", websocket.id)
    try:
        while True:
            data = await websocket.recv()
            reply = f"Data received: {data}"
            command = data
            message = data
            client = websocket
            await websocket.send(reply)

    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(e)
    finally:
        connected_clients.remove(websocket)


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

    print("Server started at:")
    local_ip = get_local_ip()
    print(f"Server started at {local_ip}:8765 and is accessible from local network devices")
    for sock in server.sockets:
        host, port = sock.getsockname()[:2]
        print(f"Host: {host}, Port: {port}")
    
    noti_th = threading.Thread(target=lambda: asyncio.run(notification_thread()), daemon=True)
    
    noti_th.start()
    
    await server.wait_closed()
    
    
subscribed_clients: Dict[int, set]
subscribed_clients = {}

async def notification_thread():
    global message, client
    
    l = log('notification')
    
    wait_sec = 0.3
    
    while True:
        
        if not message.startswith('subscribe'):
            await asyncio.sleep(wait_sec)
            continue
            
        project_id = message.split(' ')[1]
        
        clients = subscribed_clients.get(project_id)
        
        
        if not clients:
            subscribed_clients[project_id] = set()
            clients = subscribed_clients.get(project_id)
            
        
        if client in clients:
            await asyncio.sleep(wait_sec)
            continue
        
        subscribed_clients[project_id].add(client)
        l(f'Client {client.id} subscribed to {project_id}')
        print(clients)
        
        await asyncio.sleep(wait_sec)

if __name__ == '__main__':
    asyncio.run(websocket_main())