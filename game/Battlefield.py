from .classes.Frontline import*
from dataclasses import dataclass,field

@dataclass
class Battlefield():
  unitsNum : int = 0
  frontlines : list[Frontline] = field(default_factory=list[Frontline]) # type: ignore








