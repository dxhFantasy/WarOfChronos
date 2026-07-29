from dataclasses import dataclass

@dataclass
class Player():
  actionPoint : int
  apSlot : int
  handCards : list[str]
