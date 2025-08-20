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

        self._draw_trackers()

        # Funds label right below trackers, aligned with their left edge
        funds_x = getattr(self, "trackers_left_x", S.GRID_ORIGIN_X)
        funds_y = getattr(self, "trackers_bottom_y", S.GRID_ORIGIN_Y) + 20
        self.funds = Funds(
            start_amount=S.FUNDS_START,
            series_map=S.FUNDS_SERIES,
            canvas=self.canvas,
            x=funds_x,
            y=funds_y,
        )

        # --- Regions over the globe ---
        self.regions = RegionManager(S.REGION_NAMES)

        # Selection state if [1,1] was chosen this turn
        self.selecting_regions = False
        self.selection_queue = 0  # how many presence placements to make
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
            # Show the button window
            self.canvas.itemconfigure(self.take_action_button_window, state="normal")
            # Enable/disable based on funds sufficiency
            pending = self._pending_total_cost()
            if pending > self.funds.value:
                self.take_action_button.config(state="disabled")
            else:
                self.take_action_button.config(state="normal")
        else:
            self.canvas.itemconfigure(self.take_action_button_window, state="hidden")
            self.take_action_button.config(state="normal")  # reset for next time

    def take_actions(self):
        # Funds gate first
        pending = self._pending_total_cost()
        if pending > self.funds.value:
            self._toast("Insufficient Funds")
            return

        # Count how many presence placements we need (tokens at [1,1])
        need_presence = sum(
            1 for c in self.cubes if c.current_cell == (1, 1)
        )
        if need_presence > 0:
            self.selection_queue = need_presence
            self.selecting_regions = True
            self._show_center_popup(f"Select a region ({self.selection_queue} remaining)")
            return

        # Otherwise no presence picks needed; finish immediately
        self._finish_take_actions_after_selection()

    def _finish_take_actions_after_selection(self):
        # 1) Card draws for cubes in final column (rows 0–2)
        for _ in self.cubes_on_final_column():
            self.draw_card()

        # 2) Tracker bumps based on cube placements
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
                charges["scale_presence"] += 1  # cost progression only; presence was handled by clicks

        if bumps_compute: self.inc_compute(bumps_compute)
        if bumps_model:   self.inc_model(bumps_model)
        if bumps_chaos:   self.inc_chaos(bumps_chaos)

        # 3) Deduct funds for all placed actions (clamped in Funds)
        for key, n in charges.items():
            if n:
                self.funds.charge(key, n)

        # 4) Income: SUM(rep) * SUM(power)
        income = self.regions.total_reputation() * self.regions.total_power()
        if income:
            self.funds.add(income)

        # 5) Reset tokens & occupancy
        for cube in self.cubes:
            cube.return_to_start()
        self.occupied.clear()

        # 6) Hide the button again
        self.canvas.itemconfigure(self.take_action_button_window, state="hidden")

    def _draw_trackers(self):
        """Draw three horizontal trackers below the globe, aligned under the grid/globe band."""
        # Geometry
        grid_w = S.GRID_COLS * S.CELL_SIZE
        grid_h = S.GRID_ROWS * S.CELL_SIZE
        img_x = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        left_x = img_x  # left aligned with globe
        top_y = S.GRID_ORIGIN_Y + grid_h + 10  # just below the globe
        row_h = 36
        pad_x = 10
        self.trackers_rightmost_x = S.GRID_ORIGIN_X  # init; we'll update

        # One row drawer
        def draw_row(y, title, steps, marker_list_key):
            # title
            self.canvas.create_text(left_x, y, text=title + ":", anchor="w",
                                    font=("Helvetica", 12, "bold"), fill="black")
            # boxes
            x = left_x + 110
            self.tracker_items[marker_list_key] = []
            for i, label in enumerate(steps):
                w = 120 if marker_list_key != "chaos" else 60  # chaos numbers are narrow
                rect = self.canvas.create_rectangle(x, y - 14, x + w, y + 14, outline="#222", fill="#eee")
                txt = self.canvas.create_text((x + x + w) / 2, y, text=label,
                                              font=("Helvetica", 11, "bold"), fill="#111")
                # marker position (circle) centered in rect
                cx = (x + x + w) / 2
                cy = y
                circle = self.canvas.create_oval(cx - 10, cy - 10, cx + 10, cy + 10, outline="", width=3)
                self.tracker_items[marker_list_key].append((rect, txt, circle, (x, y, w)))
                self.trackers_rightmost_x = max(self.trackers_rightmost_x, x + w)
                x += w + 8

        draw_row(top_y + 0 * row_h, "Compute", S.COMPUTE_STEPS, "compute")
        draw_row(top_y + 1 * row_h, "Model Version", S.MODEL_STEPS, "model")
        draw_row(top_y + 2 * row_h, "Chaos Created", S.CHAOS_STEPS, "chaos")

        self.trackers_left_x = left_x
        self.trackers_bottom_y = top_y + 3 * row_h

        # paint initial markers
        self._render_tracker_markers()
        # Scale screen to include full trackers
        needed_w = int(self.trackers_rightmost_x + S.GRID_PADDING)
        current_w = int(float(self.canvas.cget("width")))
        if needed_w > current_w:
            self.canvas.config(width=needed_w)

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

    def inc_model(self, n=1):
        # cap by compute
        target = min(self.model_idx + n, self.compute_idx, len(S.MODEL_STEPS) - 1)
        if target != self.model_idx:
            self.model_idx = target
            self._render_tracker_markers()

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
        """If we're in region selection mode, consume a click to set presence."""
        if not getattr(self, "selecting_regions", False):
            return

        for name, (x0, y0, x1, y1) in self.region_hitboxes.items():
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                # Only count a selection if the region doesn't already have presence
                if not self.regions.has_presence(name):
                    self.regions.add_presence(name)
                    self._render_region_markers()
                    self.selection_queue -= 1
                else:
                    # Already present: keep popup up and ask for another pick
                    self._update_center_popup(
                        f"{name} already has presence. Select a different region ({self.selection_queue} remaining)"
                    )
                    return

                if self.selection_queue <= 0:
                    # Done selecting — hide popup and finish the action phase
                    self._hide_center_popup()
                    self.selecting_regions = False
                    self._finish_take_actions_after_selection()
                else:
                    # More picks remaining; keep popup updated
                    self._update_center_popup(
                        f"Select a region ({self.selection_queue} remaining)"
                    )
                return  # stop after handling this click

        # Clicked outside any region while selecting: keep the popup visible as a reminder
        self._update_center_popup(
            f"Select a region ({self.selection_queue} remaining)"
        )

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



