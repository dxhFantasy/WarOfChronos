"""A small, dependency-free rule bot for the built-in single-player mode."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Literal, cast

from game.Cards import CommandCard, UnitCard, allCards
from game.classes.Card import Keyword
from game.classes.Target import UnitType
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
    """Greedy bot with basic combat and board-development heuristics."""

    ACTION_DELAY = 1.5

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
        # Let the human see the turn transition before the first action.
        await asyncio.sleep(self.ACTION_DELAY)
        for _ in range(40):
            if not self._playing():
                return
            action = self.choose_action()
            if action is None:
                break
            await self.session.handle_action(self.side, action)
            await asyncio.sleep(self.ACTION_DELAY)
        if self._playing():
            await self.session.handle_action(
                self.side, {"op_type": "end_turn"}
            )

    def choose_action(self) -> dict[str, Any] | None:
        # 1. If the combined available HQ damage is lethal, go face.
        action = self._lethal_hq_action()
        if action is not None:
            return action

        # 2. Remove/neutralize a valuable enemy target before developing.
        action = self._command_action(enemy_only=True)
        if action is not None:
            return action

        # 3. Develop the board with the best available unit.
        action = self._deploy_action()
        if action is not None:
            return action

        # 4. Use buffs/draw/other non-removal commands after deploying.
        action = self._command_action(enemy_only=False)
        if action is not None:
            return action

        # 5. Take good attacks/trades; avoid clear suicide attacks.
        action = self._attack_action()
        if action is not None:
            return action

        # 6. Move toward the front.
        action = self._move_action()
        if action is not None:
            return action

        return None

    def _hq_damage_available(self) -> list[Any]:
        result: list[Any] = []
        for unit in self._own_units():
            _, can_hq = self.game.GetAttackTargets(unit, self.side)
            if can_hq:
                result.append(unit)
        return result

    def _lethal_hq_action(self) -> dict[str, Any] | None:
        enemy_player = self.game.GetPlayer(self._enemy_side())
        if enemy_player is None:
            return None
        units = self._hq_damage_available()
        total = sum(max(0, u.atk) for u in units)
        if total < enemy_player.hq or not units:
            return None
        unit = max(units, key=lambda u: u.atk)
        return {
            "op_type": "attack_unit",
            "unit_id": unit.id,
            "target_hq": True,
        }

    def _counter_damage(self, unit: Any, target: Any) -> int:
        if target.uType == UnitType.bomber:
            return 0
        if unit.uType in (UnitType.bomber, UnitType.artillery):
            return 0
        return max(0, target.atk)

    def _score_attack(self, unit: Any, target: Any) -> float:
        atk = max(0, unit.atk)
        target_hp = max(0, target.dfns)
        kills = atk >= target_hp
        counter = self._counter_damage(unit, target)
        dies = counter >= unit.dfns and counter > 0
        # Trading into a high-attack target is good; dying without a kill is bad.
        score = float(target.atk) * 2.0
        if kills:
            score += 25.0
        if dies:
            score -= 14.0
        if kills and dies:
            score += 8.0
        if target.uType == UnitType.fighter:
            score += 4.0
        return score

    def _attack_action(self) -> dict[str, Any] | None:
        best_score = -1e9
        best_action: dict[str, Any] | None = None
        for unit in self._own_units():
            targets, can_hq = self.game.GetAttackTargets(unit, self.side)
            for target_id in targets:
                target = self.game.GetUnitById(target_id)
                if target is None:
                    continue
                score = self._score_attack(unit, target)
                counter = self._counter_damage(unit, target)
                # Do not throw a unit away into a surviving target for nothing.
                if unit.atk < target.dfns and counter >= unit.dfns:
                    continue
                if score > best_score:
                    best_score = score
                    best_action = {
                        "op_type": "attack_unit",
                        "unit_id": unit.id,
                        "target_id": target.id,
                    }
            if can_hq:
                # A safe HQ hit is a useful fallback when no good trade exists.
                hq_score = 8.0
                if hq_score > best_score and not targets:
                    best_score = hq_score
                    best_action = {
                        "op_type": "attack_unit",
                        "unit_id": unit.id,
                        "target_hq": True,
                    }
        return best_action

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
        best_score = -1e9
        best_action: dict[str, Any] | None = None
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
                # Prefer efficient bodies, with a small bonus for prepared units.
                score = float(card.attack + card.defense) - handcard.cost * 0.5
                if any(tag.keyword is Keyword.Prepared for tag in card.tags):
                    score += 1.0
                if timeline != current:
                    score += 0.5
                if score > best_score:
                    best_score = score
                    action: dict[str, Any] = {
                        "op_type": "deploy_unit",
                        "card_index": index,
                        "target": target,
                    }
                    if timeline != current:
                        action["timeline"] = timeline
                    best_action = action
        return best_action

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

    def _is_enemy_target(self, card_id: int) -> bool:
        kind = self.game.GetTargetKind(card_id)
        if kind is None:
            return False
        return kind.split("_", 1)[0] in ("enemy", "any")

    def _command_action(self, enemy_only: bool) -> dict[str, Any] | None:
        player = self._player()
        current = self.game.currentBF
        best_score = -1e9
        best_action: dict[str, Any] | None = None
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
            if self._is_enemy_target(handcard.id) != enemy_only:
                continue
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
                score = 5.0
                if target is not None:
                    selected = self.game.GetUnitById(target)
                    if selected is not None:
                        score = selected.atk * 2.0 + (10.0 if enemy_only else 2.0)
                    elif enemy_only:
                        score = 18.0
                if timeline != current:
                    score += 0.5
                if score > best_score:
                    best_score = score
                    action: dict[str, Any] = {
                        "op_type": "use_card",
                        "card_index": index,
                    }
                    if target is not None:
                        action["target_id"] = target
                    if timeline != current:
                        action["timeline"] = timeline
                    best_action = action
        return best_action

    def _move_action(self) -> dict[str, Any] | None:
        for unit in sorted(self._own_units(), key=lambda u: (-u.atk, -u.dfns)):
            targets = self.game.GetMoveTargets(unit, self.side)
            if not targets:
                continue
            if F in targets:
                target = F
            elif unit.fl == F and unit.dfns <= 2 and self._own_base() in targets:
                # Retreat a wounded frontline unit only if it is cheap to do so.
                target = self._own_base()
            else:
                continue
            return {
                "op_type": "move_unit",
                "unit_id": unit.id,
                "target": "frontline" if target == F else "player_base",
            }
        return None
