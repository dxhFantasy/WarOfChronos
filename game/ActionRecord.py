#操作记录，可以用于服务器数据同步

from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
  DrawCard = '抽牌'
  PlayCard = '出牌'
  AddAtk = '获得攻击力'
  AddDef = '获得防御力'
  Attack = '攻击'

  ...

@dataclass
class Action:
  actionType : ActionType    #操作类型
  value : int #操作数值 如获得1攻击力

@dataclass
class LogEntry:
  '''单条操作记录'''
  TurnNumber : int   #第几回合
  actorPlayer : str    #A/B方操作
  actions = list[Action]   #具体操作
  actorId : int | str    #发起该操作的单位Id 若为指令则为指令卡牌名称
  targetIds : list[str] | None     #目标Id列表
  changeEvent : list[int] | None #改变的事件 若无则None

if __name__ == '__main__':
  log = LogEntry()




