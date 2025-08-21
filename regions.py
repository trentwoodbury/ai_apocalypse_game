from dataclasses import dataclass
import settings as S

@dataclass
class Region:
    def __init__(self, name):
        self.name = name
        self.chaos = 0          # integer, 0..S.CHAOS_MAX, multiples of S.CHAOS_STEP
        self.player_presence = False
        self.reputation = 0
        self.power = 0

        # UI hooks (optional; used by Game)
        self.canvas = None
        self.tracker_ids = None  # legacy; no longer required

    def attach_ui(self, canvas, _rows_list):
        """Kept for compatibility; panels are handled by Game now."""
        self.canvas = canvas

    def set_presence(self, value: bool = True):
        self.player_presence = bool(value)

    @property
    def presence(self):  # compatibility alias
        return self.player_presence

    def set_chaos(self, value: int):
        # Clamp and snap to steps of 10
        v = max(0, min(int(value), S.CHAOS_MAX))
        v = (v // S.CHAOS_STEP) * S.CHAOS_STEP
        self.chaos = v

    def adjust_rep(self, delta: int):
        self.reputation += int(delta)

    def adjust_power(self, delta: int):
        self.power += int(delta)


class RegionManager:
    def __init__(self, names=None):
        from settings import REGION_NAMES
        names = names or REGION_NAMES
        self.regions = {n: Region(n) for n in names}

    def __getitem__(self, name): return self.regions[name]
    def __contains__(self, name): return name in self.regions
    def region_at(self, name): return self.regions[name]

    def total_reputation(self):
        return sum(r.reputation for r in self.regions.values())

    def total_power(self):
        return sum(r.power for r in self.regions.values())

    def add_presence(self, name: str):
        if name in self.regions:
            self.regions[name].set_presence(True)

    def has_presence(self, name: str) -> bool:
        return name in self.regions and self.regions[name].player_presence

    def any_presence(self) -> bool:
        return any(r.player_presence for r in self.regions.values())

    def with_presence(self):
        return [r for r in self.regions.values() if r.player_presence]
