# mixins/logic_core.py
import settings as S

class LogicCoreMixin:
    # Mouse + placement
    def on_mouse_down(self, event):
        for cube in reversed(self.cubes):
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
            r, c = cell
            self.place_cube_and_handle_events(cube, r, c)
        else:
            cube.return_to_start()
        self.update_reset_visibility()
        self.active_cube = None

    def place_cube_and_handle_events(self, cube, row, col):
        cube.center_on_cell(row, col)
        self.occupied[(row, col)] = cube.idx

    def cell_from_cube_center(self, cube):
        x0, y0, x1, y1 = self.canvas.bbox(cube.rect)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        inside = (S.GRID_ORIGIN_X <= cx < S.GRID_ORIGIN_X + S.GRID_COLS * S.CELL_SIZE
                  and S.GRID_ORIGIN_Y <= cy < S.GRID_ORIGIN_Y + S.GRID_ROWS * S.CELL_SIZE)
        if not inside: return None
        col = int((cx - S.GRID_ORIGIN_X) // S.CELL_SIZE)
        row = int((cy - S.GRID_ORIGIN_Y) // S.CELL_SIZE)
        return (row, col) if (0 <= row < S.GRID_ROWS and 0 <= col < S.GRID_COLS) else None

    def can_place(self, cell):
        return cell not in self.occupied

    def cubes_on_final_column(self):
        results = []
        for cube in self.cubes:
            if cube.current_cell:
                row, col = cube.current_cell
                if col == S.GRID_COLS - 1 and row in (0, 1, 2):
                    results.append((row, col))
        return results

    # Buttons / gating
    def update_reset_visibility(self):
        placed = sum(1 for c in self.cubes if c.current_cell is not None)
        if placed == 4:
            self.canvas.itemconfigure(self.take_action_button_window, state="normal")

            pending_cost = self._pending_total_cost()
            funds_ok = (pending_cost <= self.funds.value)

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
        pending = self._pending_total_cost()
        if pending > self.funds.value:
            self._toast("Insufficient Funds"); return

        need_presence = any(
            c.current_cell in S.PRESENCE_REQUIRED_COORDS
            for c in self.cubes if c.current_cell
        )
        if need_presence and not self.regions.any_presence():
            self._toast("Requires presence in a region"); return

        self.selection_tasks = []

        for _ in [c for c in self.cubes if c.current_cell == (1, 1)]:
            self.selection_tasks.append({"type": "add_presence", "requires_presence": False})
        for _ in [c for c in self.cubes if c.current_cell == (1, 0)]:
            self.selection_tasks.append({"type": "rep+1", "requires_presence": True})
        for _ in [c for c in self.cubes if c.current_cell == (1, 2)]:
            self.selection_tasks.append({"type": "power+1", "requires_presence": True})
        for _ in [c for c in self.cubes if c.current_cell == (2, 1)]:
            self.selection_tasks.append({"type": "power+1_rep-2_chaos+10", "requires_presence": True})
        for _ in [c for c in self.cubes if c.current_cell == (2, 2)]:
            self.selection_tasks.append({"type": "rep-1_chaos+10", "requires_presence": True})

        if self.selection_tasks:
            self.selecting_regions = True
            self._show_center_popup(self._current_selection_prompt())
            return

        self._finish_take_actions_after_selection()

    def _finish_take_actions_after_selection(self):
        for _ in self.cubes_on_final_column():
            self.draw_card()

        if any(c.current_cell == (0, 1) for c in self.cubes if c.current_cell):
            for r in self.regions.with_presence():
                r.adjust_rep(+1); r.adjust_power(+1)

        bumps_compute = bumps_model = 0
        charges = {"lobby": 0, "scale_presence": 0, "compute_or_model": 0}

        for cube in self.cubes:
            if not cube.current_cell: continue
            r, c = cube.current_cell
            if (r, c) == (0, 0):
                bumps_compute += 1; charges["compute_or_model"] += 1
            elif (r, c) == (0, 1):
                bumps_model += 1; charges["compute_or_model"] += 1
            if (r, c) in ((2, 1), (2, 2)):
                pass
            if (r, c) == (0, 2):
                charges["lobby"] += 1
            if (r, c) == (1, 1):
                charges["scale_presence"] += 1

        if bumps_compute: self.inc_compute(bumps_compute)
        if bumps_model: self.inc_model(bumps_model)

        for key, n in charges.items():
            if n: self.funds.charge(key, n)

        income = self.regions.total_reputation() * self.regions.total_power()
        if income: self.funds.add(income)

        for cube in self.cubes: cube.return_to_start()
        self.occupied.clear()
        self.canvas.itemconfigure(self.take_action_button_window, state="hidden")

    # Cost helpers / toast
    def _charges_for_current_turn(self):
        charges = {"lobby": 0, "scale_presence": 0, "compute_or_model": 0}
        for cube in self.cubes:
            if not cube.current_cell: continue
            r, c = cube.current_cell
            if (r, c) in ((0, 0), (0, 1)): charges["compute_or_model"] += 1
            if (r, c) == (0, 2): charges["lobby"] += 1
            if (r, c) == (1, 1): charges["scale_presence"] += 1
        return charges

    def _pending_total_cost(self):
        charges = self._charges_for_current_turn()
        return (self.funds.peek_cost("compute_or_model", charges["compute_or_model"])
                + self.funds.peek_cost("lobby", charges["lobby"])
                + self.funds.peek_cost("scale_presence", charges["scale_presence"]))

    def _toast(self, msg: str, millis: int = 1500):
        if hasattr(self, "toast_id") and self.toast_id:
            self.canvas.delete(self.toast_id); self.toast_id = None
        x = S.CARD_AREA_X + S.CARD_AREA_W / 2
        y = S.CARD_AREA_Y - 8
        self.toast_id = self.canvas.create_text(
            x, y, text=msg, fill="#b00020", font=("Helvetica", 12, "bold"), anchor="s"
        )
        self.canvas.after(millis, lambda: (self.canvas.delete(self.toast_id), setattr(self, "toast_id", None)))
