import random
import string

rooms: dict[int, Room] = {}

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        self.players = []

    def add_player(self, websocket):
        self.players.append(websocket)

    def is_ready(self):
        return len(self.players) >= 2

def create_room() -> Room:
    room_id = "".join(
        random.choice(string.ascii_uppercase)
        for _ in range(6)
    )

    rooms[room_id] = Room(room_id)
    return rooms[room_id]