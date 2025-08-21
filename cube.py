import settings as S

class Cube:
    def __init__(self, canvas, idx, x, y, color, size=60, locked=False):
        self.canvas = canvas
        self.idx = idx
        self.size = size
        self.locked = locked
        self.current_cell = None
        self.dragging = False

        self.rect = canvas.create_rectangle(x, y, x + size, y + size, fill=color, outline="#222", width=3)
        self.text = canvas.create_text(x + size/2, y + size/2, text=f"C{idx+1}", fill="white", font=("Helvetica", 14, "bold"))
        self.start_x, self.start_y = x, y

    def contains(self, px, py):
        x0, y0, x1, y1 = self.canvas.coords(self.rect)
        return x0 <= px <= x1 and y0 <= py <= y1

    def begin_drag(self, x, y):
        if self.locked:
            return
        self.dragging = True
        self.drag_offset_x = x - self.start_x
        self.drag_offset_y = y - self.start_y

    def drag_to(self, x, y):
        if not self.dragging:
            return
        nx = x - self.drag_offset_x
        ny = y - self.drag_offset_y
        self.canvas.coords(self.rect, nx, ny, nx + self.size, ny + self.size)
        self.canvas.coords(self.text, nx + self.size/2, ny + self.size/2)

    def end_drag(self):
        self.dragging = False

    def return_to_start(self):
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.start_x + self.size, self.start_y + self.size)
        self.canvas.coords(self.text, self.start_x + self.size/2, self.start_y + self.size/2)
        self.current_cell = None

    def center_on_cell(self, row, col, grid_origin_x=None, grid_origin_y=None, cell_size=None):
        """Snap the cube to the center of (row, col).
        Backwards-compatible: if grid geometry is not passed, use settings.
        """
        gx = S.GRID_ORIGIN_X if grid_origin_x is None else grid_origin_x
        gy = S.GRID_ORIGIN_Y if grid_origin_y is None else grid_origin_y
        cs = S.CELL_SIZE if cell_size is None else cell_size

        x0 = gx + col * cs
        y0 = gy + row * cs
        cx = x0 + cs / 2
        cy = y0 + cs / 2

        # move the rect so its center is (cx, cy)
        rx0, ry0, rx1, ry1 = self.canvas.coords(self.rect)
        cur_cx = (rx0 + rx1) / 2
        cur_cy = (ry0 + ry1) / 2
        dx = cx - cur_cx
        dy = cy - cur_cy
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.text, dx, dy)

        self.current_cell = (row, col)

    def set_start(self, x, y):
        self.start_x, self.start_y = x, y
        self.return_to_start()
