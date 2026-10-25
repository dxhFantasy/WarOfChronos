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
    ActionType,
    HQ_A,
    HQ_B,
    DA,
    F,
    DB,
)
from enum import Enum
from typing import TYPE_CHECKING, Callable, Any, Literal
from typing import Coroutine
if TYPE_CHECKING:
    from .room import Player as PlayerConnection
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
        self.game: Game = Game()
        self.status: SessionState = SessionState.PLAYING
        self.broadcaster: Callable[[dict[str, Any]], Coroutine[Any, Any, None]] = broadcaster

    async def send_error(self, player_side: Literal["A", "B"], message: str) -> None:
        await self.connections[player_side].send({
            "type": "error",
            "message": message
        })

    def get_hand_cards(self, state: GameState, player_side: Literal["A", "B"]) -> list[HandCard]:
        return state.playerA.handCards if player_side == "A" else state.playerB.handCards

    def resolve_target(self, player_side: Literal["A", "B"], data: dict[str, Any]) -> int | None:
        '''把前端传来的 target_id / target_hq 转成游戏内的目标 id'''
        if data.get("target_hq"):
            if data.get("target_hq_side") == "friendly":
                return HQ_A if player_side == "A" else HQ_B
            return HQ_B if player_side == "A" else HQ_A
        target = data.get("target_id", None)
        if target is None:
            return None
        try:
            return int(target)
        except (TypeError, ValueError):
            return None

    def frontline_from_target(self, player_side: Literal["A", "B"], target: Any) -> int | None:
        '''把前端的 base / frontline 转成游戏内的阵线下标'''
        if target in (None, "player_base", "base"):
            return DA if player_side == "A" else DB
        if target in ("frontline", "front", F):
            return F
        try:
            target = int(target)
        except (TypeError, ValueError):
            return None
        if target in (DA, F, DB):
            return target
        return None

    async def handle_action(
            self,
            player_side: Literal["A", "B"] | None,
            data: dict[str, Any]
    ) -> None:
        if not player_side: return
        state = self.game.GetState()
        if self.status != SessionState.PLAYING:
            await self.connections[player_side].send({
                "type": "error",
                "message": "游戏未开始或已结束"
            })
            return
        entry: LogEntry | None = None
        op_type: str | None = data.get("op_type", None)
        card_id: int | None = None
        timeline: int | None = None
        if op_type == "surrender":
            winner: Literal["A", "B"] = "B" if player_side == "A" else "A"
            await self.broadcast_game_over(winner, reason="surrender")
            return
        if player_side == "A" and self.game.totalTurn % 2 == 0:
            await self.send_error(player_side, "当前不是你的回合")
            return
        if player_side == "B" and self.game.totalTurn % 2 == 1:
            await self.send_error(player_side, "当前不是你的回合")
            return
        if op_type == "deploy_unit":
            raw_card_index = data.get("card_index", None)
            if raw_card_index is None:
                await self.send_error(player_side, "缺少必要参数")
                return
            try:
                card_index = int(raw_card_index)
            except (TypeError, ValueError):
                await self.send_error(player_side, "手牌参数不合法")
                return
            handcards = self.get_hand_cards(state, player_side)
            if card_index < 0 or card_index >= len(handcards):
                await self.send_error(player_side, "手牌索引不存在")
                return
            target = self.frontline_from_target(player_side, data.get("target", None))
            if target is None:
                await self.send_error(player_side, "部署位置不合法")
                return
            card_id = handcards[card_index].id
            timeline: int | None = None
            if self.game.IsTimeWarpCard(card_id):
                raw_timeline = data.get("timeline", None)
                if raw_timeline is None:
                    await self.send_error(player_side, "请选择穿梭的时间线")
                    return
                try:
                    timeline = int(raw_timeline)
                except (TypeError, ValueError):
                    await self.send_error(player_side, "时间线参数不合法")
                    return
                if timeline not in (0, 1, 2):
                    await self.send_error(player_side, "时间线参数不合法")
                    return
            entry = LogEntry(
                TurnNumber=self.game.totalTurn,
                actorPlayer=player_side,
                actionType=ActionType.Deploy,
                actorId=card_id,
                target=target,
                handCardIdx=card_index,
                timeline=timeline
            )
        elif op_type == "end_turn":
            self.game.TurnEnd(player_side)
            self.game.totalTurn += 1
            await self.broadcast_turn()
            await self.broadcast_state()
            await self.broadcast_game_over()
            return
        elif op_type == "use_card":
            raw_card_index = data.get("card_index", None)
            if raw_card_index is None:
                await self.send_error(player_side, "缺少必要参数")
                return
            try:
                card_index = int(raw_card_index)
            except (TypeError, ValueError):
                await self.send_error(player_side, "手牌参数不合法")
                return
            handcards = self.get_hand_cards(state, player_side)
            if card_index < 0 or card_index >= len(handcards):
                await self.send_error(player_side, "手牌索引不存在")
                return
            card_id = handcards[card_index].id
            raw_timeline = data.get("timeline", None)
            timeline: int | None = None
            if self.game.IsTimeWarpCard(card_id):
                if raw_timeline is None:
                    await self.send_error(player_side, "请选择穿梭的时间线")
                    return
                try:
                    timeline = int(raw_timeline)
                except (TypeError, ValueError):
                    await self.send_error(player_side, "时间线参数不合法")
                    return
                if timeline not in (0, 1, 2):
                    await self.send_error(player_side, "时间线参数不合法")
                    return
            entry = LogEntry(
                TurnNumber=self.game.totalTurn,
                actorPlayer=player_side,
                actionType=ActionType.UseCommand,
                actorId=card_id,
                target=self.resolve_target(player_side, data),
                handCardIdx=card_index,
                timeline=timeline
            )
        elif op_type == "move_unit":
            raw_unit_id = data.get("unit_id", None)
            if raw_unit_id is None or data.get("target", None) is None:
                await self.send_error(player_side, "缺少必要参数")
                return
            try:
                unit_id = int(raw_unit_id)
            except (TypeError, ValueError):
                await self.send_error(player_side, "单位参数不合法")
                return
            target = self.frontline_from_target(player_side, data.get("target", None))
            if target is None:
                await self.send_error(player_side, "移动位置不合法")
                return
            entry = LogEntry(
                TurnNumber=self.game.totalTurn,
                actorPlayer=player_side,
                actionType=ActionType.Move,
                actorId=unit_id,
                target=target,
                handCardIdx=None
            )
        elif op_type == "attack_unit":
            raw_unit_id = data.get("unit_id", None)
            if raw_unit_id is None:
                await self.send_error(player_side, "缺少必要参数")
                return
            try:
                unit_id = int(raw_unit_id)
            except (TypeError, ValueError):
                await self.send_error(player_side, "单位参数不合法")
                return
            target = self.resolve_target(player_side, data)
            if target is None:
                await self.send_error(player_side, "未选择攻击目标")
                return
            entry = LogEntry(
                TurnNumber=self.game.totalTurn,
                actorPlayer=player_side,
                actionType=ActionType.Attack,
                actorId=unit_id,
                target=target,
                handCardIdx=None
            )
        else:
            await self.send_error(player_side, "未知的操作类型")
            return
        result = self.game.ProcessRecord(entry)
        if result.state == "ok":
            if op_type == "attack_unit" \
                    and entry.actorId is not None and entry.target is not None:
                await self.broadcast_message({
                    "type": "attack_animation",
                    "attacker_id": entry.actorId,
                    "target_id": entry.target,
                    "target_hq": entry.target in (HQ_A, HQ_B),
                    "target_hq_owner": (
                        "A" if entry.target == HQ_A
                        else "B" if entry.target == HQ_B
                        else None
                    ),
                })
            if op_type == "use_card" and card_id is not None:
                await self.connections["A" if player_side == "B" else "B"].send({
                                "type": "enemy_use_card",
                                "card_id":card_id,
                })
            await self.broadcast_state()
            await self.broadcast_game_over()
        else:
            await self.connections[player_side].send({
                "type": "error",
                "message": result.msg
            })
    def handle_handcards(self, handcards: list[HandCard]) -> list[dict[str, Any]]:
        l: list[dict[str, Any]] = []
        for hc in handcards:
            tags = self.game.GetCardTags(hc.id)
            l.append({
                "cost": hc.cost,
                "id": hc.id,
                "extTags": hc.extraTags,
                "tags": tags,
                "timelines": self.game.GetCardTimelines(hc.id),
                "target": self.game.GetTargetKind(hc.id),
                "timeWarp": self.game.IsTimeWarpCard(hc.id),
                "prepared": "预备" in tags,
            })
        return l
    def handle_units(self, units: list[Unit], view: Literal['A', 'B']) -> list[dict[str, Any]]:
        l: list[dict[str, Any]] = []
        for u in units:
            move_targets = self.game.GetMoveTargets(u, view)
            attack_targets, can_hq = self.game.GetAttackTargets(u, view)
            l.append({
                "id": u.id,
                "cardId": u.cardId,
                "atk": u.atk,
                "dfns": u.dfns,
                "cost": u.cost,
                "actionCost": u.actionCost,
                "tags": [t.keyword.value for t in u.tags],
                "uType": (u.uType.name, u.uType.value),
                "utl": u.utl,
                "owner": u.owner,
                "fl": u.fl,
                "relFl": u.fl if view == "A" else 2 - u.fl,
                "movedCount": self.game.moved.count(u.id),
                "attacked": u.id in self.game.attacked,
                "canMove": len(move_targets) > 0,
                "moveTargets": [
                    "frontline" if t == F else "base"
                    for t in move_targets
                ],
                "canAttack": len(attack_targets) > 0 or can_hq,
                "attackTargets": attack_targets,
                "canAttackHq": can_hq,
            })
        return l
    def handle_frontlines(self, frontlines: list[Frontline], view: Literal['A', 'B']) -> list[dict[str, Any]]:
        l: list[dict[str, Any]] = []
        for fl in frontlines:
            owners = {u.owner for u in fl.targets if u.dfns > 0}
            owner: str
            if not owners:
                owner = "N"
            elif owners == {"A"}:
                owner = "A"
            elif owners == {"B"}:
                owner = "B"
            else:
                owner = "X"
            l.append({
                "maxTargets" : fl.maxTargets,
                "owner": owner,
                "targets" : self.handle_units(fl.targets, view)
            })
        l.reverse() if view == "B" else None
        return l
    def handle_bf(self, bf: list[Battlefield], view: Literal['A', 'B']) -> list[dict[str, Any]]:
        l: list[dict[str, Any]] = []
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
    ) -> dict[str, Any]:
        state_dict: dict[str, Any] = dict()
        if view == 'A':
            state_dict['my_act_point'] = state.playerA.actionPoint
            state_dict["enemy_act_point"] = state.playerB.actionPoint
            state_dict["my_ap_slot"] = state.playerA.apSlot
            state_dict["enemy_ap_slot"] = state.playerB.apSlot
            state_dict["my_hq"] = state.playerA.hq
            state_dict["enemy_hq"] = state.playerB.hq
            state_dict["my_handcards"] = self.handle_handcards(state.playerA.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerB.handCards)
            state_dict["my_deck_cnts"] = len(state.playerA.deck)
            state_dict["enemy_deck_counts"] = len(state.playerB.deck)
        else:
            state_dict['my_act_point'] = state.playerB.actionPoint
            state_dict["enemy_act_point"] = state.playerA.actionPoint
            state_dict["my_ap_slot"] = state.playerB.apSlot
            state_dict["enemy_ap_slot"] = state.playerA.apSlot
            state_dict["my_hq"] = state.playerB.hq
            state_dict["enemy_hq"] = state.playerA.hq
            state_dict["my_handcards"] = self.handle_handcards(state.playerB.handCards)
            state_dict["enemy_hc_counts"] = len(state.playerA.handCards)
            state_dict["my_deck_cnts"] = len(state.playerB.deck)
            state_dict["enemy_deck_counts"] = len(state.playerA.deck)
        state_dict["cur_bf"] = state.cbf
        state_dict["events"] = state.evt
        state_dict["total_turn"] = self.game.totalTurn
        state_dict["my_side"] = view
        state_dict["my_turn"] = self.game.IsTurn(view)
        state_dict["my_hq_guarded"] = self.game.HqIsGuarded(view)
        state_dict["enemy_hq_guarded"] = self.game.HqIsGuarded(
            "B" if view == "A" else "A")
        state_dict["battlefields"] = self.handle_bf(state.battlefields, view)
        state_dict["type"] = "update_state"
        return state_dict
    async def broadcast_state(self) -> None:
        state = self.game.GetState()
        await self.connections["A"].send(
            self.state_jsonify(state, "A")
        )
        await self.connections["B"].send(
            self.state_jsonify(state, "B")
        )
    async def broadcast_message(self, message: dict[str, Any]) -> None:
        await self.broadcaster(message)
    async def broadcast_game_over(
        self,
        winner: Literal["A", "B", "draw"] | None = None,
        reason: Literal["hq", "surrender"] = "hq"
    ) -> bool:
        if winner is None:
            winner = self.game.GetWinner()
        if winner is None:
            return False
        if self.status == SessionState.FINISHED:
            return True
        self.status = SessionState.FINISHED
        sides: tuple[Literal["A", "B"], Literal["A", "B"]] = ("A", "B")
        for side in sides:
            if winner == "draw":
                result = "draw"
                message = "平局"
            elif winner == side:
                result = "win"
                message = "胜利"
            else:
                result = "lose"
                message = "失败"
            if reason == "surrender":
                if result == "win":
                    message = "对方投降"
                elif result == "lose":
                    message = "我方投降"
            await self.connections[side].send({
                "type": "game_over",
                "winner": winner,
                "my_result": result,
                "message": message,
                "reason": reason,
            })
        return True
    async def broadcast_turn(self) -> None:
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
    async def start_game(self) -> None:
        print("Game session started.")
        self.game.totalTurn = 1
        await self.broadcast_turn()
        self.game.InitDraw()
        self.game.TurnStart('B')
        await self.broadcast_state()
    
if __name__ == "__main__":
    ...
