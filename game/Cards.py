from classes.Tags import *
from classes.Target import *
import random

allCards : dict[int, Unit] = {
  1 : Unit(6,8,[Tag(Keyword.Guard)],6,2,'ZTZ99A主战坦克','N'),
  2 : Unit(4,2,[Tag(Keyword.Blitz),Tag(Keyword.Passive,'对战坦克时，具有双倍攻击力')],\
            3,1,'2S38\"偏瘫\"','N')
}

cardIds = list(range(1,len(allCards)+1))

cardIds *= 40




def Shuffle():
  random.shuffle(cardIds)
