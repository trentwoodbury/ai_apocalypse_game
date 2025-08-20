import tkinter as tk
import random
import settings as S
from cube import Cube

import tkinter.font as tkfont
import textwrap

try:
    from PIL import Image, ImageTk  # Pillow
except Exception:
    Image = ImageTk = None



BOARD_LABELS = S.BOARD_LABELS

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("4x4 Grid + 4 Cubes + Card Draw")
        w = (
                S.GRID_ORIGIN_X
                + S.GRID_COLS * S.CELL_SIZE
                + S.GRID_PADDING
                + S.SIDE_IMAGE_MAX_W  # reserve horizontal room for the image
                + S.GRID_PADDING
        )
        h = S.CARD_AREA_Y + S.CARD_AREA_H + S.GRID_PADDING
        self.canvas = tk.Canvas(root, width=w, height=h, bg="#f7f7fb")
        self.canvas.pack()

        # --- state (UI reads this) ---
        self.occupied = {}
        self.active_cube = None
        self.deck = list(range(1, 51));
        random.shuffle(self.deck)
        self.hand = []

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
        self.canvas.itemconfigure(
            self.take_action_button_window,
            state=("normal" if placed == 4 else "hidden")
        )

    def take_actions(self):
        # 1) Draw a card for each cube in the final column (rows 0–2)
        for _ in self.cubes_on_final_column():
            self.draw_card()

        # 2) Return cubes to start
        for cube in self.cubes:
            cube.return_to_start()

        # 3) Clear board occupancy so future placements aren’t blocked
        self.occupied.clear()

        # 4) Hide the button again
        self.canvas.itemconfigure(self.take_action_button_window, state="hidden")