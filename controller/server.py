import websockets
import asyncio

connected_clients = set()

async def handler(websocket: websockets.WebSocketServerProtocol, path):
    connected_clients.add(websocket)
    print("New connection: ", websocket.id)
    try:
        while True:
            data = await websocket.recv()
            reply = f"Data recieved as: {data}"
            print(reply)
            await websocket.send(reply)
        
    except websockets.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(e)
        
        
async def main():
    server = await websockets.serve(handler, host="localhost", port=8765)
    print("Server started at localhost:6969")
    
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())