from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

rooms = {}


@router.websocket("/ws/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: str):
    await websocket.accept()

    if room_id not in rooms:
        rooms[room_id] = []

    rooms[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            for connection in rooms[room_id]:
                if connection != websocket:
                    await connection.send_text(data)

    except WebSocketDisconnect:
        rooms[room_id].remove(websocket)

        if not rooms[room_id]:
            del rooms[room_id]