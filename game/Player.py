from dataclasses import dataclass
from .Cards import *

@dataclass
class Player():
  actionPoint : int
  apSlot : int
  handCards : list[HandCard]
  deck : list[int]
  hq : int
  name : Literal['A','B','N']
