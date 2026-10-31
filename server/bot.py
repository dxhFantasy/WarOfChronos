"""A small, dependency-free rule bot for the built-in single-player mode."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Literal, cast

from game.Cards import CommandCard, UnitCard, allCards
from game.classes.Card import Keyword
from game.game import DA, DB, F, HQ_A, HQ_B

if TYPE_CHECKING:
    from .game_session import GameSession


class BotConnection:
    """Duck-typed player connection used by GameSession for the AI side."""

    side: Literal["B"] = "B"
    ready: bool = True
    room: Any = None

    async def send(self, data: dict[str, Any]) -> None:
        # The bot has no browser connection; GameSession still calls send().
        return None


class SimpleBot:
    """Greedy bot: play on curve, trade reasonably, and attack the HQ when able."""

    def __init__(self, session: GameSession, side: Literal["A", "B"] = "B") -> None:
        self.session = session
        self.side: Literal["A", "B"] = side
        self.game = session.game

    def _playing(self) -> bool:
        return (
            self.session.status.name == "PLAYING"
            and self.game.IsTurn(self.side)
        )

    def _player(self) -> Any:
        player = self.game.GetPlayer(self.side)
        if player is None:
            raise RuntimeError("bot player is missing")
        return player

    def _enemy_side(self) -> Literal["A", "B"]:
        return "B" if self.side == "A" else "A"

    def _enemy_hq(self) -> int:
        return HQ_B if self.side == "A" else HQ_A

    def _own_base(self) -> int:
        return DA if self.side == "A" else DB

    def _units(self, owner: Literal["A", "B"]) -> list[Any]:
        bf = self.game.battlefields[self.game.currentBF]
        result: list[Any] = []
        for line in bf.frontlines:
            for unit in line.targets:
                if unit.owner == owner and unit.dfns > 0:
                    result.append(unit)
        return result

    def _own_units(self) -> list[Any]:
        return self._units(self.side)

    def _enemy_units(self) -> list[Any]:
        return self._units(self._enemy_side())

    async def play_turn(self) -> None:
        # Let the human client see the turn transition before the bot starts.
        await asyncio.sleep(0.6)
        for _ in range(40):
            if not self._playing():
                return
            action = self.choose_action()
            if action is None:
                break
            await self.session.handle_action(self.side, action)
            await asyncio.sleep(0.3)
        if self._playing():
            await self.session.handle_action(
                self.side, {"op_type": "end_turn"}
            )

    def choose_action(self) -> dict[str, Any] | None:
        # 1. Lethal HQ attack.
        action = self._attack_action(lethal_only=True)
        if action is not None:
            return action

        # 2. Develop the board.
        action = self._deploy_action()
        if action is not None:
            return action

        # 3. Use affordable commands (buffs/removal/draw).
        action = self._command_action()
        if action is not None:
            return action

        # 4. Attack units/HQ.
        action = self._attack_action()
        if action is not None:
            return action

        # 5. Reposition toward the front.
        action = self._move_action()
        if action is not None:
            return action

        return None

    def _attack_action(self, lethal_only: bool = False) -> dict[str, Any] | None:
        enemy_player = self.game.GetPlayer(self._enemy_side())
        if enemy_player is None:
            return None
        enemy_hq = enemy_player.hq

        for unit in self._own_units():
            targets, can_hq = self.game.GetAttackTargets(unit, self.side)
            if can_hq and enemy_hq <= unit.atk:
                return {
                    "op_type": "attack_unit",
                    "unit_id": unit.id,
                    "target_hq": True,
                }
            if lethal_only:
                continue
            if targets:
                target = min(
                    (self.game.GetUnitById(tid) for tid in targets),
                    key=lambda t: (t.dfns if t is not None else 999, -(t.atk if t is not None else 0)),
                )
                if target is not None:
                    return {
                        "op_type": "attack_unit",
                        "unit_id": unit.id,
                        "target_id": target.id,
                    }
            if can_hq:
                return {
                    "op_type": "attack_unit",
                    "unit_id": unit.id,
                    "target_hq": True,
                }
        return None

    def _deploy_target(self, card: UnitCard, timeline: int) -> str | None:
        bf = self.game.battlefields[timeline]
        base = self._own_base()
        if len(bf.frontlines[base].targets) < bf.frontlines[base].maxTargets:
            return "player_base"
        if any(tag.keyword is Keyword.Prepared for tag in card.tags):
            front = bf.frontlines[F]
            enemy_in_front = any(
                u.owner != self.side and u.dfns > 0 for u in front.targets
            )
            if not enemy_in_front and len(front.targets) < front.maxTargets:
                return "frontline"
        return None

    def _deploy_action(self) -> dict[str, Any] | None:
        player = self._player()
        current = self.game.currentBF
        for index, handcard in enumerate(player.handCards):
            card = cast(UnitCard | CommandCard, allCards[handcard.id])
            if not isinstance(card, UnitCard):
                continue
            if handcard.cost > player.actionPoint:
                continue
            if current not in card.timelines:
                continue
            timelines = [current]
            if self.game.IsTimeWarpCard(handcard.id):
                timelines = [t for t in (0, 1, 2) if t != current]
            for timeline in timelines:
                target = self._deploy_target(card, timeline)
                if target is None:
                    continue
                action: dict[str, Any] = {
                    "op_type": "deploy_unit",
                    "card_index": index,
                    "target": target,
                }
                if timeline != current:
                    action["timeline"] = timeline
                return action
        return None

    def _command_target_candidates(self, card_id: int) -> list[int]:
        kind = self.game.GetTargetKind(card_id)
        if kind is None:
            return []
        side, zone = kind.split("_", 1)
        candidates: list[int] = []
        enemy_units = sorted(
            self._enemy_units(), key=lambda u: (-u.atk, u.dfns)
        )
        friendly_units = sorted(
            self._own_units(), key=lambda u: (-u.atk, u.dfns)
        )
        enemy_hq = self._enemy_hq()

        if zone in ("unit", "any"):
            if side in ("enemy", "any"):
                candidates.extend(u.id for u in enemy_units)
            if side in ("friendly", "any"):
                candidates.extend(u.id for u in friendly_units)
        if zone in ("hq", "any"):
            if side in ("enemy", "any"):
                candidates.append(enemy_hq)
            if side in ("friendly", "any"):
                own_hq = HQ_A if self.side == "A" else HQ_B
                candidates.append(own_hq)
        return candidates

    def _choose_command_target(self, card_id: int) -> int | None:
        for target in self._command_target_candidates(card_id):
            if self.game.CheckCommandTarget(card_id, self.side, target) is None:
                return target
        return None

    def _command_action(self) -> dict[str, Any] | None:
        player = self._player()
        current = self.game.currentBF
        for index, handcard in enumerate(player.handCards):
            card = cast(UnitCard | CommandCard, allCards[handcard.id])
            if not isinstance(card, CommandCard):
                continue
            if not card.effects:
                continue
            if handcard.cost > player.actionPoint:
                continue
            if current not in card.timelines:
                continue
            has_target = self.game.GetTargetKind(handcard.id) is not None
            timelines = [current]
            if self.game.IsTimeWarpCard(handcard.id):
                # A targeted warp would need target selection in the new
                # timeline; the current card pool does not contain one.
                if has_target:
                    continue
                timelines = [t for t in (0, 1, 2) if t != current]
            for timeline in timelines:
                target = self._choose_command_target(handcard.id)
                if has_target and target is None:
                    continue
                action: dict[str, Any] = {
                    "op_type": "use_card",
                    "card_index": index,
                }
                if target is not None:
                    action["target_id"] = target
                if timeline != current:
                    action["timeline"] = timeline
                return action
        return None

    def _move_action(self) -> dict[str, Any] | None:
        for unit in self._own_units():
            targets = self.game.GetMoveTargets(unit, self.side)
            if not targets:
                continue
            target = F if F in targets else targets[0]
            return {
                "op_type": "move_unit",
                "unit_id": unit.id,
                "target": "frontline" if target == F else "player_base",
            }
        return None
