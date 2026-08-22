from .classes.Target import *
from dataclasses import dataclass
import random

A = 0
B = 1
C = 2

allCards : list[UnitCard | CommandCard] = [
UnitCard(6,7,[Tag(Keyword.Guard),Tag(Keyword.Prepared)],7,2,'ZTZ99A主战坦克','N',UnitType.tank,B),
UnitCard(4,2,[Tag(Keyword.Blitz)],\
            3,1,'2S38\"偏流\"','N',UnitType.tank,B),
CommandCard(7,[],'破釜沉舟','',effects_=[
  EffectData(
    target=TargetChoose(
      owner=TargetOwner.Ally,
      num=ALL,
      Random=False),
    effect=EffectType.Buff,
    value=(4,-1),
    endTime=Time(0,turnOwner=ALLY,turnTime=TURN_END,info = END)),
  EffectData(
    target=TargetChoose(
      condition=ChooseCondition(tid = HQ),
      owner=TargetOwner.Ally,
      num=1,
      Random=False),
    effect=EffectType.TakeDamage,
    value=7,)
],dect_='使所有友方单位获得 +4-1 , 对友方总部造成 7 点伤害',tl=0),
CommandCard(3,[],'全频带阻塞干扰','',effects_=[
  EffectData(
    target=TargetChoose(
      owner=TargetOwner.All,
      num = ALL,
      Random = False,
    ),
    effect=EffectType.AddAC,
    value = 4,
  )
],dect_='使所有单位获得 +4 行动花费',tl=1),
CommandCard(7,[],'死线扩散','',effects_=[
  EffectData(
    target=TargetChoose(
      owner=TargetOwner.Enemy,
      num = ALL,
      Random = False,
    ),
    effect=EffectType.SetAtk,
    value = 0,
  ),
  EffectData(
    target=TargetChoose(
      owner = TargetOwner.Enemy,
      num = ALL,
      Random = False,
    ),
    effect=EffectType.ADDAPS,
    value = -2,
  ),
],dect_='使所有敌方单位攻击力为 0 ,友方失去2个行动点槽',tl=C),
UnitCard(
  attack_= 5,
  defense_= 4,
  tags_= [
    Tag(
      keyword=Keyword.Blitz
    ),
    Tag(
      keyword=Keyword.Deathrattle,
      value=[
        EffectData(
          target=TargetChoose(
            owner=TargetOwner.Enemy,
            num=1,
            Random=False,
            condition=ChooseCondition(
              tid=HQ
            )
          ),
          effect=EffectType.TakeDamage,
          value=3,
        )
      ]
    )
  ],
  cost_ = 6,
  actionCost_ = 2,
  name_ = '强-5 强击机',
  owner_='N',
  type_=UnitType.bomber,
  timeline=B
),
CommandCard(
  cost_=5,
  tags_=[],
  name_='陈庆之北伐',
  owner_='',
  effects_=[
    EffectData(
      target=TargetChoose(
        owner=TargetOwner.Enemy,
        num=ALL,
        Random=False
      ),
      effect=EffectType.Buff,
      value=(-2,-3)
    )
  ],
  dect_='使所有敌方单位获得-2-3',
  tl=A
),
UnitCard(
  attack_=7,
  defense_=5,
  tags_=[
    Tag(
      keyword=Keyword.Blitz
    ),
  ],
  cost_=7,
  actionCost_=1,
  name_='BMPT-"终结者"',
  owner_='N',
  type_=UnitType.tank,
  timeline=B,
),
UnitCard(
  attack_=4,
  defense_=5,
  tags_=[
    Tag(
      keyword=Keyword.Guard
    )
  ],
  cost_=4,
  actionCost_=0,
  name_='白袍军',
  owner_='N',
  type_=UnitType.infantry,
  timeline=A
)
]

cardIds = list(range(len(allCards)))

cardIds *= 10

def CardToHand(cid : int):
  return HandCard(cid,allCards[cid].cost,[])



@dataclass
class HandCard():
  id : int
  cost : int
  extraTags : list[Tag]

def Shuffle():
  random.shuffle(cardIds)



