# -*- coding: utf-8 -*-
from .classes.Target import *
from .classes.Card import PassiveTag, PassiveType, ClacType, Tag, Keyword
from .classes.CommandEffect import (
    Buff, CustomAction, DealDamage, DrawCards, Effect, EndPoint, EventType,
    ForEach, Lifespan, PlayEffect, Selection, Side, StartPoint, Trigger,
)
# 下划线别名：不会被 `from .Cards import *` 转发，避免 Final 重分配报错
from .classes.CommandEffect import (
    OP_ACTION_COST as _OP_ACTION_COST,
    OP_AP_SLOT as _OP_AP_SLOT,
    OP_SET_ATTACK as _OP_SET_ATTACK,
    OP_SHUFFLE as _OP_SHUFFLE,
    OP_TO_TOP as _OP_TO_TOP,
)


from dataclasses import dataclass
import random

A = 0
B = 1
C = 2

allCards: list[UnitCard | CommandCard] = [
  # ================= 0 =================
  UnitCard(6, 7, [Tag(Keyword.Guard), Tag(Keyword.Prepared)], 7, 2,
          'ZTZ99A主战坦克', 'N', UnitType.tank, B, '守护,预备'),

  # ================= 1 =================
  UnitCard(4, 2, [Tag(Keyword.Blitz)], 3, 1,
          '2S38"偏流"', 'N', UnitType.tank, B, '闪击'),

  # ================= 2 指令 =================
  CommandCard(7, [], '破釜沉舟', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        Buff(Selection.Units(Side.FRIENDLY), 4, -1),
        DealDamage(Selection.HQ(Side.FRIENDLY), 7),
        # 快照每个被加过 buff 的单位，本友方回合结束时单独复原
        ForEach(
          Selection.Units(Side.FRIENDLY),
          PlayEffect(Effect(
            trigger=Trigger(EventType.TURN_ENDED, side=Side.FRIENDLY),
            lifespan=Lifespan(StartPoint.NOW, EndPoint.AFTER_TRIGGER),
            actions=(Buff(Selection.Self(), -4, 1),),   # ← 加圆括号和逗号
          )),
        ),
      ),
    ),
  ), dect_='使所有友方单位获得 +4-1，本回合结束时复原；对友方总部造成 7 点伤害', tl=A),

  # ================= 3 指令 =================
  CommandCard(3, [], '全频带阻塞干扰', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        CustomAction(_OP_ACTION_COST, Selection.Units(Side.ANY), {'值': 4}),
      ),
    ),
  ), dect_='使所有单位获得 +4 行动花费', tl=B),

  # ================= 4 指令 =================
  CommandCard(7, [], '死线扩散', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        CustomAction(_OP_SET_ATTACK, Selection.Units(Side.ENEMY), {'值': 0}),
        CustomAction(_OP_AP_SLOT, None, {'值': -2}),
      ),
    ),
  ), dect_='使所有敌方单位攻击力变为 0；友方失去 2 个行动点槽', tl=C),

  # ================= 5 单位：闪击 + 亡计 =================
  UnitCard(5, 4, [Tag(Keyword.Blitz), Tag(Keyword.Deathrattle)], 6, 2,
          '强-5 强击机', 'N', UnitType.bomber, B,
          '闪击。亡计：对敌方总部造成 3 点伤害',
          effects_=(
            Effect(
              trigger=Trigger(EventType.UNIT_DESTROYED,
                              subjectMatches=Selection.Self()),
              lifespan=Lifespan(),
              actions=(DealDamage(Selection.HQ(Side.ENEMY), 3),),
            ),
          )),

  # ================= 6 指令 =================
  CommandCard(5, [], '陈庆之北伐', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(Buff(Selection.Units(Side.ENEMY), -2, -3),),
    ),
  ), dect_='使所有敌方单位获得 -2-3', tl=A),

  # ================= 7 =================
  UnitCard(7, 5, [Tag(Keyword.Blitz)], 7, 1,
          'BMPT-"终结者"', 'N', UnitType.tank, B, '闪击'),

  # ================= 8 =================
  UnitCard(4, 5, [Tag(Keyword.Guard)], 4, 0,
          '白袍军', 'N', UnitType.infantry, A, '守护'),

  # ================= 9 指令 =================
  CommandCard(4, [Tag(Keyword.TimeWarp)], '王莽', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 2),),
    ),
  ), dect_='穿梭，抽 2 张牌', tl=A),

  # ================= 10 指令 =================
  CommandCard(5, [], '改革开放', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(DrawCards(Side.FRIENDLY, 3),),
    ),
  ), dect_='抽 3 张牌', tl=B),

  # ================= 11 单位：被动 =================
  UnitCard(6, 3,
          [PassiveTag(PT=PassiveType.TakeDamage, CT=ClacType.MLimit, value=1)],
          5, 1, '德械师', 'N', UnitType.infantry, A,
          '本单位受到的伤害至多为 1'),

  # ================= 12 =================
  UnitCard(5, 6, [], 5, 2,
          'T-34 85D/5T', 'N', UnitType.tank, A, ''),

  # ================= 13 =================
  UnitCard(5, 5, [Tag(Keyword.Blitz)], 5, 1,
          'T-72', 'N', UnitType.tank, B, '闪击'),

  # ================= 14 指令 =================
  CommandCard(6, [], '军备竞赛', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        CustomAction(_OP_TO_TOP, None, {'值': 13}),
        CustomAction(_OP_SHUFFLE, None, {'值': 13}),
      ),
    ),
  ), dect_='将 2 张"T-72"分别置于友方卡组顶与洗入卡组', tl=B),

  # ================= 15 指令 =================
  CommandCard(1, [], '经济危机', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DealDamage(Selection.HQ(Side.FRIENDLY), 3),
        DrawCards(Side.FRIENDLY, 1),
      ),
    ),
  ), dect_='抽 1 张牌，对友方总部造成 3 点伤害', tl=B),

  # ================= 16 指令 =================
  CommandCard(5, [], '市场经济', '', effects_=(
    Effect(
      trigger=Trigger(EventType.SELF_DEPLOYED),
      lifespan=Lifespan.Once(),
      actions=(
        DrawCards(Side.FRIENDLY, 3),
        CustomAction(_OP_SHUFFLE, None, {'值': 15}),
        CustomAction(_OP_SHUFFLE, None, {'值': 16}),
      ),
    ),
  ), dect_='抽 3 张牌，将 1 张"经济危机"和"市场经济"洗入卡组', tl=B),
]

# 原来 +1 会让最后一张牌索引越界，去掉
cardIds = list(range(len(allCards)))
def RemoveCard(cardIdx : int):
  cardIds.remove(cardIdx)

RemoveCard(15)

@dataclass
class HandCard():
  id : int
  cost : int
  extraTags : list[Tag]


def CardToHand(cid : int):
  return HandCard(cid, allCards[cid].cost, [])


def Shuffle():
  random.shuffle(cardIds)
