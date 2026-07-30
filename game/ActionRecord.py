#操作记录，可以用于服务器数据同步，测试版本0.2？

from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
  DrawCard = '抽牌'
  PlayCard = '出牌'
  AddAtk = '获得攻击力'
  AddDef = '获得防御力'
  TakeDamage = '受到伤害'
  Attack = '攻击'
  TurnStart = '回合开始'
  TurnEnd = '回合结束'

  ...


@dataclass
class LogEntry:
  '''单条操作记录'''
  TurnNumber : int   #第几回合
  actorPlayer : str    #A/B方操作
  actionType : ActionType 
  actorId : int | None #发起该操作的单位Id 若为指令则为指令卡牌id
  target : int | None #操作目标 如攻击目标

if __name__ == '__main__':
  ...



