'''
基于FastAPI的WebSocket游戏服务器
运行方式: uvicorn app:app --reload
(需要安装fastapi和uvicorn)
'''
import asyncio
import secrets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import sys
from .room import (
    rooms,
    create_room,
    Player,
)

#创建FastAPI应用实例
app = FastAPI(
    title="WarOfChronos Server",
    version="0.1"
)
# PyInstaller onefile/onedir 下静态资源在 _MEIPASS 中；源码运行时是项目根目录
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
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
connections: list[WebSocket] = []
# 同一个 client_id 重连时复用 Player 对象，从而复用房间和 GameSession
players: dict[str, Player] = {}

# 首页html内容显示
@app.get("/")
def index():
    return FileResponse(
        BASE_DIR / "frontend" / "index.html" 
    )

async def send_reconnect_state(player: Player) -> None:
    room = player.room
    if room is None:
        await player.send({
            "type": "reconnected",
            "room_id": None,
            "in_game": False,
        })
        return
    await room.player_reconnected(player)
    in_game = room.game_session is not None
    await player.send({
        "type": "reconnected",
        "room_id": room.room_id,
        "in_game": in_game,
        "side": player.side,
        "vs_ai": room.vs_ai,
    })
    if room.game_session is not None:
        if room.game_session.status.name == "FINISHED":
            if player.side is not None:
                await room.game_session.send_game_over_to(player.side)
        elif player.side is not None:
            await room.game_session.send_state_to(player.side)
    else:
        await player.send({
            "type": "room_joined",
            "room_id": room.room_id,
        })

async def heartbeat(websocket: WebSocket, player: Player) -> None:
    try:
        while player.websocket is websocket and player.connected:
            await asyncio.sleep(15)
            await websocket.send_json({"type": "ping"})
    except Exception:
        return

# WebSocket连接
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    client_id = websocket.query_params.get("client_id")
    if not client_id:
        client_id = secrets.token_urlsafe(18)

    player = players.get(client_id)
    reconnecting = player is not None
    if player is None:
        player = Player(websocket, client_id)
        players[client_id] = player
    else:
        old_websocket = player.websocket
        player.websocket = websocket
        player.connected = True
        if player.disconnect_task is not None:
            player.disconnect_task.cancel()
            player.disconnect_task = None
        if old_websocket is not websocket:
            try:
                await old_websocket.close()
            except Exception:
                pass

    connections.append(websocket)
    hb_task = asyncio.create_task(heartbeat(websocket, player))

    if reconnecting:
        await send_reconnect_state(player)

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "pong":
                continue

            room = player.room

            if action == "create_room":
                vs_ai = bool(data.get("vs_ai", False))
                room = create_room(vs_ai)
                await room.add_player(player)

                await player.send({
                    "type": "room_created",
                    "room_id": room.room_id,
                    "vs_ai": vs_ai,
                })
                if vs_ai:
                    await room.start_game()
            elif action == "join_room":
                room_id = data.get("room_id")
                room = rooms.get(room_id)

                if room:
                    if room.vs_ai or room.state == "IN_PROGRESS":
                        await player.send({
                            "type": "error",
                            "message":"房间不可加入"
                        })
                        continue
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
            elif action == "player_operation" and room:
                if room.game_session:
                    await room.game_session.handle_action(
                        player.side,
                        data                
                    )
            else:
                print("无效的操作:", data)
                await player.send({
                    "type": "error",
                    "message": "无效的操作"
                })    
    except WebSocketDisconnect:
        print("玩家断开连接")
    except Exception as err:
        print(f"WebSocket error: {err}")
    finally:
        hb_task.cancel()
        if websocket in connections:
            connections.remove(websocket)
        # 只有当前仍是这个连接时才标记断开；旧连接被新连接替换时不能误伤。
        if player.websocket is websocket:
            if player.room is not None:
                await player.room.player_disconnected(player)
            else:
                players.pop(client_id, None)
