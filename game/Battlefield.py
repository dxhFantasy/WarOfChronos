from classes.Frontline import*
from dataclasses import dataclass,field

@dataclass
class Battlefield():
  frontlines : list[Frontline] = field(default_factory=list[Frontline]) # type: ignore







