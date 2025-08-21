# mixins/ui_grid.py
import tkinter.font as tkfont
import textwrap
import tkinter as tk
import settings as S

try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None


class UIGridMixin:
    def draw_grid(self):
        self.canvas.create_text(
            S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE / 2,
            20,
            text="Quarterly Strategy",
            font=("Helvetica", 16, "bold"),
            fill="black",
        )
        for r in range(S.GRID_ROWS):
            for c in range(S.GRID_COLS):
                x0 = S.GRID_ORIGIN_X + c * S.CELL_SIZE
                y0 = S.GRID_ORIGIN_Y + r * S.CELL_SIZE
                x1, y1 = x0 + S.CELL_SIZE, y0 + S.CELL_SIZE
                fill = "#ffffff" if c % 2 == r % 2 else "#f5f6fa"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#ccccd6")
                idx = r * S.GRID_COLS + c
                if idx < len(self.BOARD_LABELS):
                    self.draw_cell_label(r, c, self.BOARD_LABELS[idx])

    def draw_cell_label(self, row, col, text):
        CELL_TEXT_PAD = 10
        x0 = S.GRID_ORIGIN_X + col * S.CELL_SIZE
        y0 = S.GRID_ORIGIN_Y + row * S.CELL_SIZE
        x1, y1 = x0 + S.CELL_SIZE, y0 + S.CELL_SIZE

        max_w = S.CELL_SIZE - 2 * CELL_TEXT_PAD
        max_h = S.CELL_SIZE - 2 * CELL_TEXT_PAD

        size, wrapped = 18, text
        for fs in range(18, 9, -1):
            font = tkfont.Font(family="Helvetica", size=fs, weight="bold")
            avg_char_px = max(font.measure("M"), 1)
            chars_per_line = max(int(max_w / (avg_char_px * 0.7)), 8)
            lines = []
            for p in text.split("\n"):
                lines.extend(textwrap.wrap(p, width=chars_per_line) or [""])
            line_h = font.metrics("linespace")
            total_h = line_h * len(lines)
            widest = max((font.measure(line) for line in lines), default=0)
            if widest <= max_w and total_h <= max_h:
                wrapped = "\n".join(lines)
                size = fs
                break

        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        t_id = self.canvas.create_text(
            cx, cy, text=wrapped, font=("Helvetica", size, "bold"),
            fill="#111", justify="center",
        )
        self.cell_text_ids[(row, col)] = t_id

    def draw_start_area(self):
        start_x, start_y, start_w, start_h = self._start_area_geom
        self.start_area_rect_id = self.canvas.create_rectangle(
            start_x, start_y, start_x + start_w, start_y + start_h,
            outline="#bbbbc6", dash=(4, 2), fill=""
        )

    def _draw_side_image(self):
        if Image is None or ImageTk is None:
            return
        try:
            img = Image.open(S.SIDE_IMAGE_PATH)
        except Exception:
            return

        grid_h = S.GRID_ROWS * S.CELL_SIZE
        grid_w = S.GRID_COLS * S.CELL_SIZE

        ow, oh = img.size
        if oh == 0:
            return
        scale = grid_h / float(oh)
        new_w, new_h = max(1, int(round(ow * scale))), grid_h
        img = img.resize((new_w, new_h), Image.LANCZOS)

        x = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        y = S.GRID_ORIGIN_Y

        try:
            self._side_img_tk = ImageTk.PhotoImage(img, master=self.canvas)
            self.side_image_id = self.canvas.create_image(x, y, image=self._side_img_tk, anchor="nw")
            self.side_image_dims = (new_w, new_h)
        except tk.TclError:
            self._side_img_tk = None
            self.side_image_id = None
            self.side_image_dims = (0, 0)

    def _draw_ops_tracks(self):
        # Titles
        self.canvas.create_text(
            S.OPS_ASP_X + S.OPS_TRACK_W/2, S.OPS_TRACK_TOP - 14,
            text="Aspirational Action Tokens", font=("Helvetica", 12, "bold"),
            fill="black", anchor="s"
        )
        self.canvas.create_text(
            S.OPS_AVAIL_X + S.OPS_TRACK_W/2, S.OPS_TRACK_TOP - 14,
            text="Available Action Tokens", font=("Helvetica", 12, "bold"),
            fill="black", anchor="s"
        )
        # Columns
        self.ops_asp_rect = self.canvas.create_rectangle(
            S.OPS_ASP_X, S.OPS_TRACK_TOP,
            S.OPS_ASP_X + S.OPS_TRACK_W, S.OPS_TRACK_TOP + S.OPS_TRACK_H,
            outline="#bbbbc6", fill="#e7f2ff"
        )
        self.ops_avail_rect = self.canvas.create_rectangle(
            S.OPS_AVAIL_X, S.OPS_TRACK_TOP,
            S.OPS_AVAIL_X + S.OPS_TRACK_W, S.OPS_TRACK_TOP + S.OPS_TRACK_H,
            outline="#bbbbc6", fill="#e7f2ff"
        )

    def _ops_slot_starts(self, left_x):
        y = S.OPS_TRACK_TOP + S.OPS_TRACK_PAD + S.OPS_DISC_R
        out = []
        for _ in range(S.OPS_MAX_TOKENS):
            cx = left_x + S.OPS_TRACK_W/2
            cy = y
            out.append((cx - S.OPS_DISC_R, cy - S.OPS_DISC_R))
            y += 2 * S.OPS_DISC_R + S.OPS_DISC_GAP
        return out

    def _reset_tokens_to_tracks(self):
        asp_slots = self._ops_slot_starts(S.OPS_ASP_X)
        ava_slots = self._ops_slot_starts(S.OPS_AVAIL_X)

        avail = [c for c in self.cubes if not c.locked]
        locked = [c for c in self.cubes if c.locked]

        for i, c in enumerate(sorted(avail, key=lambda x: x.idx)):
            x, y = ava_slots[i]
            c.set_start(x, y)
        for i, c in enumerate(sorted(locked, key=lambda x: x.idx)):
            x, y = asp_slots[i]
            c.set_start(x, y)