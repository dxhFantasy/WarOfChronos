'''
房间的管理模块
'''
from __future__ import annotations
import random
import asyncio
from .game_session import GameSession
from fastapi import WebSocket
from typing import Any, Literal

rooms: dict[str, Room] = {}
class Player:
    """
    将 websocket 封装为 Player 对象，便于管理玩家状态和发送消息
    """
    def __init__(self, websocket: WebSocket) -> None:
        self.websocket: WebSocket = websocket
        self.ready: bool = False
        self.room: Room | None = None
        self.side: Literal["A", "B"] | None = None  # 玩家在房间中的位置，"A" 或 "B"
    async def send(self, data: dict[str, Any]) -> None:
        await self.websocket.send_json(data)
class Room:
    '''
    房间类，管理房间内的玩家和游戏状态
    '''
    def __init__(self, room_id: str) -> None:
        self.room_id: str = room_id
        self.players: list[Player] = []
        self.state: str = "WAITING"
        self.countdown_task: asyncio.Task[None] | None = None
        self.game_session: GameSession | None = None

    async def add_player(self, player: Player) -> None:
        self.players.append(player)
        player.room = self
        if len(self.players) == 1:
            player.side = "A"
        elif len(self.players) == 2:
            player.side = "B"
        if self.is_full():
            self.state = "READY_CHECK"

            await self.broadcast({
                "type": "ready_check",
                "countdown": 10
            })

            self.countdown_task = asyncio.create_task(
                self.start_countdown()
            )
    def is_full(self) -> bool:
        return len(self.players) >= 2

    def all_ready(self) -> bool:
        return all(player.ready for player in self.players)

    async def broadcast(self, data: dict[str, Any]) -> None:
        for player in self.players:
            try:
                await player.send(data)
            except Exception as e:
                print(f"Error sending message to player: {e}")

    async def check_ready(self) -> None:
        if not self.is_full():
            self.state = "READY_CHECK"

        self.state = "READY_CHECK"

        await self.broadcast({
            "type": "ready_check",
            "countdown": 10,
        })
    async def player_ready(self, player: Player) -> None:

        player.ready=True

        await self.broadcast({
            "type":"player_ready",
            "player_id":id(player),
        })

        if self.all_ready():

            if self.countdown_task:
                self.countdown_task.cancel()

            await self.start_game()

    async def start_game(self) -> None:
        if self.state == "IN_PROGRESS":
            return
        self.state = "IN_PROGRESS"

        self.game_session = GameSession(
            self.players[0],
            self.players[1],
            self.broadcast
        )
        await self.broadcast({
            "type": "game_start",
            "room_id": self.room_id,
        })
        await self.game_session.start_game()

    async def start_countdown(self) -> None:
        try:
            countdown = 10
            while countdown > 0:
                await self.broadcast({
                    "type": "update_countdown",
                    "countdown": countdown,
                })
                await asyncio.sleep(1)
                countdown -= 1
            await self.start_game()
        except asyncio.CancelledError:
            pass
def create_room() -> Room:
    room_id = "".join(
        str(random.choice(list(range(10))))
        for _ in range(6)
    )

    rooms[room_id] = Room(room_id)
    return rooms[room_id]