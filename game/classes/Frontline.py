from classes.Target import *
from dataclasses import dataclass,field

@dataclass
class Unit():
  id : int
  cardId : int
  atk : int
  dfns : int
  cost : int
  actionCost : int
  tags : list[Tag]
  

@dataclass
class Frontline():
  maxTargets : int
  targets : list[Unit] = field(
        default_factory=list[Unit]
  ) # type: ignore
  