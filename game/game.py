from Battlefield import *
from Player import *
from Cards import *
from ActionRecord import *
from typing import Any,Literal



@dataclass
class GameState():
  playerA : Player
  playerB : Player
  hqA : int
  hqB : int
  deckA : list[int]
  deckB : list[int]
  battlefields : list[Battlefield]

class Result:
  def __init__(self, state : Literal['ok','err'],msg : str | None = None, gameState : GameState | None = None) -> None:
    self.state : Literal['ok','err'] = state
    if(self.state == 'ok'):
      self.gameState = gameState
    else:
      self.msg = msg

class Game():
  def __init__(self) -> None:
    self.playerA : Player = Player(0,0,[])
    self.playerB : Player = Player(0,0,[])
    
    self.deckA : list[int] = cardIds[0:len(cardIds)/2-1]
    self.deckB : list[int] = cardIds[len(cardIds)/2:len(cardIds)/2-1]

    self.hqA = 20
    self.hqB = 20

    self.currentPlayer = 'A'
    self.totalTurn = 0

    self.battlefields : list[Battlefield] = []


    random.shuffle(self.deckA)
    random.shuffle(self.deckB)

    self.DrawCard('A',5)
    self.DrawCard('B',6)



  def GetPlayer(self,player : str):
    if player != 'N':
      return self.playerB if player == 'B' else self.playerA
    else:
      return None
    
  def DrawCard(self,player : str,num : int):
    playerT = self.GetPlayer(player)
    if playerT:
      for _ in range(num):
        if len(self.deckA) != 0 :
          temp : int = self.deckA.pop()
          playerT.handCards.append(temp)
        else:
          if(player == 'A'):
            self.hqA -= 3
          else:
            self.hpB -= 3

  def ReceiveRecord(self):
    ...
    #self.ProcessRecord(...)
  
  def ProcessRecord(self,entry : LogEntry):
    ...
  
  def SendRecord(self,record : LogEntry):
    state = GameState(self.playerA,self.playerB,self.hqA,self.hqB,self.deckA,self.deckB,self.battlefields)
    if(state):
      ...
    ...


  def TurnStart(self, lastTurnPlayer : str) -> None:
    if(lastTurnPlayer == 'A'):
      self.DrawCard('B',1)
      self.playerB.apSlot += 1
      self.playerB.actionPoint = self.playerB.apSlot
    else:
      self.DrawCard('A',1)
      self.playerA.apSlot += 1
      self.playerA.actionPoint = self.playerA.apSlot
    

    


  def TurnEnd(self,player : str) -> None:
    ...
    self.TurnStart(player)
    ...




def debug(arg : Any):
  print(arg)

if __name__ == '__main__':
  a = Player(0,0,[])
  b = a
  b.apSlot += 1
  debug(a.apSlot)

