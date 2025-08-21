# mixins/ui_regions.py
import math
import settings as S

class UIRegionsMixin:
    def _draw_region_panels(self, start_y=None):
        grid_w = S.GRID_COLS * S.CELL_SIZE
        grid_h = S.GRID_ROWS * S.CELL_SIZE
        base_x = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        y0 = start_y if start_y is not None else (S.GRID_ORIGIN_Y + grid_h + 10)

        self.canvas.create_text(
            base_x, y0, text=S.REGION_PANELS_TITLE, anchor="w",
            font=("Helvetica", 13, "bold"), fill="black"
        )
        y0 += 24

        self.region_panel_items = {}
        col_w, row_h = S.REGION_PANEL_W, S.REGION_PANEL_H

        for idx, name in enumerate(S.REGION_NAMES):
            r, c = divmod(idx, S.REGION_PANEL_COLS)
            x = base_x + c * (col_w + S.REGION_PANEL_GAP_X)
            y = y0 + r * (row_h + S.REGION_PANEL_GAP_Y)

            rect = self.canvas.create_rectangle(
                x, y, x + col_w, y + row_h,
                outline="#bbb", fill="#f2f2f6"
            )
            text_id = self.canvas.create_text(
                x + 10, y + 10, anchor="nw",
                font=("Helvetica", 11), fill="black", text=""
            )
            self.region_panel_items[name] = {"rect": rect, "text": text_id}

        self.panels_bottom_y = y0 + (S.REGION_PANEL_ROWS) * (row_h + S.REGION_PANEL_GAP_Y) - S.REGION_PANEL_GAP_Y

        for name in S.REGION_NAMES:
            self._render_region_panel(name)

        rightmost = base_x + S.REGION_PANEL_COLS * (col_w + S.REGION_PANEL_GAP_X) - S.REGION_PANEL_GAP_X
        self.trackers_rightmost_x = max(getattr(self, "trackers_rightmost_x", 0), rightmost)

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

    # --- globe hitboxes & markers ---
    def _build_region_hitboxes(self):
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
            ang = math.radians(60 * i - 30)
            pts.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])
        return pts

    def _render_region_markers(self):
        for poly_id in list(self.region_hex_ids.values()):
            try:
                self.canvas.delete(poly_id)
            except Exception:
                pass
        self.region_hex_ids.clear()

        for name, (x0, y0, x1, y1) in self.region_hitboxes.items():
            if not self.regions.has_presence(name):
                continue
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            pts = self._hex_points(cx, cy, S.REGION_HEX_RADIUS)
            pid = self.canvas.create_polygon(
                *pts, fill="", outline=S.REGION_HEX_OUTLINE, width=S.REGION_HEX_WIDTH
            )
            self.region_hex_ids[name] = pid

    # --- selection popup ---
    def _show_center_popup(self, msg: str):
        self._hide_center_popup()
        cw = int(float(self.canvas.cget("width")))
        ch = int(float(self.canvas.cget("height")))
        cx, cy = cw // 2, ch // 2
        pad_x, pad_y = 16, 12
        txt_id = self.canvas.create_text(
            cx, cy, text=msg, font=("Helvetica", 14, "bold"),
            fill="black", anchor="c", justify="center",
            width=min(420, cw - 60),
        )
        tx0, ty0, tx1, ty1 = self.canvas.bbox(txt_id)
        rx0, ry0 = tx0 - pad_x, ty0 - pad_y
        rx1, ry1 = tx1 + pad_x, ty1 + pad_y
        rect_id = self.canvas.create_rectangle(rx0, ry0, rx1, ry1, fill="#e9e9ee", outline="#555", width=2)
        self.canvas.tag_raise(txt_id, rect_id)
        self._popup_rect_id = rect_id
        self._popup_text_id = txt_id

    def _update_center_popup(self, msg: str):
        if getattr(self, "_popup_text_id", None):
            self.canvas.itemconfigure(self._popup_text_id, text=msg)
            tx0, ty0, tx1, ty1 = self.canvas.bbox(self._popup_text_id)
            pad_x, pad_y = 16, 12
            rx0, ry0 = tx0 - pad_x, ty0 - pad_y
            rx1, ry1 = tx1 + pad_x, ty1 + pad_y
            if getattr(self, "_popup_rect_id", None):
                self.canvas.coords(self._popup_rect_id, rx0, ry0, rx1, ry1)

    def _hide_center_popup(self):
        if getattr(self, "_popup_text_id", None):
            try: self.canvas.delete(self._popup_text_id)
            except Exception: pass
            self._popup_text_id = None
        if getattr(self, "_popup_rect_id", None):
            try: self.canvas.delete(self._popup_rect_id)
            except Exception: pass
            self._popup_rect_id = None

    def _current_selection_prompt(self):
        if not getattr(self, "selection_tasks", None):
            return ""
        t = self.selection_tasks[0]
        if t["type"] == "add_presence":
            return f"Select a region to ADD presence ({len(self.selection_tasks)} remaining)"
        if t.get("requires_presence"):
            return f"Select a region WHERE YOU HAVE PRESENCE ({len(self.selection_tasks)} remaining)"
        return f"Select a region ({len(self.selection_tasks)} remaining)"

    def _maybe_region_click(self, event):
        if not getattr(self, "selecting_regions", False):
            return
        if not self.selection_tasks:
            self._hide_center_popup()
            self.selecting_regions = False
            self._finish_take_actions_after_selection()
            return

        hit_name = None
        for name, (x0, y0, x1, y1) in self.region_hitboxes.items():
            if x0 <= event.x <= x1 and y0 <= event.y <= y1:
                hit_name = name
                break
        if not hit_name:
            self._update_center_popup(self._current_selection_prompt()); return

        task = self.selection_tasks[0]
        if task.get("requires_presence") and not self.regions.has_presence(hit_name):
            self._update_center_popup("Select a region WHERE YOU HAVE PRESENCE"); return

        if task["type"] == "add_presence":
            if not self.regions.has_presence(hit_name):
                self.regions.add_presence(hit_name)
                self._render_region_markers()
            self._update_region_panel(hit_name)
            self._render_costs_panel()
        elif task["type"] == "rep+1":
            R = self.regions[hit_name]; R.adjust_rep(+1); self._update_region_panel(hit_name)
        elif task["type"] == "power+1":
            R = self.regions[hit_name]; R.adjust_power(+1); self._update_region_panel(hit_name)
        elif task["type"] == "power+1_rep-2_chaos+10":
            R = self.regions[hit_name]; R.adjust_power(+1); R.adjust_rep(-2); R.set_chaos(R.chaos + S.CHAOS_STEP); self._update_region_panel(hit_name)
        elif task["type"] == "rep-1_chaos+10":
            R = self.regions[hit_name]; R.adjust_rep(-1); R.set_chaos(R.chaos + S.CHAOS_STEP); self._update_region_panel(hit_name)

        self.selection_tasks.pop(0)
        if self.selection_tasks:
            self._update_center_popup(self._current_selection_prompt())
        else:
            self._hide_center_popup(); self.selecting_regions = False; self._finish_take_actions_after_selection()
