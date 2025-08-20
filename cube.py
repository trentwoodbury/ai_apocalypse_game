import settings as S

class Cube:
    def __init__(self, canvas, idx, x, y, color):
        self.canvas = canvas
        self.idx = idx
        self.start_pos = (x, y)
        self.rect = canvas.create_rectangle(
            x, y, x + S.CUBE_SIZE, y + S.CUBE_SIZE, fill=color, outline="black", width=2
        )
        self.label = canvas.create_text(
            x + S.CUBE_SIZE/2, y + S.CUBE_SIZE/2, text=f"C{idx+1}", font=("Helvetica", 14, "bold")
        )
        self.dragging = False
        self.offset = (0, 0)
        self.current_cell = None  # (row, col) or None

    def items(self):
        return (self.rect, self.label)

    def contains(self, x, y):
        x0, y0, x1, y1 = self.canvas.bbox(self.rect)
        return x0 <= x <= x1 and y0 <= y <= y1

    def begin_drag(self, x, y):
        x0, y0, _, _ = self.canvas.bbox(self.rect)
        self.offset = (x - x0, y - y0)
        self.dragging = True

    def drag_to(self, x, y):
        if not self.dragging:
            return
        x0, y0, _, _ = self.canvas.bbox(self.rect)
        dx = (x - self.offset[0]) - x0
        dy = (y - self.offset[1]) - y0
        for item in self.items():
            self.canvas.move(item, dx, dy)

    def end_drag(self):
        self.dragging = False

    def move_to_pixel(self, px, py):
        x0, y0, _, _ = self.canvas.bbox(self.rect)
        dx = px - x0
        dy = py - y0
        for item in self.items():
            self.canvas.move(item, dx, dy)

    def center_on_cell(self, row, col):
        cell_x = S.GRID_ORIGIN_X + col * S.CELL_SIZE
        cell_y = S.GRID_ORIGIN_Y + row * S.CELL_SIZE
        target_x = cell_x + (S.CELL_SIZE - S.CUBE_SIZE) / 2
        target_y = cell_y + (S.CELL_SIZE - S.CUBE_SIZE) / 2
        self.move_to_pixel(target_x, target_y)
        self.current_cell = (row, col)

    def return_to_start(self):
        self.move_to_pixel(*self.start_pos)
        self.current_cell = None
