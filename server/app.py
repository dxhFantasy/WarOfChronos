from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json


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

    connections.append(websocket)


    try:

        while True:

            # 接收客户端消息
            data = await websocket.receive_json()


            print(
                "收到消息:",
                data
            )


            # 测试广播
            for conn in connections:

                await conn.send_json({

                    "type":
                    "message",

                    "data":
                    data

                })


    except WebSocketDisconnect:

        connections.remove(websocket)

        print(
            "玩家断开连接"
        )