from Battlefield import *
from Player import *
from Cards import *
from ActionRecord import *
from typing import Any


class Game():
  def __init__(self) -> None:
    playerA = Player(0,0,[]) # type: ignore
    playerB = Player(0,0,[]) # type: ignore
    


    self.DrawCard('A',4)
    self.DrawCard('B',4)
    
  def DrawCard(self,player : str,num : int):
    if(player == 'A'):
      ...
    else:
      ...


  def TurnStart(self) -> None:
    ...

  def TurnEnd(self) -> None:
    ...




def debug(arg : Any):
  print(arg)

if __name__ == '__main__':
  debug('fxxk')

