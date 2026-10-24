from __future__ import annotations
from enum import Enum
from enum import Enum
from dataclasses import dataclass
from typing import Literal
#from abc import ABC
from typing import Literal

class Keyword(Enum):
    Blitz = '闪击'
    Agile = '灵活'
    Prepared = '预备'
    Guard = '守护'
    Guarded = '被守护'
    TimeWarp = '穿梭'
    Deploy = '部署'          # 仅作展示用词条，行为改由 effects 表达
    Deathrattle = '亡计'     # 同上
    Passive = '_被动效果'


@dataclass
class Tag():
    keyword: Keyword
    value: str | int | None = None

# classes/Card.py
from .CommandEffect import Effect

class Card():
  def __init__(self, cost_: int, tags_: list[Tag], name_: str, owner_: str,
              timeline: Literal[0, 1, 2],
              effects_: tuple[Effect, ...] = ()) -> None:
    self.cost = cost_
    self.tags = tags_
    self.name = name_
    self.owner = owner_
    self.timeline: Literal[0, 1, 2] = timeline
    self.effects: tuple[Effect, ...] = effects_

class CommandCard(Card):
  def __init__(self, cost_: int, tags_: list[Tag], name_: str, owner_: str,
              effects_: tuple[Effect, ...], dect_: str,
              tl: Literal[0, 1, 2]) -> None:
    super().__init__(cost_, tags_, name_, owner_, tl, effects_)
    self.dect = dect_











class PassiveType(Enum):
  TakeDamage = '受伤'
  Attack = '造成伤害'
  N = None

class ClacType(Enum):
  LLimit = '至少'
  MLimit = '至多'
  Add = '+'
  Sub = '-'
  Time = '*'
  N = None

@dataclass
class PassiveTag(Tag):
  PT : PassiveType = PassiveType.N
  CT : ClacType = ClacType.N
  keyword : Keyword = Keyword.Passive
