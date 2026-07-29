from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
from room import (
    rooms,
    create_room,
)

app = FastAPI(
    title="WarOfChronos Server",
    version="0.1"
)

app.mount(
    "/static",
    StaticFiles(
        directory="../frontend",
    ),
    name="static"
)
# 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 当前在线玩家
connections = []

# 测试接口
@app.get("/")
def index():
    return FileResponse(
        "../frontend/index.html"
    )
# WebSocket连接
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket
):

    await websocket.accept()

    room = None

    connections.append(websocket)

    try:
        while True:

            data = await websocket.receive_json()

            action = data.get("action")

            if action == "create_room":
                room = create_room()
                room.add_player(websocket)

                await websocket.send_json({
                    "type": "room_created",
                    "room_id": room.room_id,
                })
            elif action == "join_room":
                room_id = data.get("room_id")
                room = rooms.get(room_id)

                if room:
                    room.add_player(websocket)

                    await websocket.send_json({
                        "type": "room_joined",
                        "room_id": room.room_id,
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": "房间不存在"
                    })
                    continue
            if room and room.is_ready():
                for player in room.players:
                    await player.send_json({
                        "type": "game_start",
                        "room_id": room.room_id,
                    })
    except WebSocketDisconnect:

        connections.remove(websocket)

        room.players.remove(websocket)

        for player in room.players:
            await player.send_json({
                "type": "opponent_left",
            })
        print(
            "玩家断开连接"
        )