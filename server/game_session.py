'''实现游戏逻辑与服务器的互通'''
##############################
#消息格式提醒
#A方总部的id是-1， B方是-2
##############################
from game.game import Game, LogEntry, GameState, HandCard, Battlefield, Frontline
from enum import Enum
from typing import TYPE_CHECKING, Callable, Any, Literal
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
        broadcaster: Callable[[dict[str, Any]], None]
    ) -> None:
        self.connections = {
            "A": conn_a,
            "B": conn_b,
        }
        self.game = Game()
        self.status = SessionState.PLAYING
        self.broadcaster = broadcaster

    async def handle_action(
            self,
            player_side: str,
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
        state_dict: dict[str, Any] = dict()
        if view == 'A':
            state_dict['my_act_point'] = state.playerA.actionPoint
            state_dict["enemy_act_point"] = state.playerB.actionPoint
            state_dict["my_hq"] = state.hqA
            state_dict["enemy_hq"] = state.hqB
            state_dict["my_handcards"] = self.handle_handcards(state.playerA.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerB.handCards)
        else:
            state_dict['my_act_point'] = state.playerB.actionPoint
            state_dict["enemy_act_point"] = state.playerA.actionPoint
            state_dict["my_hq"] = state.hqB
            state_dict["enemy_hq"] = state.hqA
            state_dict["my_handcards"] = self.handle_handcards(state.playerB.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerA.handCards)
        state_dict["cur_bf"] = state.cbf
        state_dict["events"] = state.evt
        state_dict["battlefields"] = self.handle_bf(state.battlefields)
        return json.dumps(state_dict)
if __name__ == "__main__":
    ...
