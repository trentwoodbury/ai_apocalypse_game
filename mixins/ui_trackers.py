# mixins/ui_trackers.py
import settings as S

class UITrackersMixin:
    def _draw_trackers(self):
        grid_w = S.GRID_COLS * S.CELL_SIZE
        img_x = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        left_x = img_x

        self._draw_costs_panel()
        cb = self.canvas.bbox(self.costs_panel_tag)
        costs_bottom_y = cb[3] if cb else (S.GRID_ORIGIN_Y + 200)

        top_y = costs_bottom_y + 20
        row_h = S.TRACKER_ROW_H
        self.trackers_left_x = left_x

        self._draw_tracker_row(
            y=top_y + 0 * row_h, title="Compute",
            steps=S.COMPUTE_STEPS, key="compute", active_idx=self.compute_idx
        )
        self._draw_tracker_row(
            y=top_y + 1 * row_h, title="Model Version",
            steps=S.MODEL_STEPS, key="model", active_idx=self.model_idx
        )

        self._draw_region_panels(start_y=top_y + 2 * row_h)
        self.trackers_bottom_y = getattr(self, "panels_bottom_y", top_y + 1)

        needed_w = int(self.trackers_rightmost_x + S.GRID_PADDING)
        current_w = int(float(self.canvas.cget("width")))
        if needed_w > current_w:
            self.canvas.config(width=needed_w)

    def _draw_tracker_row(self, y, title, steps, key, active_idx=0):
        left_x = self.trackers_left_x if hasattr(self, "trackers_left_x") else S.GRID_ORIGIN_X
        pad_label = 110
        w_box = 120 if key not in ("chaos",) else 60
        gap = 8

        self.canvas.create_text(left_x, y, text=title + ":", anchor="w",
                                font=("Helvetica", 12, "bold"), fill="black")

        x = left_x + pad_label
        rows_list = []
        for i, label in enumerate(steps):
            rect = self.canvas.create_rectangle(x, y - 14, x + w_box, y + 14, outline="#222", fill="#eee")
            txt = self.canvas.create_text((x + x + w_box) / 2, y, text=label,
                                          font=("Helvetica", 11, "bold"), fill="#111")
            cx = (x + x + w_box) / 2
            circle = self.canvas.create_oval(cx - 10, y - 10, cx + 10, y + 10, outline="", width=3)
            rows_list.append((rect, txt, circle, (x, y, w_box)))
            self.trackers_rightmost_x = max(getattr(self, "trackers_rightmost_x", 0), x + w_box)
            x += w_box + gap

        if not hasattr(self, "tracker_items"):
            self.tracker_items = {}
        self.tracker_items[key] = rows_list
        self._set_tracker_active_index(key, active_idx)
        return rows_list

    def _set_tracker_active_index(self, key, idx):
        rows_list = self.tracker_items.get(key, [])
        for i, (_rect, _txt, circle, (x, y, w)) in enumerate(rows_list):
            if i == idx:
                cx = (x + x + w) / 2
                self.canvas.coords(circle, cx - 12, y - 12, cx + 12, y + 12)
                self.canvas.itemconfigure(circle, outline="black")
            else:
                self.canvas.itemconfigure(circle, outline="")

    def _render_tracker_markers(self):
        def paint(key, idx):
            items = self.tracker_items[key]
            for i, (_rect, _txt, circle, (x, y, w)) in enumerate(items):
                if i == idx:
                    cx, cy = (x + x + w) / 2, y
                    self.canvas.coords(circle, cx - 12, cy - 12, cx + 12, cy + 12)
                    self.canvas.itemconfigure(circle, outline="black")
                else:
                    self.canvas.itemconfigure(circle, outline="")
        paint("compute", self.compute_idx)
        paint("model", self.model_idx)

    def inc_compute(self, n=1):
        self.compute_idx = min(self.compute_idx + n, len(S.COMPUTE_STEPS) - 1)
        if self.model_idx > self.compute_idx:
            self.model_idx = self.compute_idx
        self._render_tracker_markers()
        self._set_tracker_active_index("compute", self.compute_idx)

    def inc_model(self, n=1):
        target = min(self.model_idx + n, self.compute_idx, len(S.MODEL_STEPS) - 1)
        if target != self.model_idx:
            self.model_idx = target
            self._render_tracker_markers()
        self._set_tracker_active_index("model", self.model_idx)
        self._render_costs_panel()

    # legacy hook kept (no global chaos now; harmless)
    def inc_chaos(self, n=1):
        pass

    def _update_region_chaos(self, name):
        # kept for compatibility with tests; now handled by panels
        pass
