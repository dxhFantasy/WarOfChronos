from classes.Card import *
from classes.Tags import *
from enum import Enum

class UnitType(Enum):
  infantry = '步兵'
  tank = '坦克'
  fighter = '战斗机'
  bomber = '轰炸机'
  starship = '星舰'

'''

class Target(Card):
  def __init__(self, attack_ : int,defense_ : int, tags_ : list[Tag], cost_ : int, name_ : str, owner_ : str) -> None:
    super().__init__(cost_, tags_, name_, owner_)
    self.defense = defense_
    self.attack = attack_
    self.id : int | None = None
'''


class UnitCard(Card):
  def __init__(self, attack_: int, defense_: int, tags_: list[Tag], cost_ : int, actionCost_ : int, name_ : str, owner_ : str,type_ : UnitType, inHand_ : bool = True) -> None:
    super().__init__(cost_, tags_, name_, owner_)
    self.defense = defense_
    self.attack = attack_
    self.id : int | None = None
    self.actionCost = actionCost_
    self.inHand = inHand_
    self.type = type_
  
  def AddAttack(self,n : int):
    self.attack += n
  
  def AddTag(self,newTag : Tag):
    self.tags.append(newTag)

  # def loseHp(self, damage : int) -> tuple[int,int]:
  #   self.defense-=damage
  #   return (self.defense, damage)

  def ClacDamage(self,baseDamage : int) -> int:
    damage : int = baseDamage
    
    for tag in self.tags:
      if tag : #处理特殊效果
        ...
    
    return damage
  
  def ClacAtk(self,baseAtk : int):
    atk : int = baseAtk
    for tag in self.tags:
      if tag : #处理特殊效果
        ...
    return atk


class CommandCard(Card):
  def __init__(self, cost_: int, tags_: list[Tag], name_ : str, owner_ : str) -> None:
    super().__init__(cost_, tags_, name_, owner_)
