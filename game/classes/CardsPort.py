# # -*- coding: utf-8 -*-
# """把 CommandEffect 的 GamePort 接到原有的 Game / Unit / Card 上。"""
'''此文件已废弃'''
# from __future__ import annotations

# from collections.abc import Mapping, Sequence
# from typing import TYPE_CHECKING

# from .Card import Keyword, Tag
# from .CommandEffect import (
#     CardType, EvalContext, EventType, GameEvent, GamePort,
#     StatKind, UnitType, Zone,
# )
# from .Frontline import Unit, CardToUnit
# from .Target import ClacDamage

# if TYPE_CHECKING:
#     from ..game import Game



# EntityId = str

# # ---- 实体引用编码：单位 "unit:<id>"，总部 "hq:A" ----

# def UnitRef(uid: int) -> EntityId:
#     return f"unit:{uid}"

# def HqRef(player: str) -> EntityId:
#     return f"hq:{player}"

# def IsHqRef(ref: EntityId) -> bool:
#     return ref.startswith("hq:")

# # ---- CustomAction 的操作名 ----

# from .CommandEffect import (
#     OP_ACTION_COST, OP_ADD_TO_HAND, OP_AP, OP_AP_SLOT,
#     OP_CHANGE_EVENT, OP_SET_ACTION_COST, OP_SET_AP, OP_SET_AP_SLOT,
#     OP_SET_ATTACK, OP_SET_HEALTH, OP_SHUFFLE, OP_TO_BOTTOM, OP_TO_TOP,
# )



# class KardsPort(GamePort):
#     """实现所有“真正改变游戏状态”的操作。

#     可修改点：
#       * ListEntities 的 HAND / DECK 分支（目前只支持战场和总部）。
#       * Choose：改成前端异步选择时，把 choiceQueue 换成回调。
#     """

#     def __init__(self, game: Game) -> None:
#         self.game = game
#         self.choiceQueue: list[int | None] = []

#     # ---------- 基础解析 ----------

#     def GetUnit(self, ref: EntityId) -> Unit | None:
#         if IsHqRef(ref):
#             return None
#         return self.game.GetUnitById(int(ref.split(":", 1)[1]))

#     def HqOwner(self, ref: EntityId) -> str:
#         return ref.split(":", 1)[1]

#     # ---------- 查询 ----------

#     def GetHQ(self, player: str) -> EntityId:
#         return HqRef(player)

#     def ListEntities(self, player: str, zone: Zone) -> Sequence[EntityId]:
#         if zone is Zone.BOARD:
#             bf = self.game.battlefields[self.game.currentBF]
#             return [UnitRef(u.id) for fl in bf.frontlines for u in fl.targets]
#         # 手牌/卡组不是实体实例，需要时可在这里扩展
#         return []

#     def GetStat(self, entity: EntityId, stat: StatKind) -> int:
#         if IsHqRef(entity):
#             player = self.game.GetPlayer(self.HqOwner(entity))
#             if player is None:
#                 return 0
#             return player.hq if stat is StatKind.HEALTH else 0
#         u = self.GetUnit(entity)
#         if u is None:
#             return 0
#         if stat is StatKind.ATTACK:
#             return u.atk
#         if stat is StatKind.HEALTH:
#             return u.dfns
#         if stat is StatKind.COST:
#             return u.cost
#         if stat is StatKind.ACTION_COST:
#             return u.actionCost
#         if stat is StatKind.FRONTLINE:
#             return u.fl
#         if stat is StatKind.TIMELINE:
#             return u.utl
#         return 0

#     def GetKeywords(self, entity: EntityId) -> frozenset[str]:
#         u = self.GetUnit(entity)
#         if u is None:
#             return frozenset()
#         return frozenset(t.keyword.value for t in u.tags)

#     def GetCardType(self, entity: EntityId) -> CardType:
#         return CardType.HQ if IsHqRef(entity) else CardType.UNIT

#     def GetUnitType(self, entity: EntityId) -> UnitType:
#         u = self.GetUnit(entity)
#         if u is None:
#             return UnitType.NONE
#         try:
#             return UnitType(u.uType.value)
#         except ValueError:
#             return UnitType.NONE

#     def IsAlive(self, entity: EntityId) -> bool:
#         if IsHqRef(entity):
#             return True
#         u = self.GetUnit(entity)
#         return u is not None and u.dfns > 0

#     def OpponentOf(self, player: str) -> str:
#         return 'B' if player == 'A' else 'A'

#     def Choose(self, candidates: Sequence[EntityId], ctx: EvalContext) -> EntityId | None:
#         """从指令/效果发起时排队的目标里取一个（Human 输入）。"""
#         while self.choiceQueue:
#             tid = self.choiceQueue.pop(0)
#             if tid is None:
#                 continue
#             ref = UnitRef(tid)
#             if ref in candidates:
#                 return ref
#         return candidates[0] if candidates else None

#     # ---------- 操作 ----------

#     def DealDamage(self, source: EntityId | None, target: EntityId,
#                   amount: int, ctx: EvalContext) -> None:
#         if IsHqRef(target):
#             player = self.game.GetPlayer(self.HqOwner(target))
#             if player is not None:
#                 player.hq -= amount
#             self.game.effectInterp.HandleEvent(
#                 GameEvent(EventType.HQ_DAMAGED, subject=target, data={'数值': amount}))
#             return
#         u = self.GetUnit(target)
#         if u is None:
#             return
#         dmg = ClacDamage(u.tags, amount)      # 保留被动减伤
#         u.dfns -= dmg
#         self.game.effectInterp.HandleEvent(
#             GameEvent(EventType.UNIT_DAMAGED, actor=u.owner, subject=target,
#                       data={'数值': dmg}))

#     def Heal(self, target: EntityId, amount: int, ctx: EvalContext) -> None:
#         if IsHqRef(target):
#             player = self.game.GetPlayer(self.HqOwner(target))
#             if player is not None:
#                 player.hq += amount
#             return
#         u = self.GetUnit(target)
#         if u is None:
#             return
#         u.dfns += amount
#         self.game.effectInterp.HandleEvent(
#             GameEvent(EventType.UNIT_HEALED, actor=u.owner, subject=target,
#                       data={'数值': amount}))

#     def Destroy(self, target: EntityId, ctx: EvalContext) -> None:
#         u = self.GetUnit(target)
#         if u is None:
#             return
#         u.dfns = -1
#         self.game.Check()

#     def DrawCards(self, player: str, amount: int, ctx: EvalContext) -> None:
#         self.game.DrawCard(player, amount)
#         self.game.effectInterp.HandleEvent(
#             GameEvent(EventType.CARD_DRAWN, actor=player, data={'数值': amount}))

#     def Discard(self, entity: EntityId, ctx: EvalContext) -> None:
#         # 手牌目前不是实体，留空
#         return

#     def ModifyStats(self, entity: EntityId, attack: int, health: int,
#                     ctx: EvalContext) -> None:
#         u = self.GetUnit(entity)
#         if u is None:
#             return
#         u.atk = max(0, u.atk + attack)
#         u.dfns += health

#     def GrantKeyword(self, entity: EntityId, keyword: str, ctx: EvalContext) -> None:
#         u = self.GetUnit(entity)
#         if u is None:
#             return
#         try:
#             kw = Keyword(keyword)
#         except ValueError:
#             return
#         if self.FindTag(u, kw) is None:
#             u.tags.append(Tag(kw))

#     def RevokeKeyword(self, entity: EntityId, keyword: str, ctx: EvalContext) -> None:
#         u = self.GetUnit(entity)
#         if u is None:
#             return
#         try:
#             kw = Keyword(keyword)
#         except ValueError:
#             return
#         idx = self.FindTag(u, kw)
#         if idx is not None:
#             u.tags.pop(idx)

#     @staticmethod
#     def FindTag(u: Unit, kw: Keyword) -> int | None:
#         for i, t in enumerate(u.tags):
#             if t.keyword == kw:
#                 return i
#         return None

#     def Summon(self, player: str, cardId: str, ctx: EvalContext) -> None:
#         from ..Cards import allCards
#         from .Target import UnitCard
#         card = allCards[int(cardId)]
#         if not isinstance(card, UnitCard):
#             return
#         u = CardToUnit(card)
#         u.id = self.game.lastId + 1
#         self.game.lastId += 1
#         u.owner = player
#         u.fl = 1
#         assert player == 'A' or player == 'B'
#         self.game.Deploy(u, 1, player)

#     def AddKredits(self, player: str, amount: int, ctx: EvalContext) -> None:
#         p = self.game.GetPlayer(player)
#         if p is not None:
#             p.actionPoint += amount

#     def CustomAction(self, op: str, args: Mapping[str, int | str],
#                     ctx: EvalContext, target: EntityId | None) -> None:
#         value = int(args.get('值', 0))
#         player = self.game.GetPlayer(ctx.owner)

#         # ---- 不指向具体单位、只作用于玩家的操作 ----
#         if target is None:
#             if player is None:
#                 return
#             if op == OP_AP:
#                 player.actionPoint += value
#             elif op == OP_AP_SLOT:
#                 player.apSlot += value
#             elif op == OP_SET_AP:
#                 player.actionPoint = value
#             elif op == OP_SET_AP_SLOT:
#                 player.apSlot = value
#             elif op == OP_ADD_TO_HAND:
#                 from ..Cards import CardToHand
#                 player.handCards.append(CardToHand(value))
#             elif op == OP_TO_TOP:
#                 player.deck.append(value)
#             elif op == OP_TO_BOTTOM:
#                 player.deck.insert(0, value)
#             elif op == OP_SHUFFLE:
#                 import random
#                 player.deck.append(value)
#                 random.shuffle(player.deck)
#             elif op == OP_CHANGE_EVENT:
#                 self.game.ChangeEvent(value)  # type: ignore[arg-type]
#             return

#         # ---- 指向单位 ----
#         if IsHqRef(target):
#             if op == OP_SET_HEALTH and player is not None:
#                 player.hq = value
#             elif op == OP_AP and player is not None:
#                 player.actionPoint += value
#             return
#         u = self.GetUnit(target)
#         if u is None:
#             return
#         if op == OP_ACTION_COST:
#             u.actionCost += value
#         elif op == OP_SET_ACTION_COST:
#             u.actionCost = value
#         elif op == OP_SET_ATTACK:
#             u.atk = max(0, value)
#         elif op == OP_SET_HEALTH:
#             u.dfns = value
