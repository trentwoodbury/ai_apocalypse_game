# regions.py
from dataclasses import dataclass
import settings as S

@dataclass
class Region:
    def __init__(self, name):
        self.name = name
        self.chaos = 0
        self.player_presence = False
        self.reputation = 0
        self.power = 0

        # UI hooks (optional)
        self.canvas = None
        self.tracker_ids = None

    def attach_ui(self, canvas, tracker_ids):
        """Attach UI elements so chaos/reputation updates redraw on canvas."""
        self.canvas = canvas
        self.tracker_ids = tracker_ids

    def set_presence(self, value: bool = True):
        """Set binary presence flag for the player in this region."""
        self.player_presence = bool(value)

    def set_chaos(self, value):
        # Clamp chaos to [0, 90]
        self.chaos = max(0, min(value, 90))

        # Update UI only if attached
        if self.canvas and self.tracker_ids:
            idx = self.chaos // 10
            # self.tracker_ids is a list of row tuples (rect, txt, circle, geo)
            for i, (_r, _t, circle, _geo) in enumerate(self.tracker_ids):
                self.canvas.itemconfig(
                    circle, fill="black" if i == idx else "white"
                )

    def _set_tracker_active_index(self, tracker_ids, idx):
        # Clear all ovals
        for i, oid in enumerate(tracker_ids):
            self.canvas.itemconfig(
                oid, fill="black" if i == idx else "white"
            )

    def adjust_rep(self, delta: int):
        self.reputation += int(delta)

    def adjust_power(self, delta: int):
        self.power += int(delta)

    @property
    def presence(self):
        return self.player_presence


class RegionManager:
    def __init__(self, names):
        self.regions = {n: Region(n) for n in names}

    # Optional ergonomic sugar:
    def __getitem__(self, name): return self.regions[name]
    def __contains__(self, name): return name in self.regions

    def region_at(self, name: str) -> Region:
        return self.regions[name]

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
        return any(r.presence for r in self.regions.values())

    def with_presence(self):
        return [r for r in self.regions.values() if r.presence]
