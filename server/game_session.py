'''实现游戏逻辑与服务器的互通'''
from game.game import Game
from game.game import Player as PlayerInGame
from room import Player as PlayerConnection
class GameSession:
    def __init__(
        self, 
        conn_a: PlayerConnection,
        conn_b: PlayerConnection,
    ) -> None:
        self.connections = {
            "A": conn_a,
            "B": conn_b,
        }
        self.game = Game()
