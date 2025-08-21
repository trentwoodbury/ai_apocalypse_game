import tkinter as tk
import random
import settings as S
from funds import Funds
from cube import Cube

import tkinter.font as tkfont
import textwrap

from regions import RegionManager
import math

try:
    from PIL import Image, ImageTk  # Pillow
except Exception:
    Image = ImageTk = None



BOARD_LABELS = S.BOARD_LABELS

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("4x4 Grid + 4 Cubes + Card Draw")

        # --- Regions over the globe ---
        self.regions = RegionManager(S.REGION_NAMES)

        # --- state (UI reads this) ---
        self.occupied = {}
        self.active_cube = None
        self.deck = list(range(1, 51));
        random.shuffle(self.deck)
        self.hand = []

        # --- tracker state (leftmost index by default) ---
        self.compute_idx = 0
        self.model_idx = 0
        self.chaos_idx = 0
        self.tracker_items = {"compute": [], "model": [], "chaos": []}  # canvas ids for circles/text

        # bookkeeping for tests/ids
        self.cell_text_ids = {}
        self.side_image_id = None
        self.side_image_dims = (0, 0)

        # --- canvas ---
        w = S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE + S.GRID_PADDING + 300  # provisional width
        h = S.CARD_AREA_Y + S.CARD_AREA_H + S.GRID_PADDING
        self.canvas = tk.Canvas(root, width=w, height=h, bg="#f7f7fb")
        self.canvas.pack()

        # --- draw grid first ---
        self.draw_grid()

        # --- compute start area geometry BEFORE drawing/using it ---
        start_box_width = S.CUBE_SIZE + 2 * S.START_AREA_PAD
        start_box_height = 4 * S.CUBE_SIZE + 3 * S.CUBE_GAP + 2 * S.START_AREA_PAD
        start_x = S.GRID_ORIGIN_X - S.GRID_PADDING - start_box_width
        start_y = S.GRID_ORIGIN_Y
        self._start_area_geom = (start_x, start_y, start_box_width, start_box_height)

        # --- draw start area and label ---
        self.draw_start_area()

        # --- card/hand UI ---
        self.draw_card_area()

        # --- create cubes inside the start area ---
        self.cubes = []
        colors = ["#ff7f50", "#87cefa", "#98fb98", "#dda0dd"]
        for i in range(4):
            x = start_x + S.START_AREA_PAD
            y = start_y + S.START_AREA_PAD + i * (S.CUBE_SIZE + S.CUBE_GAP)
            self.cubes.append(Cube(self.canvas, i, x, y, colors[i % len(colors)]))

        # --- side image (after grid) ---
        self._draw_side_image()
        if self.side_image_id is not None:
            grid_w = S.GRID_COLS * S.CELL_SIZE
            base_w = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING + self.side_image_dims[0] + S.GRID_PADDING
            if int(float(self.canvas.cget("width"))) < base_w:
                self.canvas.config(width=base_w)

        # right-hand requirements/costs panel
        self._draw_costs_panel()

        self._draw_trackers()
        funds_x = self.trackers_left_x
        funds_y = self.trackers_bottom_y + 20
        self.funds = Funds(S.FUNDS_START, S.FUNDS_SERIES, self.canvas, funds_x, funds_y)

        # Selection state if [1,1] was chosen this turn
        self.selecting_regions = False
        self.selection_tasks = []
        self.region_hitboxes = {}  # name -> (x0,y0,x1,y1)
        self.region_hex_ids = {}  # name -> canvas polygon id

        # Build hitboxes now that the image is drawn & sized
        self._build_region_hitboxes()  # computes pixel-space rects from fractional config
        self._render_region_markers()  # draw initial markers (none yet)

        # --- Take Actions button (left of hand area) ---
        btn_pad_x = 12
        btn_center_y = S.CARD_AREA_Y + S.CARD_AREA_H / 2
        self.take_action_button = tk.Button(self.root, text="Take Actions", command=self.take_actions)
        self.take_action_button_window = self.canvas.create_window(
            S.CARD_AREA_X - btn_pad_x, btn_center_y,
            window=self.take_action_button, anchor="e"
        )
        self.canvas.itemconfigure(self.take_action_button_window, state="hidden")

        # --- bindings ---
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Extra binding to capture clicks on globe when selecting regions
        self.canvas.bind("<Button-1>", self.on_mouse_down, add="+")
        self.canvas.bind("<Button-1>", self._maybe_region_click, add="+")

    @property
    def selection_queue(self):
        """Compatability shim: number of outstanding selections (old name)."""
        return len(self.selection_tasks)

    # ---- UI drawing ----
    def draw_grid(self):
        self.canvas.create_text(
            S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE / 2,
            20,
            text="Quarterly Strategy",
            font=("Helvetica", 16, "bold"),
            fill="black"
        )

        for r in range(S.GRID_ROWS):
            for c in range(S.GRID_COLS):
                x0 = S.GRID_ORIGIN_X + c * S.CELL_SIZE
                y0 = S.GRID_ORIGIN_Y + r * S.CELL_SIZE
                x1 = x0 + S.CELL_SIZE
                y1 = y0 + S.CELL_SIZE
                fill = "#ffffff" if c % 2 == r % 2 else "#f5f6fa"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#ccccd6")
                idx = r * S.GRID_COLS + c
                if idx < len(BOARD_LABELS):
                    self.draw_cell_label(r, c, BOARD_LABELS[idx])

    def draw_start_area(self):
        if not hasattr(self, "_start_area_geom"):
            # fallback (shouldn’t happen now, but keeps tests resilient)
            start_box_width = S.CUBE_SIZE + 2 * START_AREA_PAD
            start_box_height = 4 * S.CUBE_SIZE + 3 * S.CUBE_GAP + 2 * START_AREA_PAD
            start_x = S.GRID_ORIGIN_X - S.GRID_PADDING - start_box_width
            start_y = S.GRID_ORIGIN_Y
            self._start_area_geom = (start_x, start_y, start_box_width, start_box_height)

        start_x, start_y, start_w, start_h = self._start_area_geom

        self.start_area_label_id = self.canvas.create_text(
            start_x + start_w / 2, start_y - 12,
            text="Available Action Tokens",
            font=("Helvetica", 12, "bold"), fill="black"
        )
        self.start_area_rect_id = self.canvas.create_rectangle(
            start_x, start_y, start_x + start_w, start_y + start_h,
            outline="#bbbbc6", dash=(4, 2), fill=""
        )

    def draw_card_area(self):
        # Title + deck
        self.canvas.create_text(
            S.GRID_ORIGIN_X + 100, S.CARD_AREA_Y - 8,
            text=f"Current Hand Limit: {S.HAND_LIMIT}).",
            anchor="w",
            font=("Helvetica", 12, "bold"),
            fill="black"
        )
        self.canvas.create_rectangle(
            S.CARD_AREA_X, S.CARD_AREA_Y,
            S.CARD_AREA_X + S.CARD_AREA_W, S.CARD_AREA_Y + S.CARD_AREA_H,
            outline="#bbbbc6"
        )
        self.deck_text = self.canvas.create_text(
            S.CARD_AREA_X + S.CARD_AREA_W - 10, S.CARD_AREA_Y + 16,
            text=f"Deck: {len(self.deck)}",
            anchor="e",
            font=("Helvetica", 12)
        )
        self.hand_full_text = self.canvas.create_text(
            S.CARD_AREA_X + 10, S.CARD_AREA_Y + 16,
            text="",
            anchor="w",
            font=("Helvetica", 12, "italic"),
            fill="#a00"
        )

        # Precompute hand slot positions (2 rows x 4 columns)
        self.hand_slot_ids = []  # [(rect_id, text_id), ...]
        start_x = S.CARD_AREA_X + 16
        start_y = S.CARD_AREA_Y + 40

        for i in range(S.HAND_LIMIT):
            r = i // S.HAND_COLS
            c = i % S.HAND_COLS
            x0 = start_x + c * (S.HAND_SLOT_W + S.HAND_SLOT_GAP_X)
            y0 = start_y + r * (S.HAND_SLOT_H + S.HAND_SLOT_GAP_Y)

            rect_id = self.canvas.create_rectangle(
                x0, y0, x0 + S.HAND_SLOT_W, y0 + S.HAND_SLOT_H,
                fill="#ffffff", outline="#333"
            )
            text_id = self.canvas.create_text(
                x0 + S.HAND_SLOT_W / 2, y0 + S.HAND_SLOT_H / 2,
                text="—", font=("Helvetica", 18, "bold"), fill="#111"
            )
            self.canvas.tag_raise(text_id, rect_id)
            self.hand_slot_ids.append((rect_id, text_id))

        self.render_hand()

    # ---- Mouse handling ----
    def on_mouse_down(self, event):
        for cube in reversed(self.cubes):  # topmost first
            if cube.contains(event.x, event.y):
                self.active_cube = cube
                cube.begin_drag(event.x, event.y)
                if cube.current_cell is not None:
                    self.occupied.pop(cube.current_cell, None)
                    cube.current_cell = None
                break

    def on_mouse_move(self, event):
        if self.active_cube:
            self.active_cube.drag_to(event.x, event.y)

    def on_mouse_up(self, event):
        if not self.active_cube:
            return
        cube = self.active_cube
        cube.end_drag()

        cell = self.cell_from_cube_center(cube)
        if cell and self.can_place(cell):
            row, col = cell
            self.place_cube_and_handle_events(cube, row, col)
        else:
            cube.return_to_start()

        self.update_reset_visibility()
        self.active_cube = None

    # ---- Placement & game logic ----
    def place_cube_and_handle_events(self, cube, row, col):
        cube.center_on_cell(row, col)
        self.occupied[(row, col)] = cube.idx

    # ---- Helpers ----
    def cell_from_cube_center(self, cube):
        x0, y0, x1, y1 = self.canvas.bbox(cube.rect)
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        if not (S.GRID_ORIGIN_X <= cx < S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE and
                S.GRID_ORIGIN_Y <= cy < S.GRID_ORIGIN_Y + S.GRID_ROWS * S.CELL_SIZE):
            return None
        col = int((cx - S.GRID_ORIGIN_X) // S.CELL_SIZE)
        row = int((cy - S.GRID_ORIGIN_Y) // S.CELL_SIZE)
        if 0 <= row < S.GRID_ROWS and 0 <= col < S.GRID_COLS:
            return (row, col)
        return None

    def can_place(self, cell):
        return cell not in self.occupied

    def cubes_on_final_column(self):
        """Return list of cubes currently on the final column (row, col)."""
        results = []
        for cube in self.cubes:
            if cube.current_cell:
                row, col = cube.current_cell
                if col == S.GRID_COLS - 1 and row in (0, 1, 2):  # adjust if you only want rows 0-2
                    results.append((row, col))
        return results

    def draw_cell_label(self, row, col, text):
        CELL_TEXT_PAD = 10  # inner padding in each cell
        # compute center of the cell
        x0 = S.GRID_ORIGIN_X + col * S.CELL_SIZE
        y0 = S.GRID_ORIGIN_Y + row * S.CELL_SIZE
        x1 = x0 + S.CELL_SIZE
        y1 = y0 + S.CELL_SIZE

        max_w = S.CELL_SIZE - 2 * CELL_TEXT_PAD
        max_h = S.CELL_SIZE - 2 * CELL_TEXT_PAD

        # try decreasing font sizes until it fits
        size = 18
        wrapped = text
        font = None
        for fs in range(18, 9, -1):  # 18 down to 10
            font = tkfont.Font(family="Helvetica", size=fs, weight="bold")
            # wrap per line width in pixels -> approximate via measuring characters
            # choose wrap width by binary search-ish: start with chars/line guess
            # convert pixels->chars guess using average char width
            avg_char_px = max(font.measure("M"), 1)
            chars_per_line = max(int(max_w / (avg_char_px * 0.7)), 8)

            lines = []
            for paragraph in text.split("\n"):
                lines.extend(textwrap.wrap(paragraph, width=chars_per_line) or [""])

            # measure total height
            line_h = font.metrics("linespace")
            total_h = line_h * len(lines)
            # check max line width
            widest = max((font.measure(line) for line in lines), default=0)

            if widest <= max_w and total_h <= max_h:
                wrapped = "\n".join(lines)
                size = fs
                break

        # create the text item centered in the cell
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        t_id = self.canvas.create_text(
            cx, cy, text=wrapped, font=("Helvetica", size, "bold"),
            fill="#111", justify="center"
        )
        # stash for testing
        self.cell_text_ids[(row, col)] = t_id

    def _draw_side_image(self):
        if Image is None or ImageTk is None:
            return
        try:
            img = Image.open(S.SIDE_IMAGE_PATH)
        except Exception:
            return

        grid_h = S.GRID_ROWS * S.CELL_SIZE
        grid_w = S.GRID_COLS * S.CELL_SIZE

        orig_w, orig_h = img.size
        if orig_h == 0:
            return
        scale = grid_h / float(orig_h)
        new_w = max(1, int(round(orig_w * scale)))
        new_h = grid_h
        img = img.resize((new_w, new_h), Image.LANCZOS)

        x = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        y = S.GRID_ORIGIN_Y  # top-align with grid

        try:
            # CRITICAL: bind PhotoImage to the same Tk master as the canvas
            self._side_img_tk = ImageTk.PhotoImage(img, master=self.canvas)
            self.side_image_id = self.canvas.create_image(x, y, image=self._side_img_tk, anchor="nw")
            self.side_image_dims = (new_w, new_h)
        except tk.TclError:
            # In headless/CI edge cases, just skip the image
            self._side_img_tk = None
            self.side_image_id = None
            self.side_image_dims = (0, 0)
            return

    # ---- Cards / Hand ----
    def draw_card(self):
        if len(self.hand) >= S.HAND_LIMIT:
            self.canvas.itemconfigure(self.hand_full_text, text="Hand is full")
            return
        self.canvas.itemconfigure(self.hand_full_text, text="")

        if not self.deck:
            return

        card = self.deck.pop()
        self.hand.append(card)

        slot_index = len(self.hand) - 1
        if 0 <= slot_index < len(self.hand_slot_ids):
            _, text_id = self.hand_slot_ids[slot_index]
            self.canvas.itemconfigure(text_id, text=str(card), fill="#111")
            self.canvas.tag_raise(text_id)

        self.canvas.itemconfigure(self.deck_text, text=f"Deck: {len(self.deck)}")
        try:
            self.canvas.update_idletasks()
        except Exception:
            pass

    def render_hand(self):
        for i, (rect_id, text_id) in enumerate(self.hand_slot_ids):
            if i < len(self.hand):
                self.canvas.itemconfigure(text_id, text=str(self.hand[i]), fill="#111")
                self.canvas.tag_raise(text_id, rect_id)
            else:
                self.canvas.itemconfigure(text_id, text="—", fill="#aaa")

    def update_reset_visibility(self):
        placed = sum(1 for c in self.cubes if c.current_cell is not None)
        if placed == 4:
            self.canvas.itemconfigure(self.take_action_button_window, state="normal")

            # Funds gate
            pending_cost = self._pending_total_cost()
            funds_ok = (pending_cost <= self.funds.value)

            # Presence gate: if any presence-required squares are used, must already have presence somewhere
            need_presence = any(
                c.current_cell in S.PRESENCE_REQUIRED_COORDS
                for c in self.cubes if c.current_cell
            )
            presence_ok = (not need_presence) or self.regions.any_presence()

            if funds_ok and presence_ok:
                self.take_action_button.config(state="normal")
            else:
                self.take_action_button.config(state="disabled")
                if not presence_ok:
                    self._toast("Requires presence in a region")
        else:
            self.canvas.itemconfigure(self.take_action_button_window, state="hidden")
            self.take_action_button.config(state="normal")

    def take_actions(self):
        # 0) Funds gate
        pending = self._pending_total_cost()
        if pending > self.funds.value:
            self._toast("Insufficient Funds")
            return

        # 0b) Presence gate (if needed)
        need_presence = any(
            c.current_cell in S.PRESENCE_REQUIRED_COORDS
            for c in self.cubes if c.current_cell
        )
        if need_presence and not self.regions.any_presence():
            self._toast("Requires presence in a region")
            return

        # 1) Build selection tasks
        self.selection_tasks = []  # list of dicts: {"type": ..., "requires_presence": bool}

        # [1,1] — Scale Presence: add presence (does NOT require existing presence)
        for _ in [c for c in self.cubes if c.current_cell == (1, 1)]:
            self.selection_tasks.append({"type": "add_presence", "requires_presence": False})

        # Presence-required targets:
        for _ in [c for c in self.cubes if c.current_cell == (1, 0)]:
            self.selection_tasks.append({"type": "rep+1", "requires_presence": True})
        for _ in [c for c in self.cubes if c.current_cell == (1, 2)]:
            self.selection_tasks.append({"type": "power+1", "requires_presence": True})
        for _ in [c for c in self.cubes if c.current_cell == (2, 1)]:
            self.selection_tasks.append({"type": "power+1_rep-2_chaos+10", "requires_presence": True})
        for _ in [c for c in self.cubes if c.current_cell == (2, 2)]:
            self.selection_tasks.append({"type": "rep-1_chaos+10", "requires_presence": True})

        # 2) If we need selections, enter selection mode and prompt
        if self.selection_tasks:
            self.selecting_regions = True
            self._show_center_popup(self._current_selection_prompt())
            return

        # 3) If no selections needed, resolve immediately
        self._finish_take_actions_after_selection()

    def _finish_take_actions_after_selection(self):
        # 1) Card draws for cubes in final column (rows 0–2)
        for _ in self.cubes_on_final_column():
            self.draw_card()

        # 1b) Global buff: [0,1] => +1 rep & +1 power in ALL regions where you have presence
        if any(c.current_cell == (0, 1) for c in self.cubes if c.current_cell):
            for r in self.regions.with_presence():
                r.adjust_rep(+1)
                r.adjust_power(+1)

        # 2) Tracker bumps (unchanged)
        bumps_compute = bumps_model = bumps_chaos = 0
        charges = {"lobby": 0, "scale_presence": 0, "compute_or_model": 0}

        for cube in self.cubes:
            if not cube.current_cell:
                continue
            r, c = cube.current_cell
            if (r, c) == (0, 0):
                bumps_compute += 1
                charges["compute_or_model"] += 1
            elif (r, c) == (0, 1):
                bumps_model += 1
                charges["compute_or_model"] += 1
            elif (r, c) in ((2, 1), (2, 2)):
                bumps_chaos += 1

            if (r, c) == (0, 2):
                charges["lobby"] += 1
            if (r, c) == (1, 1):
                charges["scale_presence"] += 1

        if bumps_compute:
            self.inc_compute(bumps_compute)
        if bumps_model:
            self.inc_model(bumps_model)
        if bumps_chaos:
            self.inc_chaos(bumps_chaos)

        # 3) Deduct funds
        for key, n in charges.items():
            if n: self.funds.charge(key, n)

        # 4) Income at end: SUM(rep) * SUM(power)
        income = self.regions.total_reputation() * self.regions.total_power()
        if income: self.funds.add(income)

        # 5) Reset board
        for cube in self.cubes: cube.return_to_start()
        self.occupied.clear()
        self.canvas.itemconfigure(self.take_action_button_window, state="hidden")

    def _draw_trackers(self):
        """Draw Compute, Model, and the 2x3 Region Panels below the costs panel."""
        grid_w = S.GRID_COLS * S.CELL_SIZE
        grid_h = S.GRID_ROWS * S.CELL_SIZE
        img_x = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        left_x = img_x

        # 1) Draw right-hand costs panel first (so we can position everything below it)
        self._draw_costs_panel()
        # Figure out the bottom of the costs panel using its tag bbox
        cb = self.canvas.bbox(self.costs_panel_tag)
        costs_bottom_y = cb[3] if cb else (S.GRID_ORIGIN_Y + 200)

        # 2) Now place trackers just below that
        top_y = costs_bottom_y + 20
        row_h = S.TRACKER_ROW_H
        self.trackers_left_x = left_x

        # Compute tracker row
        self._draw_tracker_row(
            y=top_y + 0 * row_h,
            title="Compute",
            steps=S.COMPUTE_STEPS,
            key="compute",
            active_idx=self.compute_idx
        )
        # Model tracker row
        self._draw_tracker_row(
            y=top_y + 1 * row_h,
            title="Model Version",
            steps=S.MODEL_STEPS,  # ["0","1","2","3","4","5","6","7"]
            key="model",
            active_idx=self.model_idx
        )

        # Region summary panels below the tracker rows
        self._draw_region_panels(start_y=top_y + 2 * row_h)

        # Where to place Funds below the panels
        self.trackers_bottom_y = getattr(self, "panels_bottom_y", top_y + 1)

        # Widen canvas if needed based on rightmost content
        needed_w = int(self.trackers_rightmost_x + S.GRID_PADDING)
        current_w = int(float(self.canvas.cget("width")))
        if needed_w > current_w:
            self.canvas.config(width=needed_w)

    def _draw_tracker_row(self, y, title, steps, key, active_idx=0):
        """Render one horizontal tracker row; store item ids in self.tracker_items[key].
           Returns the list of (rect, txt, circle, meta) tuples for external use.
        """
        left_x = self.trackers_left_x if hasattr(self, "trackers_left_x") else S.GRID_ORIGIN_X
        pad_label = 110
        w_box = 120 if key not in ("chaos",) else 60  # smaller boxes okay for chaos numbers
        gap = 8

        # title
        self.canvas.create_text(
            left_x, y,
            text=title + ":",
            anchor="w",
            font=("Helvetica", 12, "bold"),
            fill="black"
        )

        x = left_x + pad_label
        rows_list = []
        for i, label in enumerate(steps):
            rect = self.canvas.create_rectangle(x, y - 14, x + w_box, y + 14, outline="#222", fill="#eee")
            txt = self.canvas.create_text((x + x + w_box) / 2, y, text=label,
                                          font=("Helvetica", 11, "bold"), fill="#111")
            cx = (x + x + w_box) / 2
            circle = self.canvas.create_oval(cx - 10, y - 10, cx + 10, y + 10,
                                             outline="", width=3)
            rows_list.append((rect, txt, circle, (x, y, w_box)))
            self.trackers_rightmost_x = max(getattr(self, "trackers_rightmost_x", 0), x + w_box)
            x += w_box + gap

        # Save in dict and highlight active index
        if not hasattr(self, "tracker_items"):
            self.tracker_items = {}
        self.tracker_items[key] = rows_list
        self._set_tracker_active_index(key, active_idx)

        return rows_list

    def _set_tracker_active_index(self, key, idx):
        """Show the marker (circle) on the idx-th slot, hide others."""
        rows_list = self.tracker_items.get(key, [])
        for i, (_rect, _txt, circle, (x, y, w)) in enumerate(rows_list):
            if i == idx:
                # center circle and show outline
                cx = (x + x + w) / 2
                self.canvas.coords(circle, cx - 12, y - 12, cx + 12, y + 12)
                self.canvas.itemconfigure(circle, outline="black")
            else:
                self.canvas.itemconfigure(circle, outline="")

    def _update_region_chaos(self, name):
        """Sync a region’s chaos value to its chaos row marker."""
        idx = 0
        if name in self.regions.regions:
            idx = max(0, min(9, self.regions[name].chaos // 10))
        key = f"chaos:{name}"
        self._set_tracker_active_index(key, idx)

    def _render_tracker_markers(self):
        """Position/visibility of the index markers (black circles)."""

        def paint(key, idx):
            items = self.tracker_items[key]
            for i, (_rect, _txt, circle, (x, y, w)) in enumerate(items):
                if i == idx:
                    # center the circle over this box and make it visible
                    cx = (x + x + w) / 2
                    cy = y
                    self.canvas.coords(circle, cx - 12, cy - 12, cx + 12, cy + 12)
                    self.canvas.itemconfigure(circle, outline="black")
                else:
                    self.canvas.itemconfigure(circle, outline="")  # hide

        paint("compute", self.compute_idx)
        paint("model", self.model_idx)
        paint("chaos", self.chaos_idx)
        try:
            self.canvas.update_idletasks()
        except Exception:
            pass

    # --- tracker bumpers ---
    def inc_compute(self, n=1):
        self.compute_idx = min(self.compute_idx + n, len(S.COMPUTE_STEPS) - 1)
        # model can never exceed compute
        if self.model_idx > self.compute_idx:
            self.model_idx = self.compute_idx
        self._render_tracker_markers()
        self._set_tracker_active_index("compute", self.compute_idx)

    def inc_model(self, n=1):
        # cap by compute
        target = min(self.model_idx + n, self.compute_idx, len(S.MODEL_STEPS) - 1)
        if target != self.model_idx:
            self.model_idx = target
            self._render_tracker_markers()
        self._set_tracker_active_index("model", self.model_idx)
        self._render_costs_panel()

    def inc_chaos(self, n=1):
        self.chaos_idx = min(self.chaos_idx + n, len(S.CHAOS_STEPS) - 1)
        self._render_tracker_markers()

    def _charges_for_current_turn(self):
        """Count how many times each cost key would be charged for current placements."""
        charges = {"lobby": 0, "scale_presence": 0, "compute_or_model": 0}
        for cube in self.cubes:
            if not cube.current_cell:
                continue
            r, c = cube.current_cell
            if (r, c) == (0, 0) or (r, c) == (0, 1):
                charges["compute_or_model"] += 1
            if (r, c) == (0, 2):
                charges["lobby"] += 1
            if (r, c) == (1, 1):
                charges["scale_presence"] += 1
        return charges

    def _pending_total_cost(self):
        """Sum of all costs for current placements if Take Actions were pressed now."""
        charges = self._charges_for_current_turn()
        return (
                self.funds.peek_cost("compute_or_model", charges["compute_or_model"])
                + self.funds.peek_cost("lobby", charges["lobby"])
                + self.funds.peek_cost("scale_presence", charges["scale_presence"])
        )

    def _toast(self, msg: str, millis: int = 1500):
        """Transient popup-like notice above the hand area."""
        # Kill old toast if present
        if hasattr(self, "toast_id") and self.toast_id:
            self.canvas.delete(self.toast_id)
            self.toast_id = None
        x = S.CARD_AREA_X + S.CARD_AREA_W / 2
        y = S.CARD_AREA_Y - 8
        self.toast_id = self.canvas.create_text(
            x, y, text=msg, fill="#b00020", font=("Helvetica", 12, "bold"), anchor="s"
        )
        self.canvas.after(millis, lambda: (self.canvas.delete(self.toast_id), setattr(self, "toast_id", None)))

    def _build_region_hitboxes(self):
        """Compute pixel hitboxes aligned to the displayed image."""
        if not self.side_image_id or not self.side_image_dims:
            return
        img_x, img_y = self.canvas.coords(self.side_image_id)
        img_w, img_h = self.side_image_dims

        self.region_hitboxes.clear()
        for name in S.REGION_NAMES:
            fx0, fy0, fx1, fy1 = S.REGION_BBOXES_FRAC[name]
            x0 = img_x + fx0 * img_w
            y0 = img_y + fy0 * img_h
            x1 = img_x + fx1 * img_w
            y1 = img_y + fy1 * img_h
            self.region_hitboxes[name] = (x0, y0, x1, y1)

    def _hex_points(self, cx, cy, r):
        pts = []
        for i in range(6):
            ang = math.radians(60 * i - 30)  # flat-top hex
            pts.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])
        return pts

    def _render_region_markers(self):
        """Render hex markers on regions with presence."""
        # Clear existing
        for poly_id in list(self.region_hex_ids.values()):
            try:
                self.canvas.delete(poly_id)
            except Exception:
                pass
        self.region_hex_ids.clear()

        for name, (x0, y0, x1, y1) in self.region_hitboxes.items():
            if not self.regions.has_presence(name):
                continue
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            pts = self._hex_points(cx, cy, S.REGION_HEX_RADIUS)
            pid = self.canvas.create_polygon(
                *pts, fill="", outline=S.REGION_HEX_OUTLINE, width=S.REGION_HEX_WIDTH
            )
            self.region_hex_ids[name] = pid

    def _maybe_region_click(self, event):
        """Handle selection clicks for presence adding and region-targeted effects."""
        if not getattr(self, "selecting_regions", False):
            return
        if not self.selection_tasks:
            # Safety: nothing to select
            self._hide_center_popup()
            self.selecting_regions = False
            self._finish_take_actions_after_selection()
            return

        # Hit-test regions
        hit_name = None
        for name, (x0, y0, x1, y1) in self.region_hitboxes.items():
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                hit_name = name
                break

        # If miss, just reassert prompt
        if not hit_name:
            self._update_center_popup(self._current_selection_prompt())
            return

        task = self.selection_tasks[0]

        # Enforce presence when required
        if task.get("requires_presence") and not self.regions.has_presence(hit_name):
            self._update_center_popup("Select a region WHERE YOU HAVE PRESENCE")
            return

        # Apply task
        if task["type"] == "add_presence":
            if not self.regions.has_presence(hit_name):
                self.regions.add_presence(hit_name)
                # if you draw hex markers on the map, keep this:
                self._render_region_markers()
            # update the summary panel either way
            self._update_region_panel(hit_name)
            self._render_costs_panel()  # refresh bold for next presence cost


        elif task["type"] == "rep+1":
            R = self.regions[hit_name]
            R.adjust_rep(+1)
            self._update_region_panel(hit_name)

        elif task["type"] == "power+1":
            R = self.regions[hit_name]
            R.adjust_power(+1)
            self._update_region_panel(hit_name)

        elif task["type"] == "power+1_rep-2_chaos+10":
            R = self.regions[hit_name]
            R.adjust_power(+1)
            R.adjust_rep(-2)
            R.set_chaos(R.chaos + S.CHAOS_STEP)
            self._update_region_panel(hit_name)

        elif task["type"] == "rep-1_chaos+10":
            R = self.regions[hit_name]
            R.adjust_rep(-1)
            R.set_chaos(R.chaos + S.CHAOS_STEP)
            self._update_region_panel(hit_name)

        # Consume this task
        self.selection_tasks.pop(0)

        if self.selection_tasks:
            # More to pick
            self._update_center_popup(self._current_selection_prompt())
        else:
            # Done: hide popup and finish the action phase
            self._hide_center_popup()
            self.selecting_regions = False
            self._finish_take_actions_after_selection()

    def _show_center_popup(self, msg: str):
        """Show a centered, light-grey popup with black text."""
        # Clean any existing popup
        self._hide_center_popup()

        cw = int(float(self.canvas.cget("width")))
        ch = int(float(self.canvas.cget("height")))
        cx, cy = cw // 2, ch // 2

        pad_x, pad_y = 16, 12
        # First create text to measure its bbox
        txt_id = self.canvas.create_text(
            cx, cy,
            text=msg,
            font=("Helvetica", 14, "bold"),
            fill="black",
            anchor="c",
            justify="center",
            width=min(420, cw - 60),  # wrap if narrow canvas
        )
        tx0, ty0, tx1, ty1 = self.canvas.bbox(txt_id)
        rx0 = tx0 - pad_x
        ry0 = ty0 - pad_y
        rx1 = tx1 + pad_x
        ry1 = ty1 + pad_y

        rect_id = self.canvas.create_rectangle(
            rx0, ry0, rx1, ry1,
            fill="#e9e9ee", outline="#555", width=2
        )
        # Raise text above the rectangle
        self.canvas.tag_raise(txt_id, rect_id)

        # Keep refs so we can update/hide
        self._popup_rect_id = rect_id
        self._popup_text_id = txt_id

    def _update_center_popup(self, msg: str):
        """Update the popup text (if showing)."""
        if getattr(self, "_popup_text_id", None):
            self.canvas.itemconfigure(self._popup_text_id, text=msg)
            # re-center box to new text size
            tx0, ty0, tx1, ty1 = self.canvas.bbox(self._popup_text_id)
            pad_x, pad_y = 16, 12
            rx0 = tx0 - pad_x
            ry0 = ty0 - pad_y
            rx1 = tx1 + pad_x
            ry1 = ty1 + pad_y
            if getattr(self, "_popup_rect_id", None):
                self.canvas.coords(self._popup_rect_id, rx0, ry0, rx1, ry1)

    def _hide_center_popup(self):
        """Remove the popup if present."""
        if getattr(self, "_popup_text_id", None):
            try:
                self.canvas.delete(self._popup_text_id)
            except Exception:
                pass
            self._popup_text_id = None
        if getattr(self, "_popup_rect_id", None):
            try:
                self.canvas.delete(self._popup_rect_id)
            except Exception:
                pass
            self._popup_rect_id = None

    def _current_selection_prompt(self):
        if not getattr(self, "selection_tasks", None):
            return ""
        t = self.selection_tasks[0]
        if t["type"] == "add_presence":
            return f"Select a region to ADD presence ({len(self.selection_tasks)} remaining)"
        if t["requires_presence"]:
            return f"Select a region WHERE YOU HAVE PRESENCE ({len(self.selection_tasks)} remaining)"
        return f"Select a region ({len(self.selection_tasks)} remaining)"

    def _draw_region_panels(self, start_y=None):
        """Draw a 2x3 grid of summary boxes for each region."""
        grid_w = S.GRID_COLS * S.CELL_SIZE
        grid_h = S.GRID_ROWS * S.CELL_SIZE
        base_x = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        y0 = start_y if start_y is not None else (S.GRID_ORIGIN_Y + grid_h + 10)

        # Title
        self.canvas.create_text(
            base_x, y0, text=S.REGION_PANELS_TITLE, anchor="w",
            font=("Helvetica", 13, "bold"), fill="black"
        )
        y0 += 24  # space under the title

        self.region_panel_items = {}
        col_w = S.REGION_PANEL_W
        row_h = S.REGION_PANEL_H

        for idx, name in enumerate(S.REGION_NAMES):
            r = idx // S.REGION_PANEL_COLS
            c = idx % S.REGION_PANEL_COLS
            x = base_x + c * (col_w + S.REGION_PANEL_GAP_X)
            y = y0 + r * (row_h + S.REGION_PANEL_GAP_Y)

            rect = self.canvas.create_rectangle(
                x, y, x + col_w, y + row_h,
                outline="#bbb", fill="#f2f2f6"
            )
            text_id = self.canvas.create_text(
                x + 10, y + 10, anchor="nw",
                font=("Helvetica", 11), fill="black",
                text=""
            )
            self.region_panel_items[name] = {"rect": rect, "text": text_id}

        # Bottom edge for placing Funds
        self.panels_bottom_y = y0 + (S.REGION_PANEL_ROWS) * (row_h + S.REGION_PANEL_GAP_Y) - S.REGION_PANEL_GAP_Y

        # Render initial content
        for name in S.REGION_NAMES:
            self._render_region_panel(name)

        # Track rightmost for potential canvas widening
        rightmost = base_x + S.REGION_PANEL_COLS * (col_w + S.REGION_PANEL_GAP_X) - S.REGION_PANEL_GAP_X
        self.trackers_rightmost_x = max(getattr(self, "trackers_rightmost_x", 0), rightmost)

    def _draw_costs_panel(self):
        """Create the right-hand 'Scaling Costs and Requirements' panel."""
        # Anchor to the right of the map image
        grid_w = S.GRID_COLS * S.CELL_SIZE
        x_img = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        img_w = getattr(self, "side_image_dims", (0, 0))[0]

        x = x_img + img_w + S.GRID_PADDING
        y = S.GRID_ORIGIN_Y
        w = S.COSTS_PANEL_W

        # Ensure canvas is wide enough
        needed_w = x + w + S.GRID_PADDING
        current_w = int(float(self.canvas.cget("width")))
        if needed_w > current_w:
            self.canvas.config(width=needed_w)

        # Tag all elements of this panel so we can get a reliable bbox later
        self.costs_panel_tag = "costs_panel"

        # Title (BOX TITLE)
        self.costs_title_id = self.canvas.create_text(
            x, y, anchor="nw", fill="black",
            font=("Helvetica", 13, "bold"),
            text="Scaling Costs and Requirements",
            tags=(self.costs_panel_tag,)
        )
        y += 22

        # Panel background (height will be adjusted after rendering)
        # Set a provisional height; _render_costs_panel will resize it.
        self.costs_rect_id = self.canvas.create_rectangle(
            x, y, x + w, y + 100, outline="#bbb", fill="#f7f7fb",
            tags=(self.costs_panel_tag,)
        )

        # Lines will be created by renderer; keep a list for tests
        self.costs_line_ids = []
        self._render_costs_panel()  # initial draw

    def _render_costs_panel(self):
        """(Re)render the right-hand panel, bolding the 'next' items.
           Also records (text_id, bold, text) in self.costs_line_ids for tests,
           and resizes the background rect to fit content.
        """
        if not hasattr(self, "costs_rect_id"):
            return  # not yet drawn

        # wipe previous line items
        for tid, *_ in getattr(self, "costs_line_ids", []):
            try:
                self.canvas.delete(tid)
            except Exception:
                pass
        self.costs_line_ids = []  # will store (tid, bold, text)

        # geometry
        x1, y1, x2, _ = self.canvas.coords(self.costs_rect_id)
        x = x1 + S.COSTS_PANEL_PAD
        y = y1 + S.COSTS_PANEL_PAD
        line_gap = 4

        def add_line(text, bold=False, pad_top=0):
            nonlocal y
            y += pad_top
            tid = self.canvas.create_text(
                x, y, anchor="nw", fill="black",
                font=("Helvetica", 11, "bold" if bold else "normal"),
                text=text,
                tags=(self.costs_panel_tag,)
            )
            # record for tests
            self.costs_line_ids.append((tid, bold, text))
            y += 18 + line_gap

        # --- figure out which ones should be bold ---
        next_model_idx = self.model_idx + 1 if self.model_idx < len(S.MODEL_STEPS) - 1 else None
        presence_count = len(self.regions.with_presence())
        next_presence_idx = presence_count if presence_count < len(S.SCALING_PRESENCE_COSTS) else None

        # --- Section: Model Version Scaling Requirements ---
        add_line("Model Version Scaling Requirements", bold=True, pad_top=0)

        for tgt in range(len(S.MODEL_STEPS)):
            cost = S.MODEL_UPGRADE_COSTS[tgt]
            compute_req = S.COMPUTE_STEPS[tgt] if tgt < len(S.COMPUTE_STEPS) else ""
            label = f"V{tgt}: Pay ${cost}, {compute_req}"
            bold = (next_model_idx == tgt)
            add_line(label, bold=bold)

        # spacer
        add_line("", pad_top=6)

        # --- Section: Scaling Operation Costs ---
        add_line("Scaling Operation Costs", bold=True)
        for actions in (2, 3, 4):
            add_line(f"{actions} Actions: ${S.SCALING_OPERATION_COSTS[actions]}")

        add_line("", pad_top=6)

        # --- Section: Scaling Presence Costs ---
        add_line("Scaling Presence Costs", bold=True)
        for idx, cost in enumerate(S.SCALING_PRESENCE_COSTS, start=1):
            if idx == 1:
                label = f"{idx}st Region: ${cost}"
            elif idx == 2:
                label = f"{idx}nd Region: ${cost}"
            elif idx == 3:
                label = f"{idx}rd Region: ${cost}"
            else:
                label = f"{idx}th Region: ${cost}"
            bold = (next_presence_idx is not None and (idx == next_presence_idx + 1))
            add_line(label, bold=bold)

        # --- resize the panel background to fit all lines exactly ---
        # bbox of the whole panel tag = title + rect + lines
        bx1, by1, bx2, by2 = self.canvas.bbox(self.costs_panel_tag)
        # keep left/right the same as initial rect, but set height to content bottom + padding
        # ensure at least original top and width
        new_bottom = max(by2 + S.COSTS_PANEL_PAD, y1 + 40)
        self.canvas.coords(self.costs_rect_id, x1, y1, x2, new_bottom)

    def _render_region_panel(self, name: str):
        R = self.regions[name]
        lines = [
            f"Region: {R.name}",
            f"Presence: {'Yes' if R.player_presence else 'No'}",
            f"Power: {R.power}",
            f"Reputation: {R.reputation}",
            f"Chaos: {R.chaos} out of {S.CHAOS_MAX}",
        ]
        text = "\n".join(lines)
        tid = self.region_panel_items[name]["text"]
        self.canvas.itemconfigure(tid, text=text)

    def _update_region_panel(self, name: str):
        if hasattr(self, "region_panel_items") and name in self.region_panel_items:
            self._render_region_panel(name)






