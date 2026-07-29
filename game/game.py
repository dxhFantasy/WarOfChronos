from Battlefield import *
from Player import *
from Cards import *
from ActionRecord import *
from typing import Any


class Game():
  def __init__(self) -> None:
    self.playerA : Player = Player(0,0,[])
    self.playerB : Player = Player(0,0,[])
    
    self.deckA : list[int] = cardIds[0:len(cardIds)/2-1]
    self.deckB : list[int] = cardIds[len(cardIds)/2:len(cardIds)/2-1]

    random.shuffle(self.deckA)
    random.shuffle(self.deckB)

    self.DrawCard('A',4)
    self.DrawCard('B',4)
    
  def DrawCard(self,player : str,num : int):
    if(player == 'A'):
      for _ in range(num):
        self.playerA.handCards.append(self.deckA.pop())
    else:
      for _ in range(num):
        self.playerB.handCards.append(self.deckB.pop())


  def TurnStart(self) -> None:
    ...

  def TurnEnd(self) -> None:
    ...




def debug(arg : Any):
  print(arg)

if __name__ == '__main__':
  debug('fxxk')

