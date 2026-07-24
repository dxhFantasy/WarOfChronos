#操作记录，可以用于服务器数据同步，没写完

from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
  DrawCard = '抽牌'
  PlayCard = '出牌'
  ...


@dataclass
class LogEntry:
  '''单条操作记录'''
  TurnNumber : int
  actionType : ActionType
  
  targetIds : list[str]

