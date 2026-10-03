import asyncio
import websockets

async def test():
    async with websockets.connect("ws://127.0.0.1:8000/ws/test") as ws:
        await ws.send("Minbar works")
        print("Connected successfully")

asyncio.run(test())