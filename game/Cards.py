from .classes.Tags import *
from .classes.Target import *
from .classes.Command import *
from dataclasses import dataclass
import random

allCards : list[UnitCard | CommandCard] = [
UnitCard(6,8,[Tag(Keyword.Guard)],6,2,'ZTZ99A主战坦克','N',UnitType.tank,2),
UnitCard(6,2,[Tag(Keyword.Blitz)],\
            3,1,'2S38\"偏瘫\"','N',UnitType.tank,2),
CommandCard(7,[],'破釜沉舟','',effects_=[
  EffectData(
    target=TargetChoose(
      owner=TargetOwner.Ally,
      num=ALL,
      Random=False),
    effect=EffectType.Buff,
    value=(4,-1),
    endTime=EndTime(0,turnOwner=ALLY,turnTime=TURN_END)),
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
],dect_='使所有单位获得 +4 行动花费',tl=1)
]

cardIds = list(range(0,len(allCards)))

cardIds *= 40

def CardToHand(cid : int):
  return HandCard(cid,allCards[cid].cost,[])



@dataclass
class HandCard():
  id : int
  cost : int
  extraTags : list[Tag]

def Shuffle():
  random.shuffle(cardIds)



