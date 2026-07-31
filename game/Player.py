from dataclasses import dataclass
from Cards import *

@dataclass
class Player():
  actionPoint : int
  apSlot : int
  handCards : list[HandCard]
