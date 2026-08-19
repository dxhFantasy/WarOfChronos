'''实现游戏逻辑与服务器的互通'''
##############################
#消息格式提醒
#A方总部的id是-1， B方是-2(对于Card而言)
##############################
from game.game import (
    Game, 
    LogEntry, 
    GameState, 
    HandCard, 
    Battlefield, 
    Frontline, 
    Unit
)
from enum import Enum
from typing import TYPE_CHECKING, Callable, Any, Literal
from typing import Coroutine
import json
if TYPE_CHECKING:
   from room import Player as PlayerConnection
class SessionState(Enum):
    PLAYING = "playing"
    FINISHED = "finished"
class GameSession:
    def __init__(
        self, 
        conn_a: PlayerConnection,
        conn_b: PlayerConnection,
        broadcaster: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]
    ) -> None:
        self.connections: dict[Literal["A", "B"], PlayerConnection] = {
            "A": conn_a,
            "B": conn_b,
        }
        self.game = Game()
        self.status = SessionState.PLAYING
        self.broadcaster = broadcaster

    async def handle_action(
            self,
            player_side: Literal["A", "B"],
            record: LogEntry
    ):
        ...
    def handle_handcards(self, handcards: list[HandCard]) -> list[dict[str, Any]]:
        l = []
        for hc in handcards:
            l.append({
                "cost": hc.cost,
                "id": hc.id,
                "extTags": hc.extraTags
            })
        return l
    def handle_units(self, units: list[Unit]) -> list[dict[str, Any]]:
        l = []
        for u in units:
            l.append({
                "id": u.id,
                "cardId": u.cardId,
                "atk": u.atk,
                "dfns": u.dfns,
                "cost": u.cost,
                "actionCost": u.actionCost,
                "tags": [t.keyword.value for t in u.tags],
                "uType": u.uType,
                "utl": u.utl
            })
        return l
    def handle_frontlines(self, frontlines: list[Frontline]):
        l = []
        for fl in frontlines:
            l.append({
                "maxTargets" : fl.maxTargets,
                "targets" : fl.targets
            })
        return l
    def handle_bf(self, bf: list[Battlefield]):
        l = []
        for i in bf:
            l.append({
                "frontlines" : self.handle_frontlines(i.frontlines),
                "unitsNum" : i.unitsNum
            })
        return l
    def state_jsonify(
        self,
        state: GameState,
        view: Literal["A", "B"]
    ):
        print(state.playerA.handCards, state.playerB.handCards)
        state_dict: dict[str, Any] = dict()
        if view == 'A':
            state_dict['my_act_point'] = state.playerA.actionPoint
            state_dict["enemy_act_point"] = state.playerB.actionPoint
            state_dict["my_hq"] = state.playerA.hq
            state_dict["enemy_hq"] = state.playerB.hq
            state_dict["my_handcards"] = self.handle_handcards(state.playerA.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerB.handCards)
        else:
            state_dict['my_act_point'] = state.playerB.actionPoint
            state_dict["enemy_act_point"] = state.playerA.actionPoint
            state_dict["my_hq"] = state.playerB.hq
            state_dict["enemy_hq"] = state.playerA.hq
            state_dict["my_handcards"] = self.handle_handcards(state.playerB.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerA.handCards)
        state_dict["cur_bf"] = state.cbf
        state_dict["events"] = state.evt
        state_dict["battlefields"] = self.handle_bf(state.battlefields)
        state_dict["type"] = "update_state"
        print(view,"state_dict:", state_dict)
        return state_dict
    async def broadcast_state(self):
        state = self.game.GetState()
        await self.connections["A"].send(
            self.state_jsonify(state, "A")
        )
        await self.connections["B"].send(
            self.state_jsonify(state, "B")
        )
    async def broadcast_message(self, message: dict[str, Any]):
        await self.broadcaster(message)
    async def start_game(self):
        print("Game session started.")
        print(f"{self.broadcaster}")
        await self.broadcast_message({
            "type": "show_message",
            "message": "第 1 回合"
        })
        self.game.InitDraw()
        await self.broadcast_state()
    
if __name__ == "__main__":
    ...
