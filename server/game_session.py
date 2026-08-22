'''实现游戏逻辑与服务器的互通'''
##############################
#消息格式提醒
#A方总部的id是-1， B方是-2(对于Card而言)
##############################
from __future__ import annotations
from game.game import (
    Game, 
    LogEntry, 
    GameState, 
    HandCard, 
    Battlefield, 
    Frontline, 
    Unit,
    ActionType
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
            player_side: Literal["A", "B"] | None,
            data: dict[str, Any]
    ):
        if not player_side: return
        state = self.game.GetState()
        if self.status != SessionState.PLAYING:
            await self.connections[player_side].send({
                "type": "error",
                "message": "游戏未开始或已结束"
            })
            return
        entry: LogEntry | None = None
        if player_side == "A" and self.game.totalTurn % 2 == 0:
            await self.connections[player_side].send({
                "type": "error",
                "message": "当前不是你的回合"
            })
            return
        if player_side == "B" and self.game.totalTurn % 2 == 1:
            await self.connections[player_side].send({
                "type": "error",
                "message": "当前不是你的回合"
            })
            return
        if data.get("op_type", None) == "deploy_unit":
            card_index = data.get("card_index", None)
            if card_index is None:
                await self.connections[player_side].send({
                    "type": "error",
                    "message": "缺少必要参数"
                })
                return
            entry = LogEntry(
                TurnNumber=self.game.totalTurn,
                actorPlayer=player_side,
                actionType=ActionType.Deploy,
                actorId=state.playerA.handCards[card_index].id if player_side == "A" else state.playerB.handCards[card_index].id,
                target=0 if player_side == "A" else 2,
                handCardIdx=card_index
            )
        elif data.get("op_type", None) == "end_turn":
            self.game.TurnEnd(player_side)
            self.game.totalTurn += 1
            await self.broadcast_turn()
            await self.broadcast_state()
            return
        elif data.get("op_type", None) == "use_card":
            card_index: int = data.get("card_index", None)
            if card_index is None:
                await self.connections[player_side].send({
                    "type": "error",
                    "message": "缺少必要参数"
                })
                return
            entry = LogEntry(
                self.game.totalTurn,
                actorPlayer=player_side,
                actionType=ActionType.UseCommand,
                actorId=state.playerA.handCards[card_index].id if player_side == "A" else state.playerB.handCards[card_index].id,
                target=None,
                handCardIdx=card_index
            )
        else:
            await self.connections[player_side].send({
                "type": "error",
                "message": "未知的操作类型"
            })
            return
        result = self.game.ProcessRecord(entry)
        if result.state == "ok":
            await self.broadcast_state()
        else:
            await self.connections[player_side].send({
                "type": "error",
                "message": result.msg
            })
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
                "uType": (u.uType.name, u.uType.value),
                "utl": u.utl
            })
        return l
    def handle_frontlines(self, frontlines: list[Frontline], view: Literal['A', 'B']):
        l = []
        for fl in frontlines:
            l.append({
                "maxTargets" : fl.maxTargets,
                "targets" : self.handle_units(fl.targets)
            })
        l.reverse() if view == "B" else None
        return l
    def handle_bf(self, bf: list[Battlefield], view: Literal['A', 'B']):
        l = []
        for i in bf:
            l.append({
                "frontlines" : self.handle_frontlines(i.frontlines, view),
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
            state_dict["my_hq"] = state.playerA.hq
            state_dict["enemy_hq"] = state.playerB.hq
            state_dict["my_handcards"] = self.handle_handcards(state.playerA.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerB.handCards)
            state_dict["my_deck_cnts"] = len(state.playerA.deck)
            state_dict["enemy_deck_counts"] = len(state.playerB.deck)
        else:
            state_dict['my_act_point'] = state.playerB.actionPoint
            state_dict["enemy_act_point"] = state.playerA.actionPoint
            state_dict["my_hq"] = state.playerB.hq
            state_dict["enemy_hq"] = state.playerA.hq
            state_dict["my_handcards"] = self.handle_handcards(state.playerB.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerA.handCards)
            state_dict["my_deck_cnts"] = len(state.playerB.deck)
            state_dict["enemy_deck_counts"] = len(state.playerA.deck)
        state_dict["cur_bf"] = state.cbf
        state_dict["events"] = state.evt
        state_dict["battlefields"] = self.handle_bf(state.battlefields, view)
        state_dict["type"] = "update_state"
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
    async def broadcast_turn(self):
        await self.connections["A"].send(
            {
                "type": "show_message",
                "message": "第 %d 回合" % self.game.totalTurn,
                "subtitle": ("我方行动" if self.game.totalTurn % 2 == 1 else "对方行动")
            }
        )
        await self.connections["B"].send(
            {
                "type": "show_message",
                "message": "第 %d 回合" % self.game.totalTurn,
                "subtitle": ("我方行动" if self.game.totalTurn % 2 == 0 else "对方行动")
            }
        )
    async def start_game(self):
        print("Game session started.")
        self.game.totalTurn = 1
        await self.broadcast_turn()
        self.game.InitDraw()
        self.game.TurnStart('B')
        await self.broadcast_state()
    
if __name__ == "__main__":
    ...
