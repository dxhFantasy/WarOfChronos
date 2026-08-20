from .Command import *
from typing import Literal

class Card():
  def __init__(self, cost_ : int, tags_ : list[Tag], name_ : str, owner_ : str, timeline : Literal[0,1,2]) -> None:
    self.cost = cost_
    self.tags = tags_
    self.name = name_
    self.owner = owner_
    self.timeline : Literal[0,1,2] = timeline


class CommandCard(Card):
  def __init__(self, cost_: int, tags_: list[Tag], name_ : str, owner_ : str, effects_ : list[EffectData], dect_ : str, tl : Literal[0,1,2]) -> None:
    super().__init__(cost_, tags_, name_, owner_, tl)
    self.effects = effects_
    self.dect = dect_