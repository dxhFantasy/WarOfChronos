from Tags import *

class Card():
  def __init__(self, cost_ : int, tags_ : list[Tag]) -> None:
    self.cost = cost_
    self.tags = tags_