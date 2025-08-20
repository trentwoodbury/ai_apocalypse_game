# regions.py
from dataclasses import dataclass, field
import numpy as np

@dataclass
class Region:
    name: str
    presence: bool = False
    reputation: int = 0
    power: int = 0
    chaos: int = 0  # must be in {0,10,...,90}

    def set_presence(self, val: bool = True):
        self.presence = bool(val)

    def set_chaos(self, val: int):
        # Snap to {0,10,20,...,90}
        val = max(0, min(90, int(val)))
        self.chaos = int(round(val / 10.0) * 10)

class RegionManager:
    def __init__(self, names):
        self.regions = {n: Region(n) for n in names}

    def total_reputation(self):
        return sum(r.reputation for r in self.regions.values())

    def total_power(self):
        return sum(r.power for r in self.regions.values())

    def add_presence(self, name: str):
        if name in self.regions:
            self.regions[name].set_presence(True)

    def has_presence(self, name: str) -> bool:
        return name in self.regions and self.regions[name].presence

    def region_at(self, name: str) -> Region:
        return self.regions[name]
