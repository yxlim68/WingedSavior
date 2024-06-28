import threading
from djitellopy import Tello
import websockets
import asyncio

from flask import Flask

from drone.state import connected_clients, app
from drone.video import video_feed
from controller.web import login, create_project, get_snapshot

command = ''
is_flying = False

tello = Tello()


def get_connected_clients() -> set:
    return connected_clients


def tello_connect_if_not():
    try:
        print(f'[Connect Attempt] Drone battery {tello.get_battery()} to check connection')
    except:
        print(f'f[Connect Attempt] Drone is not connected. Attempting to connect...')
        tello.connect()
        print(f'f[Connect Attempt] Batter is: {tello.get_battery()}%')


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


async def handler(websocket: websockets.WebSocketServerProtocol, path):
    global command
    connected_clients.add(websocket)
    print("[main] New connection: ", websocket.id)
    try:
        while True:
            print('[main]', connected_clients)
            data = await websocket.recv()
            reply = f"Data received: {data}"
            print(reply)
            command = data
            await websocket.send(reply)

    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(e)
    finally:
        connected_clients.remove(websocket)


async def main():
    server = await websockets.serve(handler, host="localhost", port=8765)
    print("Server started at localhost:8765")
    await server.wait_closed()



def init_app():
    app.run(host="0.0.0.0", port=8766)


if __name__ == '__main__':
    fly_thread = threading.Thread(target=flythread, daemon=True)

    web_thread = threading.Thread(target=init_app, daemon=True)

    web_thread.start()

    asyncio.run(main())
