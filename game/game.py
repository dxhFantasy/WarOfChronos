from .Battlefield import *
from .Player import *
from .Cards import *
from .ActionRecord import *
from typing import Any,Literal
from copy import deepcopy
from random import randint


def FindKeyw(u : Unit,k : Keyword):
  for t in u.tags:
    if t.keyword == k:
      return u.tags.index(t)
  return None

A = 0
B = 1
C = 2

HQ_A = -1
HQ_B = -2

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

class Game():
  def __init__(self) -> None:
    self.playerA : Player = Player(0,0,[],[],20,'A')
    self.playerB : Player = Player(0,0,[],[],20,'B')




    self.playerA.deck = cardIds[0:len(cardIds)//2-1]
    self.playerB.deck = cardIds[len(cardIds)//2:len(cardIds)//2-1]



    self.currentPlayer = 'A'
    self.totalTurn = 0

    self.battlefields : list[Battlefield] = [Battlefield(0,[Frontline(6),Frontline(4),Frontline(6)])]
    self.battlefields *= 3

    self.currentBF : Literal[0,1,2] = 1

    self.events : list[bool] = [True,True,True,False]

    random.shuffle(self.playerA.deck)
    random.shuffle(self.playerB.deck)

  def InitDraw(self):
    self.DrawCard('A',5)
    self.DrawCard('B',6)
    state = self.GetState()
    return state


  def GetPlayer(self,player : str):
    if player != 'N':
      return self.playerB if player == 'B' else self.playerA
    else:
      return None
    
  def GetUnitById(self,uid : int | None):
    for fl in self.battlefields[self.currentBF].frontlines:
      for u in fl.targets:
        if u.id == uid:
          return u
  
  def GetFlById(self,uid : int | None):
    for fl in self.battlefields[self.currentBF].frontlines:
      for u in fl.targets:
        if u.id == uid:
          return self.battlefields[self.currentBF].frontlines.index(fl)
  
  
  def ChangeEvent(self,eid : Literal[0,1,2,3]):
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
        for fl in self.battlefields[B].frontlines:
          for u in fl.targets:
            u.atk += 3
            u.dfns += 2


  def DrawCard(self,player : str,num : int):
    playerT = self.GetPlayer(player)
    if playerT:
      for _ in range(num):
        if len(playerT.deck) != 0 :
          temp : HandCard = CardToHand(playerT.deck.pop())
          if (self.currentBF == 0) and self.events[3]:
            temp.cost = temp.cost - 2 if temp.cost >= 2 else 0
          playerT.handCards.append(temp)
        else:
          playerT.hq -= 3

  def TimeWarp(self,t : Literal[0,1,2]):
    self.currentBF = t

  def Deploy(self,u : Unit,fl : int, player : Literal['A' , 'B']):
    
    if not self.events[E2]: #第二次世界大战：关闭
      if u.utl == 0:
        u.atk += 2
        u.dfns += 2
      else:
        u.atk -= 1
        u.dfns -= 1
    
    if not self.events[E3]: #美苏冷战：关闭
      if u.utl == 1:
        u.atk -= 1
        u.dfns -= 1
    
    if self.events[E4]: #三战：开启
      if u.utl == 1:
        u.actionCost -= 1
      if u.utl == 2:
        u.atk -= 3
        u.dfns -= 2
    
    u.owner = player
    self.battlefields[self.currentBF].frontlines[fl].targets.append(u)
    

    if(FindKeyw(u,Keyword.Guard) is not None):
      for un in self.battlefields[self.currentBF].frontlines[fl].targets:
        if(FindKeyw(un,Keyword.Guard) is not None):
          un.tags.append(Tag(Keyword.Guarded))
    
    if(FindKeyw(u,Keyword.Deploy) is not None):
      ...
    

  def Attack(self,u : Unit ,tid : int | None):

    if(tid in (HQ_A, HQ_B)): #攻击总部
      atk = ClacAtk(u.tags,u.atk)
      if tid == HQ_A:
        self.playerA.hq -= atk
      else:
        self.playerB.hq -= atk
    else:                             #攻击单位
      t = self.GetUnitById(tid)
      if(t is None):
        raise Exception('你不能攻击滚木')
      if(FindKeyw(t,Keyword.Guarded)):
        if(u.uType not in (UnitType.bomber, UnitType.artillery)):
          raise Exception('此单位被守护')
      
      atk = ClacAtk(u.tags,u.atk)
      dmg = ClacDamage(t.tags,atk)
      t.dfns -= dmg

      #受到反击伤害
      if t.uType != UnitType.bomber and u.uType not in (UnitType.bomber, UnitType.artillery):
        fAtk = t.atk
        dmg = ClacDamage(u.tags,fAtk)
        u.dfns -= dmg

  def Cmp(self,check : Any, cmpT : cmp, n : Any):
    if cmpT == cmp.Eq:
      return check == n
    elif cmpT == cmp.NEq:
      return check != n
    elif cmpT == cmp.Gr:
      return check > n
    elif cmpT == cmp.NGr:
      return check <= n
    elif cmpT == cmp.Le:
      return check < n
    elif cmpT == cmp.NLe:
      return check >= n

  def CheckCondition(self, cdtn : ChooseCondition | None, tid : int, player : Player):
    if cdtn is None:
      return True
    t = self.GetUnitById(tid)
    flag : list[bool] = []
    if t not in (HQ_A, HQ_B):
      assert t is not None
    if cdtn.actCost:
      if self.Cmp(t.actionCost, cdtn.cmpT, cdtn.value):
        flag.append(True)
      else:
        flag.append(False)
    if cdtn.atk:
      if self.Cmp(t.atk, cdtn.cmpT, cdtn.value):
        flag.append(True)
      else:
        flag.append(False)
    if cdtn.cost:
      if self.Cmp(t.cost, cdtn.cmpT, cdtn.value):
        flag.append(True)
      else:
        flag.append(False)
    if cdtn.dfns:
      if self.Cmp(t.dfns, cdtn.cmpT, cdtn.value):
        flag.append(True)
      else:
        flag.append(False)
    if cdtn.frontline:
      if self.Cmp(t.fl, cdtn.cmpT, cdtn.value):
        flag.append(True)
      else:
        flag.append(False)
    if cdtn.tag:
      tagIdx = FindKeyw(t,cdtn.tag.keyword)
      if tagIdx is not None and t.tags[tagIdx].value == cdtn.value:
        flag.append(True)
      else:
        flag.append(False)
    if cdtn.timeline:
      raise Exception('代码没写')
    if cdtn.tid:
      if self.Cmp(t.id, cdtn.cmpT, cdtn.value):
        flag.append(True)
      else:
        flag.append(False)
      # if self.Cmp(t.fl, cdtn.cmpT, cdtn.value):
      #   flag.append(True)
      # else:
      #   flag.append(False)

  def ApplyEffects(self,targets : list[int], effectType : EffectType, value : int | Tag | tuple[int,int], player : Player):
    for tid in targets:
      t = self.GetUnitById(tid)
      assert t is not None
      if effectType == EffectType.AddAC:
        assert type(value) == int
        t.actionCost += value
      elif  effectType == EffectType.AddAP:
        assert type(value) == int
        player.actionPoint += value
      elif  effectType == EffectType.ADDAPS:
        assert type(value) == int
        player.apSlot += value
      elif  effectType == EffectType.AddToHand:
        assert type(value) == int
        player.handCards.append(CardToHand(value))
      elif  effectType == EffectType.AddTag:
        assert type(value) == Tag
        t.tags.append(value)
      elif effectType == EffectType.Buff:
        assert type(value) == tuple[int, int]
        t.atk += value[0]
        t.dfns += value[1]
      elif effectType == EffectType.Deploy:
        assert type(value) == int
        raise Exception('代码没写')
      elif effectType == EffectType.Destroy:
        assert type(value) == int
        t.dfns = -1
      elif effectType == EffectType.DrawCard:
        assert type(value) == int
        self.DrawCard(player.name,value)
      elif effectType == EffectType.TakeDamage:
        assert type(value) == int
        dmg = ClacDamage(t.tags,value)
        t.dfns -= dmg
      elif effectType == EffectType.PutOnTop:
        assert type(value) == int
        player.deck.append(value)
      elif effectType == EffectType.ShuffleIntoDeck:
        assert type(value) == int
        player.deck.append(value)
        random.shuffle(player.deck)
      elif effectType == EffectType.PutOnBottom:
        assert type(value) == int
        player.deck.insert(0,value)

  def UseCommand(self,player : Player, command : CommandCard, tid : int | None):
    es = command.effects

    for e in es:
      targets : list[int] = []
      
      #判断目标指定合法性/分配指令目标
      if e.target.num == 0:
        targets.append(-10086) # 占位符 防止判断目标不合法
      
      if not e.target.Random:
        if e.target.num == 1:  #非随机目标要么1要么全部
          if tid is None:
            raise Exception('目标未指定')
          if self.CheckCondition(e.target.condition, tid, player):
            targets.append(tid)
        # elif e.target.num != ALL:
        #   for _ in range(e.target.num):
        #     ...
        else:
          for fl in self.battlefields[self.currentBF].frontlines:
            for u in fl.targets:
              if self.CheckCondition(e.target.condition, u.id, player):
                targets.append(u.id)
      else: #随机选择目标
        temp : list[int] = []
        for fl in self.battlefields[self.currentBF].frontlines:
          for u in fl.targets:
            if self.CheckCondition(e.target.condition, u.id, player):
              temp.append(u.id) #候选目标
        for _ in range(e.target.num):#随机选择目标
          rt = randint(0,len(temp) - 1)
          if rt not in targets:
            targets.append(rt) 
      
      
      if len(targets) == 0:
        raise Exception('目标不合法')
      #====判断结束====

      flag = False
      if e.triggerCondition:#判断触发条件
        for triCdtn in e.triggerCondition:
          if triCdtn.cdtnType == TriggerConditionType.EventsHappend:
            assert type(triCdtn.target) == int
            if self.events[triCdtn.target]:
              flag = True
          if triCdtn.cdtnType == TriggerConditionType.HasUnitsOnField:
            assert type(triCdtn.target) == ChooseCondition
            for fl in self.battlefields[self.currentBF].frontlines:
              find = False
              for u in fl.targets:
                if self.CheckCondition(triCdtn.target, u.id, player):
                  find = True
                  break
              if find:
                break
      #====判断结束====

      if flag:#处理指令效果
        self.ApplyEffects(targets,e.effect,e.value, player)



  def ReceiveRecord(self):
    ...
    #self.ProcessRecord(...)
  
  def ProcessRecord(self,entry : LogEntry):
    eType = entry.actionType
    result : Result | None = None
    player = entry.actorPlayer
    try:
      if(entry.actorPlayer == 'N'):
          raise Exception('什么叫滚木在执行操作')
      if(eType == ActionType.DrawCard):
        if(entry.target is None):
          raise Exception('未给出抽牌数量')
        self.DrawCard(entry.actorPlayer,entry.target)
      elif(eType == ActionType.UseCommand):
        
        ...# 重点
      elif(eType == ActionType.Deploy):
        if(entry.actorId is None):
          raise Exception('不能部署滚木')
        
        if(allCards[entry.actorId].timeline != self.currentBF): # type: ignore
          raise Exception('禁止出现超时空战士')
        unitCard = allCards[entry.actorId]
        if(type(unitCard) != UnitCard):
          raise Exception('不能部署指令，啥子比。')
        assert type(unitCard) == UnitCard

        if ((player == 'A' and entry.target == 2) or (player == 'B' and entry.target == 0)):
          raise Exception('单位不能放对面家里')
        elif entry.target == 1 and FindKeyw(CardToUnit(unitCard),Keyword.Prepared) or \
              ((player == 'A' and entry.target == 0) or (player == 'B' and entry.target == 1)):
          
          newUnit = CardToUnit(unitCard)
          newUnit.id = self.battlefields[self.currentBF].unitsNum
          assert entry.actorPlayer in ('A', 'B')
          newUnit.owner = entry.actorPlayer
          newUnit.fl = entry.target
          self.Deploy(newUnit,entry.target, entry.actorPlayer)
        
        else: 
          raise Exception('不是你放单位给我放好的呀')
          
      elif(eType == ActionType.TurnEnd):
        
        self.TurnEnd(entry.actorPlayer)
      
      elif eType == ActionType.Attack:
        u = self.GetUnitById(entry.actorId)
        if(u is None):
          raise Exception('你不能指挥滚木攻击')
        ufl = self.GetFlById(entry.actorId)
        tfl = self.GetFlById(entry.target)
        uType = u.uType
        if(uType in (UnitType.bomber, UnitType.artillery, UnitType.fighter)):
          self.Attack(u,entry.target)
        else:
          if(ufl in (DA, DB) and tfl in (DA, DB)):
            raise Exception('攻击距离不足')
          else:
            self.Attack(u,entry.target)
        

      
      result = Result('ok',gameState=self.GetState())

    except Exception as err:
      s = str(err)
      debug(s)
      result = Result('err',msg=s)
      
    
    return result

  def Check(self):
    for bf in self.battlefields:
      for fl in bf.frontlines:
        f = False
        for u in fl.targets:
          if(u.dfns <= 0):
            fl.targets.pop(fl.targets.index(u))
            bf.unitsNum -= 1
            continue
          if FindKeyw(u,Keyword.Guard):
            f = True
        if not f:
          for u in fl.targets:
            if FindKeyw(u,Keyword.Guarded):
              u.tags.pop(u.tags.index(Tag(Keyword.Guarded)))
    


  def GetState(self):
    self.Check()
    state = GameState(
      deepcopy(self.playerA),\
      deepcopy(self.playerB),\
      deepcopy(self.battlefields),\
      self.currentBF,\
      deepcopy(self.events)
    )
    return state


  def TurnStart(self, lastTurnPlayer : str) -> None:
    if(lastTurnPlayer == 'A'):
      self.DrawCard('B',1)
      self.playerB.apSlot += 1
      self.playerB.actionPoint = self.playerB.apSlot
      if self.events[0] :
        self.playerB.actionPoint -= 1
      if self.events[2] :
        self.playerB.actionPoint += 2
    else:
      self.DrawCard('A',1)
      self.playerA.apSlot += 1
      self.playerA.actionPoint = self.playerA.apSlot
      if self.events[0] :
        self.playerA.actionPoint -= 1
      if self.events[2] :
        self.playerA.actionPoint += 2
    ...
    

    


  def TurnEnd(self,player : str) -> None:
    ...
    self.TurnStart(player)
    ...





def debug(arg : Any):
  print(arg)

if __name__ == '__main__':
  a = Player(0,0,[],[],114514,'N')
  b = a
  b.apSlot += 1
  debug(a.apSlot)

