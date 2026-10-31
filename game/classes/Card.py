from __future__ import annotations
from enum import Enum
from enum import Enum
from dataclasses import dataclass
from typing import Literal, TypeAlias
#from abc import ABC
from typing import Literal

Timeline: TypeAlias = Literal[0, 1, 2]

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
              timeline: Timeline | list[Timeline],
              effects_: tuple[Effect, ...] = ()) -> None:
    self.cost = cost_
    self.tags = tags_
    self.name = name_
    self.owner = owner_
    if isinstance(timeline, list):
      self.timelines: list[Timeline] = list(timeline)
    else:
      self.timelines = [timeline]
    # 兼容旧代码：需要单个时间线时默认取第一个
    self.timeline: Timeline = self.timelines[0]
    self.effects: tuple[Effect, ...] = effects_

class CommandCard(Card):
  def __init__(self, cost_: int, tags_: list[Tag], name_: str, owner_: str,
              effects_: tuple[Effect, ...], dect_: str,
              tl: Timeline | list[Timeline]) -> None:
    super().__init__(cost_, tags_, name_, owner_, tl, effects_)
    self.dect = dect_











class PassiveType(Enum):
  TakeDamage = '受伤'
  Attack = '造成伤害'
  HqAttack = '攻击总部'
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
