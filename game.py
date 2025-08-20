import tkinter as tk
import random
import settings as S
from cube import Cube

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("4x4 Grid + 4 Cubes + Card Draw")
        w = S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE + S.GRID_PADDING
        h = S.CARD_AREA_Y + S.CARD_AREA_H + S.GRID_PADDING
        self.canvas = tk.Canvas(root, width=w, height=h, bg="#f7f7fb")
        self.canvas.pack()

        # --- state first ---
        self.occupied = {}          # (row, col) -> cube_idx
        self.active_cube = None
        self.deck = list(range(1, 51))
        random.shuffle(self.deck)

        # Persistent hand that survives resets
        self.hand = []              # list[int], drawn cards

        # --- UI ---
        self.draw_grid()
        self.draw_start_area()
        self.draw_card_area()

        self.cubes = []
        colors = ["#ff7f50", "#87cefa", "#98fb98", "#dda0dd"]
        for i in range(4):
            x = S.START_AREA_X
            y = S.START_AREA_Y + i * (S.CUBE_SIZE + S.CUBE_GAP)
            self.cubes.append(Cube(self.canvas, i, x, y, colors[i % len(colors)]))

        # Reset button (hidden initially)
        self.reset_button = tk.Button(self.root, text="Reset Cubes", command=self.reset_game)
        self.reset_button_window = self.canvas.create_window(
            S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE - 80,
            S.CARD_AREA_Y + S.CARD_AREA_H / 2,
            window=self.reset_button
        )
        self.canvas.itemconfigure(self.reset_button_window, state="hidden")

        # Bindings
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    # ---- UI drawing ----
    def draw_grid(self):
        self.canvas.create_text(
            S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE / 2,
            20,
            text="Drop cubes on the 4×4 grid",
            font=("Helvetica", 16, "bold")
        )
        for r in range(S.GRID_ROWS):
            for c in range(S.GRID_COLS):
                x0 = S.GRID_ORIGIN_X + c * S.CELL_SIZE
                y0 = S.GRID_ORIGIN_Y + r * S.CELL_SIZE
                x1 = x0 + S.CELL_SIZE
                y1 = y0 + S.CELL_SIZE
                fill = "#ffffff" if c % 2 == r % 2 else "#f0f0f5"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#ccccd6")
        for c in range(S.GRID_COLS):
            cx = S.GRID_ORIGIN_X + c * S.CELL_SIZE + S.CELL_SIZE / 2
            self.canvas.create_text(cx, S.GRID_ORIGIN_Y - 12, text=f"Col {c+1}", font=("Helvetica", 10))

    def draw_start_area(self):
        self.canvas.create_text(
            S.START_AREA_X + 60, S.START_AREA_Y - 12,
            text="Start Area",
            font=("Helvetica", 12, "bold")
        )
        self.canvas.create_rectangle(
            S.START_AREA_X - 10, S.START_AREA_Y - 10,
            S.START_AREA_X + S.CUBE_SIZE + 10,
            S.START_AREA_Y + 4 * (S.CUBE_SIZE + S.CUBE_GAP) - S.CUBE_GAP + 10,
            outline="#bbbbc6", dash=(4, 2)
        )

    def draw_card_area(self):
        # Title + deck
        self.canvas.create_text(
            S.GRID_ORIGIN_X + 100, S.CARD_AREA_Y - 8,
            text=f"Hand (max {S.HAND_LIMIT}). Place on Column 1, Rows 1–3 to draw:",
            anchor="w",
            font=("Helvetica", 12, "bold")
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

        # Precompute hand slot positions
        self.hand_slot_ids = []  # [(rect_id, text_id), ...]
        start_x = S.CARD_AREA_X + 10
        y0 = S.CARD_AREA_Y + 32
        for i in range(S.HAND_LIMIT):
            x0 = start_x + i * (S.HAND_SLOT_W + S.HAND_SLOT_GAP)
            rect_id = self.canvas.create_rectangle(
                x0, y0, x0 + S.HAND_SLOT_W, y0 + S.HAND_SLOT_H,
                fill="#ffffff", outline="#333"  # higher contrast
            )
            text_id = self.canvas.create_text(
                x0 + S.HAND_SLOT_W / 2, y0 + S.HAND_SLOT_H / 2,
                text="—", font=("Helvetica", 18, "bold"), fill="#111"
            )
            # guarantee text is above the rectangle
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
        self.on_cube_placed(cube)

    def on_cube_placed(self, cube):
        row, col = cube.current_cell
        # Draw only if column 0 AND row in {0,1,2}
        if col == 0 and row in (0, 1, 2):
            self.draw_card()

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
            self.reset_button_window,
            state=("normal" if placed == 4 else "hidden")
        )

    def reset_game(self):
        # Return cubes to start & clear board occupancy — DO NOT clear hand
        for cube in self.cubes:
            cube.return_to_start()
        self.occupied.clear()

        # Reset deck (reshuffle) but keep visible hand as requested
        self.deck = list(range(1, 51))
        random.shuffle(self.deck)
        self.canvas.itemconfigure(self.deck_text, text=f"Deck: {len(self.deck)}")
        self.render_hand()  # keep showing cards already drawn

        # Hide reset button
        self.canvas.itemconfigure(self.reset_button_window, state="hidden")
