from ..classes.Tags import *
from typing import Literal

class Card():
  def __init__(self, cost_ : int, tags_ : list[Tag], name_ : str, owner_ : str, timeline : Literal[0,1,2]) -> None:
    self.cost = cost_
    self.tags = tags_
    self.name = name_
    self.owner = owner_
    self.timeline : Literal[0,1,2] = timeline