# game.py (refactored)
import tkinter as tk
import random
import settings as S
from funds import Funds
from cube import Cube
from regions import RegionManager

from mixins.ui_grid import UIGridMixin
from mixins.ui_cards import UICardsMixin
from mixins.ui_costs import UICostsMixin
from mixins.ui_trackers import UITrackersMixin
from mixins.ui_regions import UIRegionsMixin
from mixins.logic_core import LogicCoreMixin

# Re-export PIL handles for tests (may be None in headless)
try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None


BOARD_LABELS = S.BOARD_LABELS

class Game(UIGridMixin, UICardsMixin, UICostsMixin, UITrackersMixin, UIRegionsMixin, LogicCoreMixin):
    BOARD_LABELS = BOARD_LABELS

    def __init__(self, root):
        self.root = root
        self.root.title("4x4 Grid + 4 Cubes + Card Draw")
        self.regions = RegionManager(S.REGION_NAMES)

        self.occupied = {}
        self.active_cube = None
        self.deck = list(range(1, 51)); random.shuffle(self.deck)
        self.hand = []

        # --- tracker state (leftmost index by default) ---
        self.compute_idx = 0
        self.model_idx = 0
        self.chaos_idx = 0  # keep for legacy tests (no UI row now)
        self.tracker_items = {  # keep keys for legacy helpers
            "compute": [],
            "model": [],
            "chaos": []
        }

        self.cell_text_ids = {}
        self.side_image_id = None
        self.side_image_dims = (0, 0)

        w = S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE + S.GRID_PADDING + 300
        h = S.CARD_AREA_Y + S.CARD_AREA_H + S.GRID_PADDING
        self.canvas = tk.Canvas(root, width=w, height=h, bg="#f7f7fb")
        self.canvas.pack()

        self.draw_grid()

        start_box_width = S.CUBE_SIZE + 2 * S.START_AREA_PAD
        start_box_height = 4 * S.CUBE_SIZE + 3 * S.CUBE_GAP + 2 * S.START_AREA_PAD
        start_x = S.GRID_ORIGIN_X - S.GRID_PADDING - start_box_width
        start_y = S.GRID_ORIGIN_Y
        self._start_area_geom = (start_x, start_y, start_box_width, start_box_height)

        self.draw_start_area()
        self.draw_card_area()

        self.cubes = []
        colors = ["#ff7f50", "#87cefa", "#98fb98", "#dda0dd"]
        for i in range(4):
            x = start_x + S.START_AREA_PAD
            y = start_y + S.START_AREA_PAD + i * (S.CUBE_SIZE + S.CUBE_GAP)
            self.cubes.append(Cube(self.canvas, i, x, y, colors[i % len(colors)]))

        self._draw_side_image()
        if self.side_image_id is not None:
            grid_w = S.GRID_COLS * S.CELL_SIZE
            base_w = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING + self.side_image_dims[0] + S.GRID_PADDING
            if int(float(self.canvas.cget("width"))) < base_w:
                self.canvas.config(width=base_w)

        # Right-hand panel + trackers + region panels
        self._draw_trackers()

        # Funds
        funds_x = self.trackers_left_x
        funds_y = self.trackers_bottom_y + 20
        self.funds = Funds(S.FUNDS_START, S.FUNDS_SERIES, self.canvas, funds_x, funds_y)

        # Selection state / region UI
        self.selecting_regions = False
        self.selection_tasks = []
        self.region_hitboxes = {}
        self.region_hex_ids = {}
        self._build_region_hitboxes()
        self._render_region_markers()

        # Actions button
        btn_pad_x = 12
        btn_center_y = S.CARD_AREA_Y + S.CARD_AREA_H / 2
        self.take_action_button = tk.Button(self.root, text="Take Actions", command=self.take_actions)
        self.take_action_button_window = self.canvas.create_window(
            S.CARD_AREA_X - btn_pad_x, btn_center_y, window=self.take_action_button, anchor="e"
        )
        self.canvas.itemconfigure(self.take_action_button_window, state="hidden")

        # Input bindings
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Button-1>", self.on_mouse_down, add="+")
        self.canvas.bind("<Button-1>", self._maybe_region_click, add="+")

    @property
    def selection_queue(self):
        return len(self.selection_tasks)
