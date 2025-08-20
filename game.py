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

        # --- state first (UI reads it) ---
        self.occupied = {}          # (row, col) -> cube_idx
        self.active_cube = None
        self.deck = list(range(1, 51))
        random.shuffle(self.deck)
        self.last_card = None

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
        self.canvas.create_text(
            S.GRID_ORIGIN_X + 100, S.CARD_AREA_Y - 8,
            text="Drawn Card (drops in Column 2):",
            anchor="w",
            font=("Helvetica", 12, "bold")
        )
        self.canvas.create_rectangle(
            S.CARD_AREA_X, S.CARD_AREA_Y,
            S.CARD_AREA_X + S.CARD_AREA_W, S.CARD_AREA_Y + S.CARD_AREA_H,
            outline="#bbbbc6"
        )
        self.card_slot = self.canvas.create_rectangle(
            S.CARD_AREA_X + 10, S.CARD_AREA_Y + 10, S.CARD_AREA_X + 110, S.CARD_AREA_Y + 90,
            fill="#fffdf5", outline="#999"
        )
        self.card_text = self.canvas.create_text(
            S.CARD_AREA_X + 60, S.CARD_AREA_Y + 50,
            text="—", font=("Helvetica", 20, "bold")
        )
        self.deck_text = self.canvas.create_text(
            S.CARD_AREA_X + 140, S.CARD_AREA_Y + 50,
            text=f"Deck: {len(self.deck)}",
            anchor="w",
            font=("Helvetica", 12)
        )

    # ---- Mouse handling ----
    def on_mouse_down(self, event):
        for cube in reversed(self.cubes):  # last created is topmost
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

        cell = self.pixel_to_cell(event.x, event.y)
        if cell and self.can_place(cell):
            row, col = cell
            self.place_cube_and_handle_events(cube, row, col)
        else:
            cube.return_to_start()

        self.update_reset_visibility()
        self.active_cube = None

    # ---- Placement & game logic ----
    def place_cube_and_handle_events(self, cube, row, col):
        """Snap cube to (row,col), mark occupied, and trigger placement events."""
        cube.center_on_cell(row, col)
        self.occupied[(row, col)] = cube.idx
        self.on_cube_placed(cube)

    def on_cube_placed(self, cube):
        """Called whenever a cube finishes placement on a cell."""
        row, col = cube.current_cell
        # Draw a card if placed in second column (0-based index 1)
        if col == 1:
            self.draw_card()

    # ---- Helpers ----
    def pixel_to_cell(self, x, y):
        if not (S.GRID_ORIGIN_X <= x < S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE and
                S.GRID_ORIGIN_Y <= y < S.GRID_ORIGIN_Y + S.GRID_ROWS * S.CELL_SIZE):
            return None
        col = int((x - S.GRID_ORIGIN_X) // S.CELL_SIZE)
        row = int((y - S.GRID_ORIGIN_Y) // S.CELL_SIZE)
        if 0 <= row < S.GRID_ROWS and 0 <= col < S.GRID_COLS:
            return (row, col)
        return None

    def can_place(self, cell):
        return cell not in self.occupied

    def draw_card(self):
        if self.deck:
            self.last_card = self.deck.pop()
            self.canvas.itemconfigure(self.card_text, text=str(self.last_card))
            self.canvas.itemconfigure(self.deck_text, text=f"Deck: {len(self.deck)}")
        else:
            self.last_card = None
            self.canvas.itemconfigure(self.card_text, text="No cards")
            self.canvas.itemconfigure(self.deck_text, text="Deck: 0")

    def update_reset_visibility(self):
        placed = sum(1 for c in self.cubes if c.current_cell is not None)
        self.canvas.itemconfigure(
            self.reset_button_window,
            state=("normal" if placed == 4 else "hidden")
        )

    def reset_game(self):
        for cube in self.cubes:
            cube.return_to_start()
        self.occupied.clear()

        self.deck = list(range(1, 51))
        random.shuffle(self.deck)
        self.last_card = None
        self.canvas.itemconfigure(self.card_text, text="—")
        self.canvas.itemconfigure(self.deck_text, text=f"Deck: {len(self.deck)}")

        self.canvas.itemconfigure(self.reset_button_window, state="hidden")
