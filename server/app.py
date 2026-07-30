'''
基于FastAPI的WebSocket游戏服务器
运行方式: uvicorn app:app --reload
(需要安装fastapi和uvicorn)
'''
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import json
from room import (
    rooms,
    create_room,
    Player,
)

#创建FastAPI应用实例
app = FastAPI(
    title="WarOfChronos Server",
    version="0.1"
)
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR/"frontend"), name="frontend")
app.mount("/assets", StaticFiles(directory=BASE_DIR/"assets"), name="assets")
#允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储所有WebSocket连接
connections = []

# 首页html内容显示
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
    
    player = Player(websocket)
    try:
        while True:

            data = await websocket.receive_json()

            action = data.get("action")

            

            if action == "create_room":
                room = create_room()
                await room.add_player(player)

                await player.send({
                    "type": "room_created",
                    "room_id": room.room_id,
                })
            elif action == "join_room":
                room_id = data.get("room_id")
                room = rooms.get(room_id)

                if room:
                    if room.is_full():
                        await player.send({
                            "type": "error",
                            "message":"房间已满人"
                        })
                        continue
                    await room.add_player(player)

                    await player.send({
                        "type": "room_joined",
                        "room_id": room.room_id,
                    })
                else:
                    await player.send({
                        "type": "error",
                        "message": "房间不存在"
                    })
                    continue
            elif action == "ready" and room:
                await room.player_ready(player)
    except WebSocketDisconnect:

        connections.remove(websocket)
        if room:
            room.players.remove(player)

            await room.broadcast({
                "type": "opponent_left",
            })
            print(
                "玩家断开连接"
            )