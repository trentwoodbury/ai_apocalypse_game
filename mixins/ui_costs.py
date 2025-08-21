# mixins/ui_costs.py
import settings as S

class UICostsMixin:
    def _draw_costs_panel(self):
        grid_w = S.GRID_COLS * S.CELL_SIZE
        x_img = S.GRID_ORIGIN_X + grid_w + S.GRID_PADDING
        img_w = getattr(self, "side_image_dims", (0, 0))[0]

        x = x_img + img_w + S.GRID_PADDING
        y = S.GRID_ORIGIN_Y
        w = S.COSTS_PANEL_W

        needed_w = x + w + S.GRID_PADDING
        current_w = int(float(self.canvas.cget("width")))
        if needed_w > current_w:
            self.canvas.config(width=needed_w)

        self.costs_panel_tag = "costs_panel"

        self.costs_title_id = self.canvas.create_text(
            x, y, anchor="nw", fill="black",
            font=("Helvetica", 13, "bold"),
            text="Scaling Costs and Requirements",
            tags=(self.costs_panel_tag,)
        )
        y += 22

        self.costs_rect_id = self.canvas.create_rectangle(
            x, y, x + w, y + 100, outline="#bbb", fill="#f7f7fb",
            tags=(self.costs_panel_tag,)
        )

        self.costs_line_ids = []
        self._render_costs_panel()

    def _render_costs_panel(self):
        if not hasattr(self, "costs_rect_id"):
            return

        for tid, *_ in getattr(self, "costs_line_ids", []):
            try:
                self.canvas.delete(tid)
            except Exception:
                pass
        self.costs_line_ids = []

        x1, y1, x2, _ = self.canvas.coords(self.costs_rect_id)
        x = x1 + S.COSTS_PANEL_PAD
        y = y1 + S.COSTS_PANEL_PAD
        line_gap = 4

        def add_line(text, bold=False, pad_top=0):
            nonlocal y
            y += pad_top
            tid = self.canvas.create_text(
                x, y, anchor="nw", fill="black",
                font=("Helvetica", 11, "bold" if bold else "normal"),
                text=text,
                tags=(self.costs_panel_tag,)
            )
            self.costs_line_ids.append((tid, bold, text))
            y += 18 + line_gap

        next_model_idx = self.model_idx + 1 if self.model_idx < len(S.MODEL_STEPS) - 1 else None
        presence_count = len(self.regions.with_presence())
        next_presence_idx = presence_count if presence_count < len(S.SCALING_PRESENCE_COSTS) else None

        add_line("Model Version Scaling Requirements", bold=True, pad_top=0)
        for tgt in range(len(S.MODEL_STEPS)):
            cost = S.MODEL_UPGRADE_COSTS[tgt]
            compute_req = S.COMPUTE_STEPS[tgt] if tgt < len(S.COMPUTE_STEPS) else ""
            label = f"V{tgt}: Pay ${cost}, {compute_req}"
            bold = (next_model_idx == tgt)
            add_line(label, bold=bold)

        add_line("", pad_top=6)
        add_line("Scaling Operation Costs", bold=True)
        for actions in (2, 3, 4):
            add_line(f"{actions} Actions: ${S.SCALING_OPERATION_COSTS[actions]}")

        add_line("", pad_top=6)
        add_line("Scaling Presence Costs", bold=True)
        for idx, cost in enumerate(S.SCALING_PRESENCE_COSTS, start=1):
            if idx == 1: label = f"{idx}st Region: ${cost}"
            elif idx == 2: label = f"{idx}nd Region: ${cost}"
            elif idx == 3: label = f"{idx}rd Region: ${cost}"
            else: label = f"{idx}th Region: ${cost}"
            bold = (next_presence_idx is not None and (idx == next_presence_idx + 1))
            add_line(label, bold=bold)

        bx1, by1, bx2, by2 = self.canvas.bbox(self.costs_panel_tag)
        new_bottom = max(by2 + S.COSTS_PANEL_PAD, y1 + 40)
        self.canvas.coords(self.costs_rect_id, x1, y1, x2, new_bottom)
