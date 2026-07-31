from classes.Target import *
from dataclasses import dataclass,field
from Cards import *

@dataclass
class Unit():
  id : int
  cardId : int
  atk : int
  dfns : int
  cost : int
  actionCost : int
  tags : list[Tag]
  uType : UnitType
  utl : Literal[0,1,2]
  

@dataclass
class Frontline():
  maxTargets : int
  targets : list[Unit] = field(
        default_factory=list[Unit]
  ) # type: ignore
  


def CardToUnit(card : UnitCard):
  return Unit(-1,allCards.index(card),card.attack,card.defense,card.cost,card.actionCost,card.tags,card.type,card.timeline)
