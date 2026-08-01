from .Card import *
from enum import Enum
from .Tags import *
#from abc import ABC

class TargetOwner(Enum):
  Enemy = '敌方单位'
  Ally = '友方单位'
  All = '所有单位'

ALL = -1

class cmp(Enum):
  Eq = '等于'
  NEq = '不等于'
  Gr = '大于'
  NGr = '不大于'
  Le = '小于'
  NLe = '不小于'

@dataclass
class TargetChoose():
  Atk : int | None
  

class EffectType(Enum):
  DrawCard = '抽牌'
  Deploy = '部署'
  TakeDamage = '受到伤害'



class EffectData(Enum):
  ...






class CommandCard(Card):
  def __init__(self, cost_: int, tags_: list[Tag], name_ : str, owner_ : str) -> None:
    super().__init__(cost_, tags_, name_, owner_)
