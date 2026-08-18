from enum import Enum
from dataclasses import dataclass

class Keyword(Enum):
  Blitz = '闪击'
  Agile = '灵活'
  Prepared = '预备'
  Guard = '守护'
  Guarded = '被守护'
  TimeWarp = '穿梭'
  Deploy = '部署'
  Deathrattle = '亡计'
  Passive = '_被动效果'

@dataclass
class Tag():
  keyword : Keyword
  value : str | int | None = None

@dataclass
class f(Tag):
  ...
