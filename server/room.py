'''
房间的管理模块
'''
import random
import string
import asyncio

rooms: dict[str, Room] = {}
class Player:
    """
    将 websocket 封装为 Player 对象，便于管理玩家状态和发送消息
    """
    def __init__(self, websocket):
        self.websocket = websocket
        self.ready = False
        self.room: Room | None = None
    async def send(self, data):
        await self.websocket.send_json(data)
class Room:
    '''
    房间类，管理房间内的玩家和游戏状态
    '''
    def __init__(self, room_id):
        self.room_id = room_id
        self.players: list[Player] = []
        self.state = "WAITING"
        self.countdown_task = None

    async def add_player(self, player: Player):
        self.players.append(player)
        player.room = self
        if self.is_full():
            self.state = "READY_CHECK"

            await self.broadcast({
                "type": "ready_check",
                "countdown": 10
            })

            self.countdown_task = asyncio.create_task(
                self.start_countdown()
            )
    def is_full(self):
        return len(self.players) >= 2

    def all_ready(self):
        return all(player.ready for player in self.players)

    async def broadcast(self, data: dict):
        for player in self.players:
            try:
                await player.send(data)
            except Exception as e:
                print(f"Error sending message to player: {e}")

    async def check_ready(self):
        if not self.is_full():
            self.state = "READY_CHECK"

        self.state = "READY_CHECK"

        await self.broadcast({
            "type": "ready_check",
            "countdown": 10,
        })
    async def player_ready(self,player):

        player.ready=True

        await self.broadcast({
            "type":"player_ready",
            "player_id":id(player),
        })

        if self.all_ready():

            if self.countdown_task:
                self.countdown_task.cancel()

            await self.start_game()

    async def start_game(self):
        if self.state == "IN_PROGRESS":
            return
        self.state = "IN_PROGRESS"
        await self.broadcast({
            "type": "game_start",
            "room_id": self.room_id,
        })

    async def start_countdown(self):
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
        random.choice(string.ascii_uppercase)
        for _ in range(6)
    )

    rooms[room_id] = Room(room_id)
    return rooms[room_id]