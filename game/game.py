
# from game.classes.CardsPort import KardsPort
from .Battlefield import *
from .Player import *
from .Cards import *
from .ActionRecord import *

from typing import Any,Literal,cast
from copy import deepcopy
from collections.abc import Mapping, Sequence
from dataclasses import fields

from .classes.CommandEffect import (
    Action, CardType, Condition, Effect, EntityId, EvalContext, EventType,
    GameEvent, GamePort, Interpreter, Pick, PlayerId, Selection, Side, StatKind,
    UnitType as EffectUnitType, Zone,
    OP_ACTION_COST, OP_ADD_TO_HAND, OP_AP, OP_AP_SLOT, OP_CHANGE_EVENT,
    OP_SET_ACTION_COST, OP_SET_AP, OP_SET_AP_SLOT, OP_SET_ATTACK,
    OP_SET_HEALTH, OP_SHUFFLE, OP_TO_BOTTOM, OP_TO_TOP,
)




def FindKeyw(u : Unit,k : Keyword) -> int | None:
  for t in u.tags:
    if t.keyword == k:
      return u.tags.index(t)
  return None

def CheckTimeWarp(cardId : int) -> bool:
  card : UnitCard | CommandCard = allCards[cardId]
  for t in card.tags:
    if t.keyword == Keyword.TimeWarp:
      return True
  return False


def GetAgileCount(u : Unit) -> int:
  idx = FindKeyw(u, Keyword.Agile)
  if idx is None:
    return 0
  value = u.tags[idx].value
  if isinstance(value, int) and value > 0:
    return value
  return 1


def IsRangedUnit(u : Unit) -> bool:
  return u.uType in (UnitType.bomber, UnitType.artillery, UnitType.fighter)


def FindChosenSelection(node : Any) -> Selection | None:
  '''递归找出手牌效果里用“指定”方式选择的目标选择器'''
  if isinstance(node, Selection):
    return node if node.pick is Pick.CHOSEN else None
  if isinstance(node, (list, tuple)):
    for item in cast(Sequence[Any], node):
      found = FindChosenSelection(item)
      if found is not None:
        return found
    return None
  if isinstance(node, (Action, Condition, Effect)):
    for f in fields(cast(Any, node)):
      if f.name.startswith('_'):
        continue
      found = FindChosenSelection(getattr(node, f.name))
      if found is not None:
        return found
  return None


DEBUG = 1


HQ_A = -1
HQ_B = -2

def UnitRef(uid: int) -> EntityId:
    return f"unit:{uid}"

def HqRef(player: PlayerId) -> EntityId:
    return f"hq:{player}"

def IsHqRef(ref: EntityId) -> bool:
    return ref.startswith("hq:")

def HqOwner(ref: EntityId) -> PlayerId:
    return ref.split(":", 1)[1]

def ParseUnitId(ref: EntityId) -> int | None:
    if IsHqRef(ref):
        return None
    try:
        return int(ref.split(":", 1)[1])
    except (IndexError, ValueError):
        return None


DA = 0
F = 1
DB = 2

E1 = 0
E2 = 1
E3 = 2
E4 = 3

PLAYER_A : str= 'A'
PLAYER_B : str= 'B'

@dataclass
class GameState():
  playerA : Player
  playerB : Player
  battlefields : list[Battlefield]
  cbf : Literal[0,1,2]
  evt : list[bool]




class Result:
  def __init__(self, state : Literal['ok','err'],msg : str | None = None, gameState : GameState | None = None) -> None:
    self.state : Literal['ok','err'] = state
    if(self.state == 'ok'):
      self.gameState = gameState
    else:
      self.msg = msg

from .classes.CommandEffect import Interpreter, GameEvent, EventType

class Game(GamePort):
  def __init__(self) -> None:

    self.choiceQueue: list[int | None] = []
    self.effectInterp = Interpreter(self)

    self.playerA : Player = Player(0,0,[],[],30,'A')
    self.playerB : Player = Player(0,0,[],[],30,'B')

    self.playerA.deck = cardIds[0:len(cardIds)//2-1]
    self.playerB.deck = cardIds[len(cardIds)//2:len(cardIds)-1]

    if DEBUG:
      self.playerA.apSlot = 12
      self.playerB.apSlot = 12

    self.lastId = 0

    self.moved : list[int] = []
    self.attacked : list[int] = []
    self.attackedByAction : list[int] = []
    self.deployedThisTurn : list[int] = []



    self.currentPlayer = 'A'
    self.totalTurn = 0

    self.battlefields : list[Battlefield] = [
      Battlefield(0,[Frontline(6),Frontline(4),Frontline(6)])
      for _ in range(3)
    ]

    self.currentBF : Literal[0,1,2] = 1

    self.events : list[bool] = [True,True,True,False]

    random.shuffle(self.playerA.deck)
    random.shuffle(self.playerB.deck)
    self.effectInterp = Interpreter(self)
    if __name__ == '__main__':
      self.InitDraw()

  def InitDraw(self) -> GameState:
    self.DrawCard('A',5)
    self.DrawCard('B',6)
    state = self.GetState()
    return state


  def GetPlayer(self,player : str) -> Player | None:
    if player != 'N':
      return self.playerB if player == 'B' else self.playerA
    else:
      return None
    
  def GetUnitById(self,uid : int | None) -> Unit | None:
    for fl in self.battlefields[self.currentBF].frontlines:
      for u in fl.targets:
        if u.id == uid:
          return u
  
  def GetFlById(self,uid : int | None) -> int | None:
    for fl in self.battlefields[self.currentBF].frontlines:
      for u in fl.targets:
        if u.id == uid:
          return self.battlefields[self.currentBF].frontlines.index(fl)

  def IsTurn(self,player : str) -> bool:
    '''A 在奇数回合行动，B 在偶数回合行动（与 game_session 保持一致）'''
    return (self.totalTurn % 2 == 1) if player == 'A' else (self.totalTurn % 2 == 0)

  def GetCardTags(self,cardId : int) -> list[str]:
    return [t.keyword.value for t in allCards[cardId].tags]

  def GetCardTimelines(self,cardId : int) -> list[int]:
    return [int(t) for t in allCards[cardId].timelines]

  def IsTimeWarpCard(self,cardId : int) -> bool:
    return CheckTimeWarp(cardId)

  def GetTargetKind(self,cardId : int) -> str | None:
    '''返回指令需要的目标类型，例如 enemy_unit / friendly_hq / any_any'''
    card = allCards[cardId]
    selection = FindChosenSelection(getattr(card,'effects',()))
    if selection is None:
      return None
    if selection.owner is Side.ENEMY:
      side = 'enemy'
    elif selection.owner is Side.FRIENDLY:
      side = 'friendly'
    else:
      side = 'any'
    if selection.zone is Zone.HQ:
      zone = 'hq'
    elif selection.zone is Zone.ANY:
      zone = 'any'
    else:
      zone = 'unit'
    return f'{side}_{zone}'

  def CheckCommandTarget(self,cardId : int,player : str,target : int | None) -> str | None:
    '''检查指向性指令的目标是否合法，返回错误信息或 None'''
    kind = self.GetTargetKind(cardId)
    if kind is None:
      return None
    if target is None:
      return '目标未指定'
    side,zone = kind.split('_')
    if zone == 'unit' and target in (HQ_A,HQ_B):
      return '目标必须是单位'
    if zone == 'hq' and target not in (HQ_A,HQ_B):
      return '目标必须是总部'
    if target in (HQ_A,HQ_B):
      owner = 'A' if target == HQ_A else 'B'
    else:
      u = self.GetUnitById(target)
      if u is None:
        return '目标不存在'
      owner = u.owner
      selection = FindChosenSelection(getattr(allCards[cardId],'effects',()))
      if selection is not None and not self.effectInterp.MatchesFilters(UnitRef(target),selection):
        return '目标不合法'
    if side == 'enemy' and owner == player:
      return '目标必须是敌方'
    if side == 'friendly' and owner != player:
      return '目标必须是友方'
    return None

  def HasEnemyFighter(self,fl : Frontline,player : str) -> bool:
    for u in fl.targets:
      if u.owner != player and u.uType == UnitType.fighter:
        return True
    return False

  def FrontlineHasEnemy(self,fl : Frontline,player : str) -> bool:
    '''前线是否还有敌方单位；有敌方单位时不能进入前线'''
    for u in fl.targets:
      if u.owner != player and u.dfns > 0:
        return True
    return False

  def FrontlineHasGuard(self,fl : Frontline,owner : str) -> bool:
    for u in fl.targets:
      if u.owner == owner and u.dfns > 0 \
          and FindKeyw(u,Keyword.Guard) is not None:
        return True
    return False

  def HqIsGuarded(self,owner : str) -> bool:
    '''底线（指挥阵线）有存活守护单位时，总部视为被守护'''
    base = DA if owner == 'A' else DB
    return self.FrontlineHasGuard(
      self.battlefields[self.currentBF].frontlines[base], owner)

  def GetMoveTargets(self,u : Unit | None,player : str) -> list[int]:
    '''返回本单位本回合可以移动到的阵线下标'''
    if u is None or u.owner != player or not self.IsTurn(player):
      return []
    if u.id in self.attackedByAction and u.uType != UnitType.tank:
      return []
    if u.id in self.deployedThisTurn:
      return []
    agile = GetAgileCount(u)
    moveLimit = agile if agile > 0 else 1
    if self.moved.count(u.id) >= moveLimit:
      return []
    p = self.GetPlayer(player)
    if p is None or p.actionPoint < u.actionCost:
      return []
    ownBase = DA if player == 'A' else DB
    bf = self.battlefields[self.currentBF]
    if u.fl == ownBase:
      frontline = bf.frontlines[F]
      if len(frontline.targets) < frontline.maxTargets \
          and not self.FrontlineHasEnemy(frontline,player):
        return [F]
    elif u.fl == F and agile > 0:
      if len(bf.frontlines[ownBase].targets) < bf.frontlines[ownBase].maxTargets:
        return [ownBase]
    return []

  def GetAttackTargets(self,u : Unit | None,player : str) -> tuple[list[int], bool]:
    '''返回 (可攻击单位 id 列表, 是否可攻击敌方总部)'''
    if u is None or u.owner != player or not self.IsTurn(player):
      return ([],False)
    if u.id in self.attacked:
      return ([],False)
    if u.uType != UnitType.tank and self.moved.count(u.id) > 0:
      return ([],False)
    p = self.GetPlayer(player)
    if p is None or p.actionPoint < u.actionCost:
      return ([],False)
    bf = self.battlefields[self.currentBF]
    ranged = IsRangedUnit(u)
    ownBase = DA if player == 'A' else DB
    enemyBase = DB if player == 'A' else DA
    enemyPlayer = 'B' if player == 'A' else 'A'
    targets : list[int] = []
    for fl_idx,fl in enumerate(bf.frontlines):
      for t in fl.targets:
        if t.owner == player or t.dfns <= 0:
          continue
        if not ranged:
          if u.fl == F:
            pass
          elif u.fl == ownBase and fl_idx == F:
            pass
          else:
            continue
        if FindKeyw(t,Keyword.Guarded) is not None and not ranged:
          continue
        if u.uType == UnitType.bomber and self.HasEnemyFighter(fl,player):
          continue
        targets.append(t.id)
    canHq = ranged or u.fl == F
    if canHq and self.HqIsGuarded(enemyPlayer) \
        and u.uType not in (UnitType.bomber,UnitType.artillery):
      canHq = False
    if u.uType == UnitType.bomber and self.HasEnemyFighter(bf.frontlines[enemyBase],player):
      canHq = False
    return (targets,canHq)

  def MoveUnit(self,u : Unit,targetFl : int,player : str) -> None:
    bf = self.battlefields[self.currentBF]
    src = bf.frontlines[u.fl]
    dst = bf.frontlines[targetFl]
    src.targets.pop(src.targets.index(u))
    dst.targets.append(u)
    u.fl = targetFl
    self.moved.append(u.id)
    if u.uType != UnitType.tank:
      self.attacked.append(u.id)
    p = self.GetPlayer(player)
    if p is not None:
      p.actionPoint -= u.actionCost
    self.RefreshGuarded()

  def AttackUnit(self,u : Unit,target : int,player : str) -> None:
    p = self.GetPlayer(player)
    if p is not None:
      p.actionPoint -= u.actionCost
    self.attacked.append(u.id)
    self.attackedByAction.append(u.id)
    if u.uType != UnitType.tank:
      self.moved.append(u.id)
    self.Attack(u,target)

  def RefreshGuarded(self) -> None:
    '''守护：给同一阵线内同阵营的非守护单位挂上“被守护”'''
    for bf in self.battlefields:
      for fl in bf.frontlines:
        guards : set[str] = set()
        for u in fl.targets:
          if FindKeyw(u,Keyword.Guard) is not None:
            guards.add(u.owner)
        for u in fl.targets:
          idx = FindKeyw(u,Keyword.Guarded)
          should = (u.owner in guards) and (FindKeyw(u,Keyword.Guard) is None)
          if should and idx is None:
            u.tags.append(Tag(Keyword.Guarded))
          elif not should and idx is not None:
            u.tags.pop(idx)
  
  
  def ChangeEvent(self,eid : Literal[0,1,2,3]) -> None:
    self.events[eid] = not self.events[eid]
    if eid == E1:
      pass
    elif eid == E2:
      if not self.events[eid]:
        for fl in self.battlefields[A].frontlines:
          for u in fl.targets:
            u.atk += 2
            u.dfns += 2
        for fl in self.battlefields[B].frontlines:
          for u in fl.targets:
            u.atk -= 1
            u.dfns -= 1
        for fl in self.battlefields[C].frontlines:
          for u in fl.targets:
            u.atk -= 1
            u.dfns -= 1
      else:
        for fl in self.battlefields[A].frontlines:
          for u in fl.targets:
            u.atk -= 2
            u.dfns -= 2
        for fl in self.battlefields[B].frontlines:
          for u in fl.targets:
            u.atk += 1
            u.dfns += 1
        for fl in self.battlefields[C].frontlines:
          for u in fl.targets:
            u.atk += 1
            u.dfns += 1
    elif eid == E3:
      if not self.events[eid]:
        for fl in self.battlefields[B].frontlines:
          for u in fl.targets:
            u.atk -= 1
            u.dfns -= 1
      else:
        for fl in self.battlefields[B].frontlines:
          for u in fl.targets:
            u.atk += 1
            u.dfns += 1
    elif eid == E4:
      if self.events[eid]:
        for fl in self.battlefields[B].frontlines:
          for u in fl.targets:
            u.actionCost = u.actionCost - 1 if u.actionCost >= 1 else 0
        for fl in self.battlefields[C].frontlines:
          for u in fl.targets:
            u.atk -= 3
            u.dfns -= 2
      else:
        for fl in self.battlefields[B].frontlines:
          for u in fl.targets:
            u.actionCost += 1
        for fl in self.battlefields[C].frontlines:
          for u in fl.targets:
            u.atk += 3
            u.dfns += 2
    self.RefreshHandCosts()


  def HandCost(self,hc : HandCard) -> int:
    '''手牌当前费用：三战开启时，A 时间线的手牌 -2 费'''
    cost = allCards[hc.id].cost
    if self.events[E4] and A in allCards[hc.id].timelines:
      cost = max(0,cost - 2)
    return cost

  def RefreshHandCosts(self) -> None:
    for p in (self.playerA,self.playerB):
      for hc in p.handCards:
        hc.cost = self.HandCost(hc)

  def DrawCard(self,player : str,num : int) -> None:
    playerT = self.GetPlayer(player)
    if playerT:
      for _ in range(num):
        if len(playerT.deck) != 0 :
          temp : HandCard = CardToHand(playerT.deck.pop())
          temp.cost = self.HandCost(temp)
          playerT.handCards.append(temp)
        else:
          playerT.hq -= 3

  def TimeWarp(self,t : int) -> None:
    if t not in (A,B,C):
      raise Exception('不存在的时间线')
    self.currentBF = t

  def Deploy(self, u : Unit, fl : int, player : Literal['A' , 'B']) -> None:
    if fl == F and self.FrontlineHasEnemy(
        self.battlefields[self.currentBF].frontlines[F], player):
      raise Exception('前线被敌方占领，请先清空')

    if not self.events[E2]:  # 第二次世界大战：关闭
      if u.utl == 0:
        u.atk += 2
        u.dfns += 2
      else:
        u.atk -= 1
        u.dfns -= 1

    if not self.events[E3]:  # 美苏冷战：关闭
      if u.utl == 1:
        u.atk -= 1
        u.dfns -= 1

    if self.events[E4]:      # 三战：开启
      if u.utl == 1:
        u.actionCost -= 1
      if u.utl == 2:
        u.atk -= 3
        u.dfns -= 2

    u.owner = player
    self.battlefields[self.currentBF].frontlines[fl].targets.append(u)

    if(FindKeyw(u, Keyword.Blitz) is None):
      self.attacked.append(u.id)
      self.moved.append(u.id)
      self.deployedThisTurn.append(u.id)

    # —— 新：挂载卡牌效果 + 派发部署事件 ——
    card = allCards[u.cardId]
    assert isinstance(card, UnitCard)
    ref = UnitRef(u.id)
    self.effectInterp.AttachCard(card, u.owner, ref)          # 触发 SELF_DEPLOYED（部署效果）
    self.effectInterp.HandleEvent(                            # 触发全场监听（UNIT_DEPLOYED）
        GameEvent(EventType.UNIT_DEPLOYED, actor=u.owner, subject=ref))
    self.RefreshGuarded()

  

  def Attack(self, u : Unit, tid : int | None) -> None:
    # 攻击方视角的上下文，供 Port 使用
    ctx = self.effectInterp.MakeContext(u.owner, UnitRef(u.id))

    if tid in (HQ_A, HQ_B):                       # 攻击总部
      hqOwner = 'A' if tid == HQ_A else 'B'
      if self.HqIsGuarded(hqOwner) \
          and u.uType not in (UnitType.bomber, UnitType.artillery):
        raise Exception('敌方总部被守护')
      atk = ClacAtk(u.tags, u.atk)
      target = HqRef('A') if tid == HQ_A else HqRef('B')
      self.effectInterp.port.DealDamage(UnitRef(u.id), target, atk, ctx)
      return

    t = self.GetUnitById(tid)                     # 攻击单位
    if t is None:
      raise Exception('你不能攻击滚木')
    if FindKeyw(t, Keyword.Guarded) is not None:
      if u.uType not in (UnitType.bomber, UnitType.artillery):
        raise Exception('此单位被守护')

    atk = ClacAtk(u.tags, u.atk)
    self.effectInterp.port.DealDamage(UnitRef(u.id), UnitRef(t.id), atk, ctx)

    # 受到反击伤害
    if t.uType != UnitType.bomber and u.uType not in (UnitType.bomber, UnitType.artillery):
      fAtk = t.atk
      self.effectInterp.port.DealDamage(UnitRef(t.id), UnitRef(u.id), fAtk, ctx)



  def UseCommand(self, player : Player, command : CommandCard, tid : int | None) -> None:
    self.choiceQueue.clear()
    if tid is not None:
      self.choiceQueue.append(tid)
    self.effectInterp.AttachCard(command, player.name, None)




  def ReceiveRecord(self) -> None:
    ...#疑似肺雾函数
    #self.ProcessRecord(...)
  
  def ProcessRecord(self,entry : LogEntry) -> Result:
    eType = entry.actionType
    result : Result
    player = entry.actorPlayer
    try:
      playerStruct = self.GetPlayer(player)
      if(not playerStruct):
          raise Exception('什么叫滚木在执行操作')
      if(eType == ActionType.DrawCard):
        if(entry.target is None):
          raise Exception('未给出抽牌数量')
        self.DrawCard(entry.actorPlayer,entry.target)
      elif(eType == ActionType.UseCommand):
        if entry.actorId is None:
          raise Exception('不能使用滚木指令')
        if entry.handCardIdx is None:
          raise Exception('不能用滚木手牌凭空使用指令')
        if entry.handCardIdx < 0 or entry.handCardIdx >= len(playerStruct.handCards):
          raise Exception('手牌索引不存在')
        handCard = playerStruct.handCards[entry.handCardIdx]
        if handCard.id != entry.actorId:
          raise Exception('手牌与指令不匹配')
        card : CommandCard = allCards[entry.actorId] # type: ignore
        if self.currentBF not in card.timelines:
          raise Exception('禁止出现超时空战士')
        if type(card) != CommandCard:
          raise Exception('单位不能当作指令使用 前端在干嘛')
        if playerStruct.actionPoint < handCard.cost:
          raise Exception('行动点不足')
        targetErr = self.CheckCommandTarget(entry.actorId,player,entry.target)
        if targetErr is not None:
          raise Exception(targetErr)
        self.UseCommand(playerStruct,card,entry.target)
        playerStruct.actionPoint -= handCard.cost
        playerStruct.handCards.pop(entry.handCardIdx)
        ...# 重点
      elif(eType == ActionType.Deploy):
        if(entry.actorId is None):
          raise Exception('不能部署滚木')
        if entry.handCardIdx is None:
          raise Exception('不能用滚木手牌部署单位')
        if entry.handCardIdx < 0 or entry.handCardIdx >= len(playerStruct.handCards):
          raise Exception('手牌索引不存在')
        handCard = playerStruct.handCards[entry.handCardIdx]
        if handCard.id != entry.actorId:
          raise Exception('手牌与单位不匹配')
        if(self.currentBF not in allCards[entry.actorId].timelines): # type: ignore
          print("TEST",allCards[entry.actorId],self.currentBF) # type: ignore
          raise Exception('禁止出现超时空战士')
        if playerStruct.actionPoint < handCard.cost:
          raise Exception('行动点不足')
        unitCard = allCards[entry.actorId]
        if(type(unitCard) != UnitCard):
          raise Exception('不能部署指令，啥子比。')
        assert type(unitCard) == UnitCard
        if entry.target is None:
          raise Exception('未选择部署阵线')

        if ((player == 'A' and entry.target == DB) or (player == 'B' and entry.target == DA)):
          raise Exception('单位不能放对面家里')
        elif (entry.target == F and FindKeyw(CardToUnit(unitCard),Keyword.Prepared) is not None) or \
              ((player == 'A' and entry.target == DA) or (player == 'B' and entry.target == DB)):
          if len(self.battlefields[self.currentBF].frontlines[entry.target].targets)\
              >= self.battlefields[self.currentBF].frontlines[entry.target].maxTargets:
            raise Exception('指挥阵线已满')
          newUnit = CardToUnit(unitCard, self.currentBF)
          newUnit.id = self.lastId + 1
          self.lastId += 1
          assert entry.actorPlayer in ('A', 'B')
          newUnit.owner = entry.actorPlayer
          newUnit.fl = entry.target
          self.Deploy(newUnit,entry.target, entry.actorPlayer)
          playerStruct.actionPoint -= handCard.cost
          playerStruct.handCards.pop(entry.handCardIdx)
          

        else: 
          print('TEXT',player,entry.target)
          raise Exception('不是你放单位给我放好的呀')
          
      elif(eType == ActionType.TurnEnd):
        
        self.TurnEnd(entry.actorPlayer)
      elif eType == ActionType.Move:
        u = self.GetUnitById(entry.actorId)
        if u is None:
          raise Exception('为什么滚木在移动？')
        if u.owner != player:
          raise Exception('不能移动敌方单位')
        if entry.target is None:
          raise Exception('未选择移动位置')
        if u.id in self.attackedByAction and u.uType != UnitType.tank:
          raise Exception('本单位本回合不能移动')
        if u.id in self.deployedThisTurn:
          raise Exception('本单位本回合不能移动')
        agile = GetAgileCount(u)
        moveLimit = agile if agile > 0 else 1
        if self.moved.count(u.id) >= moveLimit:
          raise Exception('本单位本回合不能移动')
        if playerStruct.actionPoint < u.actionCost:
          raise Exception('行动点不足')
        targets = self.GetMoveTargets(u,player)
        if entry.target not in targets:
          if entry.target == F and self.FrontlineHasEnemy(
              self.battlefields[self.currentBF].frontlines[F], player):
            raise Exception('前线被敌方占领，请先清空')
          if entry.target == F and len(self.battlefields[self.currentBF].frontlines[F].targets)\
              >= self.battlefields[self.currentBF].frontlines[F].maxTargets:
            raise Exception('前线已满')
          if u.fl == F:
            raise Exception('前线单位不能移出前线')
          raise Exception('本单位不能移动到该阵线')
        self.MoveUnit(u,entry.target,player)
      elif eType == ActionType.Attack:
        u = self.GetUnitById(entry.actorId)
        if(u is None):
          raise Exception('你不能指挥滚木攻击')
        if u.owner != player:
          raise Exception('不能指挥敌方单位攻击')
        if entry.target is None:
          raise Exception('未选择攻击目标')
        if u.id in self.attacked:
          raise Exception('本单位本回合不能攻击')
        if u.uType != UnitType.tank and self.moved.count(u.id) > 0:
          raise Exception('本单位本回合不能攻击')
        if playerStruct.actionPoint < u.actionCost:
          raise Exception('行动点不足')
        enemyHq = HQ_B if player == 'A' else HQ_A
        enemyPlayer = 'B' if player == 'A' else 'A'
        targets,canHq = self.GetAttackTargets(u,player)
        if entry.target in (HQ_A,HQ_B):
          if entry.target != enemyHq:
            raise Exception('不能攻击友方总部')
          if not canHq:
            if self.HqIsGuarded(enemyPlayer) \
                and u.uType not in (UnitType.bomber,UnitType.artillery):
              raise Exception('敌方总部被守护')
            raise Exception('攻击距离不足')
        elif entry.target not in targets:
          t = self.GetUnitById(entry.target)
          if t is None:
            raise Exception('目标不存在')
          if FindKeyw(t,Keyword.Guarded) is not None and not IsRangedUnit(u):
            raise Exception('此单位被守护')
          raise Exception('攻击距离不足')
        self.AttackUnit(u,entry.target,player)
        

      
      result = Result('ok',gameState=self.GetState())

    except Exception as err:
      s = str(err)
      debug(s)
      result = Result('err',msg=s)
      
    
    return result

  def Check(self) -> None:
    for bf in self.battlefields:
      for fl in bf.frontlines:
        for u in list(fl.targets):
          if(u.dfns <= 0):
            ref = UnitRef(u.id)
            self.effectInterp.HandleEvent(
              GameEvent(EventType.UNIT_DESTROYED, actor=u.owner, subject=ref))
            self.effectInterp.DetachHost(ref)
            fl.targets.pop(fl.targets.index(u))
      bf.unitsNum = sum(len(fl.targets) for fl in bf.frontlines)
    self.RefreshGuarded()


  def GetState(self) -> GameState:
    self.Check()
    state = GameState(
      deepcopy(self.playerA),\
      deepcopy(self.playerB),\
      deepcopy(self.battlefields),\
      self.currentBF,\
      deepcopy(self.events)
    )
    return state


  def GetWinner(self) -> Literal['A','B','draw'] | None:
    '''返回胜利方；双方同时被摧毁时为平局'''
    a = self.playerA.hq
    b = self.playerB.hq
    if a <= 0 and b <= 0:
      return 'draw'
    if a <= 0:
      return 'B'
    if b <= 0:
      return 'A'
    return None


  def TurnStart(self, lastTurnPlayer : str) -> None:
    nextPlayer = 'B' if lastTurnPlayer == 'A' else 'A'
    self.moved.clear()
    self.attacked.clear()
    self.attackedByAction.clear()
    self.deployedThisTurn.clear()
    self.effectInterp.HandleEvent(
    GameEvent(EventType.TURN_STARTED, actor=nextPlayer))
    # for c in self.clocks:
    #   if c.Time.turnTime == TURN_START:
    #     if c.Time.turnCount == 0:
    #       if c.info == START:
    #         self.ApplyEffects(c.targets,c.effect.effect,c.effect.value,c.player)
    #       elif c.info == END:
    #         self.DeleteEffects(c.targets,c.effect.effect,c.effect.value,c.player)
    #       self.clocks.pop(self.clocks.index(c))
    #     else:
    #       c.Time.turnCount -= 1

    if(lastTurnPlayer == 'A'):
      self.DrawCard('B',1)
      self.playerB.apSlot += 1
      self.playerB.actionPoint = self.playerB.apSlot
      if not self.events[0] :
        self.playerB.actionPoint -= 1
      if not self.events[2] :
        self.playerB.actionPoint += 2
    else:
      self.DrawCard('A',1)
      self.playerA.apSlot += 1
      self.playerA.actionPoint = self.playerA.apSlot
      if not self.events[0] :
        self.playerA.actionPoint -= 1
      if not self.events[2] :
        self.playerA.actionPoint += 2
    ...
    



    


  def TurnEnd(self, player : str) -> None:
      self.effectInterp.HandleEvent(
        GameEvent(EventType.TURN_ENDED, actor=player))
      self.TurnStart(player)
  

    # ==========================================================
  # GamePort 实现
  # ==========================================================

  # ---------------- 查询 ----------------

  def GetHQ(self, player: PlayerId) -> EntityId:
    return HqRef(player)

  def ListEntities(self, player: PlayerId, zone: Zone) -> Sequence[EntityId]:
    if zone is Zone.BOARD:
      bf = self.battlefields[self.currentBF]
      return [UnitRef(u.id) for fl in bf.frontlines
              for u in fl.targets if u.owner == player]
    return []


  def GetStat(self, entity: EntityId, stat: StatKind) -> int:
    if IsHqRef(entity):
      player = self.GetPlayer(HqOwner(entity))
      if player is None:
        return 0
      return player.hq if stat is StatKind.HEALTH else 0

    u = self.GetUnitById(ParseUnitId(entity))
    if u is None:
      return 0
    if stat is StatKind.ATTACK:
      return u.atk
    if stat is StatKind.HEALTH:
      return u.dfns
    if stat is StatKind.COST:
      return u.cost
    if stat is StatKind.ACTION_COST:
      return u.actionCost
    if stat is StatKind.FRONTLINE:
      return u.fl
    if stat is StatKind.TIMELINE:
      return u.utl
    return 0

  def GetKeywords(self, entity: EntityId) -> frozenset[str]:
    u = self.GetUnitById(ParseUnitId(entity))
    if u is None:
      return frozenset()
    return frozenset(t.keyword.value for t in u.tags)

  def GetCardType(self, entity: EntityId) -> CardType:
    return CardType.HQ if IsHqRef(entity) else CardType.UNIT

  def GetUnitType(self, entity: EntityId) -> EffectUnitType:
    u = self.GetUnitById(ParseUnitId(entity))
    if u is None:
      return EffectUnitType.NONE
    try:
      return EffectUnitType(u.uType.value)
    except ValueError:
      return EffectUnitType.NONE

  def IsAlive(self, entity: EntityId) -> bool:
    if IsHqRef(entity):
      return True
    u = self.GetUnitById(ParseUnitId(entity))
    return u is not None and u.dfns > 0

  def OpponentOf(self, player: PlayerId) -> PlayerId:
    return 'B' if player == 'A' else 'A'

  def Choose(self, candidates: Sequence[EntityId],
             ctx: EvalContext) -> EntityId | None:
    while self.choiceQueue:
      tid = self.choiceQueue.pop(0)
      if tid is None:
        continue
      ref = HqRef('A') if tid == HQ_A else (
        HqRef('B') if tid == HQ_B else UnitRef(tid))
      if ref in candidates:
        return ref
      raise Exception('目标不合法')
    return None

  # ---------------- 操作 ----------------

  def DealDamage(self, source: EntityId | None, target: EntityId,
                 amount: int, ctx: EvalContext) -> None:
    if IsHqRef(target):
      player = self.GetPlayer(HqOwner(target))
      if player is None:
        return
      player.hq -= amount
      self.effectInterp.HandleEvent(
        GameEvent(EventType.HQ_DAMAGED, subject=target, data={'数值': amount}))
      return

    u = self.GetUnitById(ParseUnitId(target))
    if u is None or u.dfns <= 0:
      return
    dmg = ClacDamage(u.tags, amount)          # 被动减伤在这里生效
    u.dfns -= dmg
    self.effectInterp.HandleEvent(
      GameEvent(EventType.UNIT_DAMAGED, actor=u.owner,
                subject=target, data={'数值': dmg}))

  def Heal(self, target: EntityId, amount: int, ctx: EvalContext) -> None:
    if IsHqRef(target):
      player = self.GetPlayer(HqOwner(target))
      if player is not None:
        player.hq += amount
      return

    u = self.GetUnitById(ParseUnitId(target))
    if u is None:
      return
    u.dfns += amount
    self.effectInterp.HandleEvent(
      GameEvent(EventType.UNIT_HEALED, actor=u.owner,
                subject=target, data={'数值': amount}))

  def Destroy(self, target: EntityId, ctx: EvalContext) -> None:
    u = self.GetUnitById(ParseUnitId(target))
    if u is None:
      return
    u.dfns = -1
    self.Check()                              # 统一走 Check，亡计/守护刷新都在那里

  def DrawCards(self, player: PlayerId, amount: int, ctx: EvalContext) -> None:
    self.DrawCard(player, amount)
    self.effectInterp.HandleEvent(
      GameEvent(EventType.CARD_DRAWN, actor=player, data={'数值': amount}))

  def Discard(self, entity: EntityId, ctx: EvalContext) -> None:
    return                                    # 手牌不是实体，暂不实现

  def ModifyStats(self, entity: EntityId, attack: int, health: int,
                   ctx: EvalContext) -> None:
    u = self.GetUnitById(ParseUnitId(entity))
    if u is None:
      return
    u.atk = max(0, u.atk + attack)
    u.dfns += health

  def GrantKeyword(self, entity: EntityId, keyword: str,
                   ctx: EvalContext) -> None:
    u = self.GetUnitById(ParseUnitId(entity))
    if u is None:
      return
    try:
      kw = Keyword(keyword)
    except ValueError:
      return
    idx = FindKeyw(u, kw)
    if idx is None:
      u.tags.append(Tag(kw))
      self.effectInterp.HandleEvent(
        GameEvent(EventType.KEYWORD_GAINED, actor=u.owner,
                  subject=entity, data={'数值': 1}))

  def RevokeKeyword(self, entity: EntityId, keyword: str,
                    ctx: EvalContext) -> None:
    u = self.GetUnitById(ParseUnitId(entity))
    if u is None:
      return
    try:
      kw = Keyword(keyword)
    except ValueError:
      return
    idx = FindKeyw(u, kw)
    if idx is not None:
      u.tags.pop(idx)

  def Summon(self, player: PlayerId, cardId: str, ctx: EvalContext) -> None:
    try:
      card = allCards[int(cardId)]
    except (ValueError, IndexError):
      return
    if not isinstance(card, UnitCard):
      return
    u = CardToUnit(card, self.currentBF)
    u.id = self.lastId + 1
    self.lastId += 1
    u.owner = player
    u.fl = F
    self.Deploy(u, F, player)                 # type: ignore[arg-type]

  def AddKredits(self, player: PlayerId, amount: int, ctx: EvalContext) -> None:
    p = self.GetPlayer(player)
    if p is not None:
      p.actionPoint += amount
    self.effectInterp.HandleEvent(
      GameEvent(EventType.KREDIT_GAINED, actor=player, data={'数值': amount}))

  def CustomAction(self, op: str, args: Mapping[str, int | str],
                   ctx: EvalContext, target: EntityId | None) -> None:
    value = int(args.get('值', 0))
    owner = self.GetPlayer(ctx.owner)

    # ---- 不指向具体单位：作用于效果拥有者 ----
    if target is None:
      if owner is None:
        return
      if op == OP_AP:
        owner.actionPoint += value
      elif op == OP_AP_SLOT:
        owner.apSlot += value
      elif op == OP_SET_AP:
        owner.actionPoint = value
      elif op == OP_SET_AP_SLOT:
        owner.apSlot = value
      elif op == OP_ADD_TO_HAND:
        hc = CardToHand(value)
        hc.cost = self.HandCost(hc)
        owner.handCards.append(hc)
      elif op == OP_TO_TOP:
        owner.deck.append(value)
      elif op == OP_TO_BOTTOM:
        owner.deck.insert(0, value)
      elif op == OP_SHUFFLE:
        owner.deck.append(value)
        random.shuffle(owner.deck)
      elif op == OP_CHANGE_EVENT:
        self.ChangeEvent(value)               # type: ignore[arg-type]
      return

    # ---- 指向总部 ----
    if IsHqRef(target):
      player = self.GetPlayer(HqOwner(target))
      if player is None:
        return
      if op == OP_SET_HEALTH:
        player.hq = value
      elif op == OP_AP:
        player.actionPoint += value
      elif op == OP_AP_SLOT:
        player.apSlot += value
      return

    # ---- 指向单位 ----
    u = self.GetUnitById(ParseUnitId(target))
    if u is None:
      return
    if op == OP_ACTION_COST:
      u.actionCost += value
    elif op == OP_SET_ACTION_COST:
      u.actionCost = value
    elif op == OP_SET_ATTACK:
      u.atk = max(0, value)
    elif op == OP_SET_HEALTH:
      u.dfns = value






def debug(arg : Any) -> None:
  print(arg)

if __name__ == '__main__':
  g = Game()
  print(g.playerA.deck)
  print(g.playerB.deck)
  print(g.playerA.handCards)
  print(g.playerB.handCards)
  print(g.playerB.hq)

