from ..classes.Tags import *

class Card():
  def __init__(self, cost_ : int, tags_ : list[Tag], name_ : str, owner_ : str) -> None:
    self.cost = cost_
    self.tags = tags_
    self.name = name_
    self.owner = owner_