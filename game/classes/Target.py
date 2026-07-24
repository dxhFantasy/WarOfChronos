from Tags import *
from Card import *
from game.classes.Tags import Tag


class Target(Card):
  def __init__(self,defense_ : int, attack_ : int, tags_ : list[Tag], cost_ : int) -> None:
    super().__init__(cost_, tags_)
    self.defense = defense_
    self.attack = attack_
    self.id : int | None = None

  def loseHp(self, damage : int) -> tuple[int,int]:
    self.defense-=damage
    return (self.defense, damage)

  def TakeDamage(self,baseDamage : int) -> tuple[int,int]:
    damage : int = baseDamage
    
    for tag in self.tags:
      if tag : #处理特殊效果
        ...

    return self.loseHp(damage)
  


class Unit(Target):
  def __init__(self, defense_: int, attack_: int, tags_: list[Tag], cost_ : int, actionCost_ : int) -> None:
    super().__init__(defense_, attack_, tags_, cost_)
    self.actionCost = actionCost_


class Command(Card):
  def __init__(self, cost_: int, tags_: list[Tag]) -> None:
    super().__init__(cost_, tags_)
