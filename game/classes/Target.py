from classes.Card import *
from classes.Tags import *


class Target(Card):
  def __init__(self, attack_ : int,defense_ : int, tags_ : list[Tag], cost_ : int, name_ : str, owner_ : str) -> None:
    super().__init__(cost_, tags_, name_, owner_)
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
  def __init__(self, attack_: int, defense_: int, tags_: list[Tag], cost_ : int, actionCost_ : int, name_ : str, owner_ : str, inHand_ : bool = True) -> None:
    super().__init__(defense_, attack_, tags_, cost_, name_, owner_)
    self.actionCost = actionCost_
    self.inHand = inHand_
  
  def AddAttack(self,n : int):
    self.attack += n
  
  def AddTag(self,newTag : Tag):
    self.tags.append(newTag)


class Command(Card):
  def __init__(self, cost_: int, tags_: list[Tag], name_ : str, owner_ : str) -> None:
    super().__init__(cost_, tags_, name_, owner_)
