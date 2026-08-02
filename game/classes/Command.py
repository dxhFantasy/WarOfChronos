from .Card import *
from enum import Enum
from .Tags import *
from typing import Literal
#from abc import ABC

class TargetOwner(Enum):
  Enemy = '敌方单位'
  Ally = '友方单位'
  All = '所有单位'

ALL = -1 #这个是标记指向所有

class cmp(Enum):              #字面意思
  Eq = '等于'
  NEq = '不等于'
  Gr = '大于'
  NGr = '不大于'
  Le = '小于'
  NLe = '不小于'



HQ = 114514
@dataclass
class ChooseCondition():      #选择目标的条件
  tid : int | None = None #可能要打总部
  atk : tuple[cmp,int] | None = None
  dfns : tuple[cmp,int] | None = None
  tag : Tag | None = None
  cost : tuple[cmp,int] | None = None
  actCost : tuple[cmp,int] | None = None
  frontline : Literal[0,1,2] | None = None
  timeline : Literal[0,1,2] | None = None


@dataclass
class TargetChoose():         #目标指示器
  owner : TargetOwner
  num : int   #刚刚的ALL
  Random : bool
  condition : ChooseCondition | None = None
  

class TriggerConditionType(Enum):#效果触发条件
  HasUnitsOnField = '场上有单位'
  EventsHappend = '事件被触发'
  ...

@dataclass
class TriggerCondition():        #条件指示器
  cdtnType :TriggerConditionType
  target : TargetChoose | None = None


class EffectType(Enum):          #字面意思
  DrawCard = '抽牌'
  Deploy = '部署'
  TakeDamage = '受到伤害'
  AddToHand = '加入手牌'
  ShuffleIntoDeck = '洗入卡组'
  PutOnTop = '置于卡组顶'
  PutOnBottom = '置于卡组底'
  Destroy = '消灭'
  Buff = '+x+x'
  AddAC = '增加行动花费'
  AddAP = '获得行动点'
  ADDAPS = '获得行动点槽'
  AddTag = '获得xx词条'


TURN_START = '回合开始'
TURN_END = '回合结束'
ENEMY = '敌方'
ALLY = '友方'

@dataclass
class EndTime():
  turnCount : int
  turnOwner : str
  turnTime : str

#eg ： 1/ENEMY/TURN_START 下个敌方回合开始时  0/ALLY/TURN_END （这个友方）回合结束时

@dataclass
class EffectData():
  target : TargetChoose | int #考虑到有时要把某张牌加入手牌/洗入卡组,加int指示卡牌id
  effect : EffectType
  value : int | Tag | tuple[int,int] #+x+x的两个x
  endTime : EndTime | None = None
  triggerCondition : list[TriggerCondition] | None = None





class CommandCard(Card):
  def __init__(self, cost_: int, tags_: list[Tag], name_ : str, owner_ : str, effects_ : list[EffectData], dect_ : str, tl : Literal[0,1,2]) -> None:
    super().__init__(cost_, tags_, name_, owner_, tl)
    self.effects = effects_
    self.dect = dect_
